from asyncio import CancelledError
from cmd import Cmd
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import asdict
from itertools import repeat
from json import dumps, loads
from operator import contains
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union
import logging
import shlex
import subprocess

from mash import io_util
from mash.filesystem.filesystem import FileSystem, cd
from mash.io_util import log, shell_ready_signal, print_shell_ready_signal, check_output
from mash.shell import delimiters
from mash.shell.if_statement import LINE_INDENT, Abort, Done, close_prev_if_statements, handle_else_statement, handle_if_statement, handle_then_else_statements, handle_prev_then_else_statements, handle_then_statement
from mash.shell.delimiters import ELSE, comparators, DEFINE_FUNCTION, FALSE, IF, LEFT_ASSIGNMENT, RETURN, RIGHT_ASSIGNMENT, THEN, TRUE
from mash.filesystem.scope import Scope, show
from mash.shell.errors import ShellError, ShellPipeError
from mash.shell.function import InlineFunction
from mash.shell.lex_parser import Term, parse
from mash.shell.parsing import expand_variables, expand_variables_inline, filter_comments, indent_width, infer_infix_args, inline_indent_with, parse_commands, quote_items
from mash.util import for_any, has_method, identity, is_valid_method_name, omit_prefixes, quote_all, removeprefix, split_prefixes, translate_terms


confirmation_mode = False
default_session_filename = '.shell_session.json'

COMMENT = '#'
LAST_RESULTS = '_last_results'
LAST_RESULTS_INDEX = '_last_results_index'
INNER_SCOPE = 'inner_scope'
RAW_LINE_INDENT = 'raw_line_indent'
ENV = 'env'

Command = Callable[[Cmd, str], str]
Types = Union[str, bool, int, float]


class BaseShell(Cmd):
    """Extend CMD with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrride.

    Features:
    - Parsing of multi-line and multi-segment commands.
        - Chain commands using pipes.
        - Interop between Python and e.g. Bash using pipes.
    - Parsing of single commands.
        - Set/unset variables, retrieve variable values.
    - Confirmation mode to allow a user to accept or decline commands.
    - Error handling.
    """

    intro = 'Welcome.  Type help or ? to list commands.\n' + shell_ready_signal + '\n'
    prompt = '$ '

    # TODO save stdout in a tmp file

    def __init__(self, *args, env: Dict[str, Any] = None,
                 save_session_prehook=identity,
                 load_session_posthook=identity, **kwds):
        """
        Parameters
        ----------
            env : dict
                Must be JSON serializable
        """
        super().__init__(*args, **kwds)
        self.save_session_prehook = save_session_prehook
        self.load_session_posthook = load_session_posthook

        # fill this list to customize autocomplete behaviour
        self.completenames_options: List[Command] = []

        # defaults
        self.ignore_invalid_syntax = True

        self.locals = FileSystem(scope())
        self.init_current_scope()

        self.env = Scope(self.locals, ENV)
        self.env[LAST_RESULTS] = []
        self.env[LAST_RESULTS_INDEX] = 0

        if env:
            for k, v in env.items():
                self.env[k] = v

        self.auto_save = False
        self.auto_reload = False

        # internals
        self._do_char_method = self.none
        self._chars_allowed_for_char_method: List[str] = []

        self.set_infix_operators()
        if self.auto_reload:
            self.try_load_session()

    def init_current_scope(self):
        self.locals.set(IF, [])
        self.locals.set(ENV, {})

    @property
    def delimiters(self):
        """Return the most recent values of the delimiters.
        """
        items = delimiters.python + delimiters.bash
        items.remove('=')
        items.remove('#')
        return items

    @property
    def _last_if(self):
        return self.locals[IF][-1]

    @property
    def _last_results(self):
        return self.env[LAST_RESULTS]

    @property
    def _last_results_index(self):
        return self.env[LAST_RESULTS_INDEX]

    def set_infix_operators(self):
        # use this for infix operators, e.g. `a = 1`
        self.infix_operators = {'=': self.handle_set_env_variable}
        # the sign to indicate that a variable should be expanded
        self.variable_prefix = '$'

    def set_do_char_method(self, method: Command, chars: List[str]):
        """Use `method` to interpret commands that start any item in `chars`.
        This allow special chars to be used as commands.
        E.g. transform `do_$` into `do_f $`

        Naming conflicts with existing `delimiters` are resolved.
        """
        for char in chars:
            if char in delimiters.all:
                raise ShellError(f'Char {char} is already in use.')

        self._do_char_method = method
        self._chars_allowed_for_char_method = chars

    def eval(self, args: List[str], quote=True) -> Types:
        """Evaluate / run `args` and return the result.
        """
        if quote:
            args = list(quote_items(args))

        args = list(filter_comments(args))

        if not args:
            return ''

        if not self.is_function(args[0]):
            args = ['echo'] + args

        k = '_eval_output'
        line = ' '.join(args)
        line = f'{line} |> export {k}'

        with enter_new_scope(self):

            self.onecmd(line)

            # verify result
            if k not in self.env and not self._last_results:
                raise ShellError('eval() failed')

            result = self._retrieve_eval_result(k)

            if k in self.env:
                del self.env[k]

        return result

    def _retrieve_eval_result(self, k):
        if k in self.env:
            return str(self.env[k])

        elif self._last_results:
            return self._last_results.pop()

        raise RuntimeError('Cannot retrieve result')

    def eval_compare(self, line: str) -> bool:
        f, *_ = line.split(' ')
        terms = line.split(' ')

        if self.is_function(f):
            result = self.eval(terms)
        elif for_any(comparators, contains, line):
            result = self.eval(['math'] + terms)
        else:
            result = line

        return result != FALSE

    def onecmd_prehook(self, line):
        """Similar to cmd.precmd but executed before cmd.onecmd
        """
        if confirmation_mode:
            assert io_util.interactive
            log('Command:', line)
            if not io_util.confirm():
                raise CancelledError()

        return line

    def none(self, _: str) -> str:
        """Do nothing. Similar to util.none.
        This is a default value for self._do_char_method.
        """
        return ''

    def _save_result(self, value):
        logging.debug(f'_save_result [{self._last_results_index}]: {value}')

        if len(self._last_results) < self._last_results_index:
            raise ShellError('Invalid state')
        if len(self._last_results) == self._last_results_index:
            self._last_results.append(None)

        self._last_results[self._last_results_index] = value

    def is_function(self, func_name: str) -> bool:
        return has_method(self, f'do_{func_name}') \
            or self.is_inline_function(func_name) \
            or func_name in self._chars_allowed_for_char_method

    def is_inline_function(self, func_name: str) -> bool:
        return func_name in self.env and isinstance(self.env[func_name], InlineFunction)

    ############################################################################
    # Commands: do_*
    ############################################################################

    def do_assign(self, args: str):
        """Assign the result of an expression to an environment variable.
        ```sh
        assign a |> print 10
        # results in a = 10
        ```
        """
        keys = args.split(' ')

        for k in keys:
            if not is_valid_method_name(k):
                raise ShellError(f'Invalid variable name format: {k}')

        if LEFT_ASSIGNMENT in self.locals:
            assignee = self.locals[LEFT_ASSIGNMENT]

            # cancel previous assignments
            self.locals.rm(LEFT_ASSIGNMENT)

            raise ShellError(
                f'Assignments cannot be used inside other assignments: {assignee}')

        self.locals.set(LEFT_ASSIGNMENT, keys)

        # return value must be empty to prevent side-effects in the next command
        return ''

    def do_export(self, args: str):
        """Set an environment variable.
        `export(k, *values)`
        """
        if not args:
            return ''

        k, *values = args.split(' ')

        if len(values) == 0:
            values = ['']

        self.set_env_variable(k, *values)

    def do_unset(self, args: str):
        """Unset keys
        `unset [KEY [KEY..]]
        """
        for k in args.split(' '):
            if k in self.env:
                del self.env[k]
            else:
                logging.warning('Invalid key')

        return ''

    def do_shell(self, args):
        """System call
        """
        logging.info(f'Cmd = !{args}')
        return check_output(args)

    def do_fail(self, msg: str):
        raise ShellError(f'Fail: {msg}')

    def do_reduce(self, *args: str):
        """Reduce a sequence of items to using an operator.

        See https://en.wikipedia.org/wiki/Reduction_operator

        E.g. compute the sum:
        `range 10 |> reduce sum 0 $
        """
        return self.do_foldr(*args)

    def do_foldr(self, args: str, delimiter='\n'):
        """Fold or reduce from right to left.

        See https://wiki.haskell.org/Foldr_Foldl_Foldl'
        """
        lines = args.split(delimiter)
        msg = 'Not enough arguments. Usage: `foldl f zero [args] $ [args]`.'
        # if len(lines) <= 1:
        if not lines:
            log(msg)
            return

        items = lines[0].split(' ')
        if len(items) <= 1:
            log(msg)
            return

        f, zero, *args, line = items
        lines = [line] + lines[1:]

        if '$' in args:
            i = args.index('$')
        else:
            i = -1

        # apply the reduction
        acc = zero
        for line in lines:
            local_args = args.copy()
            line = line.split(' ')

            if i == -1:
                local_args += line
            else:
                local_args[i:i+1] = line

            line = [f, acc] + local_args

            acc = self.run_single_command(line)

        return acc

    def do_map(self, args: str, delimiter='\n'):
        """Apply a function to every line.
        If `$` is present, then each line from stdin is inserted there.
        Otherwise each line is appended.

        Usage
        -----
        ```sh
        println a b |> map echo
        println a b |> map echo prefix $ suffix
        ```
        """
        self.env[LAST_RESULTS] = []

        lines = args.split(delimiter)
        msg = 'Not enough arguments. Usage: `map f [args..] $ [args..]`.'
        if len(lines) <= 1:
            log(msg)
            return

        items = lines[0].split(' ')
        if len(items) <= 1:
            log(msg)
            return

        f, *args, line = items
        lines = [line] + lines[1:]

        if '$' in args:
            i = args.index('$')
        else:
            i = -1

        # collect all results
        results = []
        for j, line in enumerate(lines):
            local_args = args.copy()
            line = line.split(' ')

            if i == -1:
                local_args += line
            else:
                local_args[i:i+1] = line

            line = [f] + local_args

            self.env[LAST_RESULTS_INDEX] = j
            results.append(self.run_single_command(line))

        self.env[LAST_RESULTS_INDEX] = 0
        return delimiter.join([str(result) for result in results])

    def do_foreach(self, args):
        """Apply a function to every term or word.

        Usage
        ```sh
        echo a b |> foreach echo
        echo a b |> foreach echo prefix $ suffix
        ```
        """
        f, *args = args.split(' ')
        args = '\n'.join(args)
        return self.do_map(f'{f} {args}')

    def do_flatten(self, args: str) -> str:
        """Convert a space-separated string to a newline-separates string.
        """
        return '\n'.join(args.split(' '))

    def do_strip(self, args: str) -> str:
        """Convert a space-separated string to a newline-separates string.
        """
        return args.strip()

    def do_int(self, args: str) -> str:
        self._save_result(int(args))
        return ''

    def do_float(self, args: str) -> str:
        self._save_result(float(args))
        return ''

    def do_bool(self, args: str) -> str:
        self._save_result(args != FALSE)
        return ''

    def do_not(self, args: str) -> str:
        return FALSE if to_bool(args) else TRUE

    ############################################################################
    # Overrides
    ############################################################################

    def onecmd(self, lines: str, print_result=True) -> bool:
        """Parse and run `line`.
        Returns 0 on success and None otherwise
        """
        result = ''
        try:
            lines = self.onecmd_prehook(lines)
            ast = parse(lines)
            if ast is None:
                raise ShellError('Invalid syntax: AST is empty')

            # for line in ast:
            result = self.run_commands_new_wrapper(ast, result, run=True)

            # if print_result and result is not None:
            #     if result or not self.locals[IF]:
            #         print(result)

        except CancelledError:
            pass

    def run_commands_new_wrapper(self, *args, **kwds):
        try:
            result = self.run_commands_new(*args, **kwds)
            # if isinstance(result, list):
            #     result = ' '.join(result)

            return result

        except ShellPipeError as e:
            if self.ignore_invalid_syntax:
                log(e)
                return

            raise ShellError(e)

        except subprocess.CalledProcessError as e:
            returncode, stderr = e.args
            log(f'Shell exited with {returncode}: {stderr}')

            if self.ignore_invalid_syntax:
                return

            raise ShellError(str(e))

    def run_commands_new(self, ast: Tuple, prev_result='', run=False):
        print_result = True
        if isinstance(ast, Term):
            term = ast
            if run:
                if self.is_function(term):
                    return self.pipe_cmd_py(term, prev_result)
                elif ast.type == 'variable':
                    k = ast[1:]
                    return self.env[k]
                elif ast.type != 'term':
                    return str(term)

                raise ShellError(f'Cannot execute the function {term}')
            return term

        elif isinstance(ast, str):
            return self.run_commands_new(Term(ast), prev_result, run=run)

        key, *values = ast
        if key == 'list':
            items = values[0]
            k = items[0]
            if run and self.is_function(k):
                # TODO if self.is_inline_function(func_name): ...

                # TODO expand vars in other branches as well
                items = list(expand_variables(items, self.env,
                                              self.completenames_options,
                                              self.ignore_invalid_syntax))

                line = ' '.join(quote_all(items, ignore='*'))

                return self.pipe_cmd_py(line, prev_result)

            elif self.ignore_invalid_syntax or not run:
                return items

            raise ShellError(f'Cannot execute the function {k}')

        elif key == 'lines':
            items = values[0]
            for item in items:
                result = self.run_commands_new(item, run=run)

                if isinstance(result, list):
                    result = ' '.join(quote_all(result))

                if print_result and result is not None:
                    if result or not self.locals[IF]:
                        print(result)

        elif key == 'assign':
            op, a, b = values
            a = self.run_commands_new(a)
            if op == '=':
                b = self.run_commands_new(b)
                if run:
                    self.set_env_variables(a, b)
                    return TRUE
                return a, op, b

            elif op == LEFT_ASSIGNMENT:
                b = self.run_commands_new(b, run=run)
                if run:
                    # self.set_env_variables(a, b)
                    self.locals.set(LEFT_ASSIGNMENT, a)
                    self._save_assignee('')
                    return TRUE
                return a, op, b
            elif op == RIGHT_ASSIGNMENT:
                raise NotImplementedError(RIGHT_ASSIGNMENT)

        elif key == 'binary-expression':
            op, a, b = values
            b = self.run_commands_new(b, run=run)
            a = self.run_commands_new(a, run=run)

            if op in delimiters.comparators:
                # TODO join a, b
                if run:
                    return self.eval(['math', a, op, b])
                return a, op, b

            if op in '+-*/':
                # math
                if run:
                    return self.eval(['math', a, op, b])
                return a, op, b

            else:
                raise ValueError('??')

        elif key == 'pipe':
            op, a, b = values

            prev = self.run_commands_new(a, prev_result, run=run)

            if op == '|>':
                next = self.run_commands_new(b, prev, run=run)
            elif op == '>>=':
                # monadic bind
                # https://en.wikipedia.org/wiki/Monad_(functional_programming)

                if isinstance(b, str) or isinstance(b, Term):
                    line = f'map {b}'
                else:
                    items = ['map'] + self.run_commands_new(b, '')
                    line = ' '.join(quote_all(items, ignore=['*', '$']))

                return self.pipe_cmd_py(line, prev)

            else:
                raise ShellError(f'unknown operator {op}')
            return next

        elif key == 'bash':
            op, a, b = values
            prev = self.run_commands_new(a, prev_result, run=run)
            line = self.run_commands_new(b, run=False)

            # TODO also quote prev result
            if not isinstance(line, str) and not isinstance(line, Term):
                line = ' '.join(quote_all(line, ignore=['*']))

            next = self.pipe_cmd_sh(line, prev, delimiter=op)
            return next

        elif key == 'break':
            _, a, b = ast
            a = self.run_commands_new(a, prev_result, run=True)
            print_result = True
            if print_result and a is not None:
                print(a)

            b = self.run_commands_new(b, run=True)
            return b

        elif key == 'indent':
            # TODO
            _, _width, value = ast
            return self.run_commands_new(value, prev_result, run=True)

        elif key == 'math':
            _key, values = ast
            if values[0] == 'binary-expression':
                values = values
            terms = self.run_commands_new(values)
            line = 'math ' + ' '.join(quote_all(terms, ignore=list('*<>')))
            if run:
                return self.pipe_cmd_py(line, prev_result)
            return line

        elif key == 'logic':
            op, a, b = values
            a = self.run_commands_new(a, run=run)
            b = self.run_commands_new(b, run=run)
            if run:
                a = to_bool(a)
                b = to_bool(b)
                if op == 'or':
                    return a or b
                elif op == 'and':
                    return a and b

            return ' '.join(quote_all((a, op, b), ignore=list('*<>')))

        elif key == 'if-then':
            condition, then = values
            if not run:
                raise NotImplementedError()

            result = self.run_commands_new(condition, run=run)

            if to_bool(result):
                return self.run_commands_new(then, run=run)
            return ''

        elif key == 'define-inline-function':
            f, args, body = values
            if args:
                args = self.run_commands_new(args)

            # body = self.run_commands_new(body)
            # if isinstance(body, str):
            #     line = body
            # else:
            #     if isinstance(body, Term):
            #         body = [body]

            #     line = ' '.join(quote_all(body, ignore='*'))

            self.env[f] = InlineFunction(body, *args, func_name=f)

        elif key == 'define-function':
            method, args = values
        else:
            0

    def onecmd2(self, line: str, print_result=True) -> bool:
        """Parse and run `line`.
        Returns 0 on success and None otherwise
        """
        try:
            line = self.onecmd_prehook(line)
            self.locals.set(RAW_LINE_INDENT, indent_width(line))

            if DEFINE_FUNCTION in self.locals and self.locals[DEFINE_FUNCTION].multiline:
                self._define_multiline_function(line)
            else:
                lines = list(parse_commands(line,
                                            self.delimiters,
                                            self.ignore_invalid_syntax))
                result = self.run_commands(lines)

                if print_result and result is not None:
                    if result or not self.locals[IF]:
                        print(result)

        except CancelledError:
            pass

        return False

    def postcmd(self, stop, _):
        """Display the shell_ready_signal to indicate termination to a parent process.
        """
        if self.auto_save and self.env:
            try:
                self.save_session()
            except OSError as e:
                log('Autosave: Cannot save session '
                    f'{default_session_filename}: {e}')

        print_shell_ready_signal()
        return stop

    def completenames(self, text, *ignored):
        """Conditionally override Cmd.completenames
        """
        if self.completenames_options:
            return [a for a in self.completenames_options if a.startswith(text)]

        return super().completenames(text, *ignored)

    def default(self, line: str):
        head, *tail = line.split(' ')
        if head in self.env and isinstance(self.env[head], InlineFunction):
            f = self.env[head]
            try:
                result = self.call_inline_function(f, *tail)
            except ShellError:
                # reset local scope
                self.reset_locals()
                raise

            return result

        if line in self._chars_allowed_for_char_method:
            return self._do_char_method(line)

        if self.ignore_invalid_syntax:
            return super().default(line)

        raise ShellError(f'Unknown syntax: {line}')

    ############################################################################
    # Pipes
    ############################################################################

    def run_commands(self, lines: Iterable[List[str]], result=''):
        """Run each command in `lines`.
        The partial results are passed through to subsequent commands.
        """
        if not lines:
            return

        if LEFT_ASSIGNMENT in self.locals:
            self.locals.rm(LEFT_ASSIGNMENT)

        for i, line in enumerate(lines):
            # indent = inline_indent_with(*self.locals[RAW_LINE_INDENT], i)
            indent = self.locals[RAW_LINE_INDENT] + (i,)
            self.locals.set(LINE_INDENT, indent)

            if DEFINE_FUNCTION in self.locals:
                self._extend_inline_function_definition(line)
                result = None
                continue

            self._conditionally_insert_assign_operator(lines, i, line)

            try:
                result = self.run_single_command(line, result)

            except ShellPipeError as e:
                if self.ignore_invalid_syntax:
                    log(e)
                    return

                raise ShellError(e)

            except subprocess.CalledProcessError as e:
                returncode, stderr = e.args
                log(f'Shell exited with {returncode}: {stderr}')

                if self.ignore_invalid_syntax:
                    return

                raise ShellError(str(e))

            # handle inline `<-`
            if DEFINE_FUNCTION not in self.locals \
                    and LEFT_ASSIGNMENT in self.locals \
                    and 'assign' not in line \
                    and not \
                        (len(lines) > i + 1
                         and lines[i+1][0] == LEFT_ASSIGNMENT):
                self._save_assignee(result)
                result = None

        if DEFINE_FUNCTION in self.locals:
            if not self.locals[DEFINE_FUNCTION].multiline:
                if self.locals[DEFINE_FUNCTION].command:
                    self._save_inline_function()
                else:
                    self.locals[DEFINE_FUNCTION].multiline = True
            return

        elif LEFT_ASSIGNMENT in self.locals and not io_util.interactive:
            # cancel assignment
            self._save_assignee(result)
            return

        if RETURN in self.locals:
            self.locals.set(RETURN,  result)
            return

        return result

    def _conditionally_insert_assign_operator(self, lines, i, line):
        if LEFT_ASSIGNMENT not in self.locals \
                and i+1 < len(lines) \
                and '<-' in lines[i+1]:
            # prefix line if '<-' is used later on
            j = 1 if ';' in line else 0
            line.insert(j, 'assign')

    def _extend_inline_function_definition(self, line):
        if not self.locals[DEFINE_FUNCTION].multiline:
            if ':' in line:
                line = line[1:]

        cmd = ' ' + ' '.join(line)
        if self.locals[DEFINE_FUNCTION].multiline:
            self.locals[DEFINE_FUNCTION].inner[-1] += cmd
        else:
            self.locals[DEFINE_FUNCTION].command += cmd
        return line

    def run_single_command(self, command_and_args: List[str], prev_result: str = '') -> str:
        prev_result = self.filter_result(command_and_args, prev_result)

        prefixes, line, infix_operator_args = self.parse_single_command(
            command_and_args)

        close_prev_if_statements(self, prefixes)

        if not for_any([IF, THEN, ELSE], contains, prefixes):
            try:
                handle_prev_then_else_statements(self)
            except Abort:
                return prev_result

        if prefixes:
            if THEN in prefixes or ELSE in prefixes:
                try:
                    handle_then_else_statements(self, prefixes, prev_result)
                except Done as result:
                    return result.args[0]

                if not self.is_function(line.split(' ')[0]):
                    line = 'echo ' + line

            if RETURN in prefixes:
                if RETURN not in self.locals:
                    self.locals.set(RETURN, None)

                if len(prefixes) == 1 and not self.is_function(line.split(' ')[0]):
                    line = 'echo ' + line

            if prefixes[-1] == IF:
                return handle_if_statement(self, line, prev_result)

            elif prefixes[-1] in delimiters.bash:
                return self.pipe_cmd_sh(line, prev_result, delimiter=prefixes[-1])

            elif prefixes[-1] == '>>=':
                # monadic bind
                # https://en.wikipedia.org/wiki/Monad_(functional_programming)
                line = f'map {line}'
                return self.pipe_cmd_py(line, prev_result)

            elif prefixes[-1] == RIGHT_ASSIGNMENT:
                # TODO verify syntax of `line`
                assert ' ' not in line
                self.set_env_variables(line, prev_result)
                return ''

        if infix_operator_args:
            return self.infix_command(*infix_operator_args)
        elif is_function_definition(command_and_args):
            return self.handle_define_inline_function(command_and_args)

        return self.pipe_cmd_py(line, prev_result)

    def _save_assignee(self, result: str):
        keys = self.locals[LEFT_ASSIGNMENT]

        self.locals.rm(LEFT_ASSIGNMENT)

        if result is None:
            raise ShellError(f'Missing return value in assignment: {keys}')
        elif result.strip() == '' and self._last_results:
            result = self._last_results
            self.env[LAST_RESULTS] = []

        self.set_env_variables(keys, result)

    def filter_result(self, command_and_args, result):
        if ';' in command_and_args:

            if result is not None and LEFT_ASSIGNMENT not in self.locals:
                # print prev result & discard it
                print(result)

            result = ''

        elif result is None:
            raise ShellPipeError('Last return value was absent')

        return result

    def infer_shell_prefix(self, command_and_args):
        # can raise IndexError

        # assume there is at most 1 delimiter
        prefixes = list(split_prefixes(command_and_args, self.delimiters))
        prefix = prefixes[-1]

        if prefix in delimiters.bash:
            return prefix

    def parse_single_command(self, command_and_args: List[str]) -> Tuple[List[str], str, List[str]]:
        # strip right-hand side delimiters
        all_args = list(omit_prefixes(command_and_args, self.delimiters))
        all_args = list(expand_variables(all_args, self.env,
                        self.completenames_options, self.ignore_invalid_syntax))
        _f, *args = all_args
        line = ' '.join(all_args)

        there_is_an_infix_operator = for_any(
            self.infix_operators, contains, args)

        infix_operator_args = all_args if there_is_an_infix_operator else []

        # assume there is at most 1 delimiter
        prefixes = list(split_prefixes(command_and_args, self.delimiters))

        return prefixes, line, infix_operator_args

    def pipe_cmd_py(self, line: str, result: str):
        # append arguments
        line = f'{line} {result}'

        return super().onecmd(line)

    def pipe_cmd_sh(self, line: str, prev_result: str, delimiter='|') -> str:
        """
        May raise subprocess.CalledProcessError
        """
        assert delimiter in delimiters.bash

        if delimiter == '>-':
            delimiter = '>'

        # pass last result to stdin
        line = f'echo {shlex.quote(prev_result)} {delimiter} {line}'

        logging.info(f'Cmd = {line}')

        result = subprocess.run(args=line,
                                capture_output=True,
                                check=True,
                                shell=True)

        stdout = result.stdout.decode().rstrip('\n')
        stderr = result.stderr.decode().rstrip('\n')

        log(stderr)
        return stdout

    def infix_command(self, *args: str):
        """Treat `args` as an infix command.
        Apply the respective infix method to args.
        E.g.  `a = 1`
        """

        # greedy search for the first occurence of `op`
        for op, method in self.infix_operators.items():
            if op not in args:
                continue

            try:
                lhs, rhs = infer_infix_args(op, *args)
            except ValueError:
                msg = f'Invalid syntax for infix operator {op}'
                if self.ignore_invalid_syntax:
                    log(msg)
                    return
                raise ShellError(msg)

            return method(lhs, *rhs)

        raise ValueError()

    ############################################################################
    # Environment Variables
    ############################################################################

    def set_env_variable(self, k: str, *values: str):
        """Set the variable `k` to `values`
        """
        if not is_valid_method_name(k):
            raise ShellError(f'Invalid variable name format: {k}')

        log(f'set {k}')
        self.env[k] = ' '.join(values)
        return k

    def set_env_variables(self, keys: Union[str, List[str]], result: str):
        """Set the variables `keys` to the values in result.
        """
        if result is None:
            raise ShellError(f'Missing return value in assignment: {keys}')

        if isinstance(keys, str):
            keys = keys.split(' ')

        try:
            if len(result) == len(keys):
                self.env.update(items=zip(keys, result))
                return
        except TypeError:
            pass

        if len(keys) == 1:
            self.env[keys[0]] = result
        elif isinstance(result, str):
            lines = result.split('\n')
            terms = result.split(' ')
            if len(lines) == len(keys):
                self.env.update(items=zip(keys, lines))

            elif len(terms) == len(keys):
                self.env.update(items=zip(keys, terms))

            elif result == '':
                self.env.update(items=zip(keys, repeat('')))

        else:
            raise ShellError(
                f'Cannot assign values to all keys: {" ".join(keys)}')

    def handle_set_env_variable(self, lhs: Tuple[str], *rhs: str) -> str:
        self.set_env_variables(lhs, ' '.join(rhs))
        return ''

    ############################################################################
    # Persistency: Save/load sessions to disk
    ############################################################################

    def save_session(self, session=default_session_filename):
        self.save_session_prehook()

        if not self.env:
            logging.info('No env data to save')
            return

        self.reset_locals()
        env = filter_private_keys(self.locals[ENV])

        with open(session, 'w') as f:
            try:
                json = dumps(env)
            except TypeError:
                logging.debug('Cannot serialize self.env')
                try:
                    json = dumps(env, skip_keys=True)
                except TypeError:
                    json = dumps(asdict(env))

            f.write(json)

    def reset_locals(self):
        self.locals.cd()

    def try_load_session(self, session=default_session_filename):
        self.load_session(session, strict=False)

    def load_session(self, session: str = None, strict=True):
        try:
            with open(session) as f:
                data = f.read()

        except OSError as e:
            if strict:
                raise ShellError(e)

            log(f'Session file not found: {session}: {e}')
            return

        if not data:
            logging.info('No env data found')
            return

        env = loads(data)

        self.reset_locals()
        log(f'Using session: {session}')
        print('Env')
        show(env, when=is_public)

        # TODO handle key conflicts
        self.env.update(env)

        self.load_session_posthook()

    ############################################################################
    # Inline & Multiline Functions
    ############################################################################

    def call_inline_function(self, f: InlineFunction, *args: str):
        translations = {}

        if len(args) != len(f.args):
            raise ShellError(
                f'Invalid number of arguments: {len(f.args)} arguments expected .')

        # translate variables in inline functions
        for i, k in enumerate(f.args):
            # quote item to preserve `\n`
            translations[k] = shlex.quote(args[i])

        with enter_new_scope(self):

            for i, k in enumerate(f.args):
                # quote item to preserve `\n`
                self.env[k] = shlex.quote(args[i])

            if f.inner == []:
                return self.run_commands_new(f.command, run=True)

            for line in f.inner:
                self.onecmd(line, print_result=False)

                if RETURN in self.locals:
                    if self.locals[RETURN] is None:
                        raise ShellError('invalid state')
                    return self.locals[RETURN]

            terms = [term for term in f.command.split(' ') if term != '']
            if not f.multiline:
                terms = list(translate_terms(terms, translations))

            # don't re-quote terms to maintain newlines
            result = self.eval(terms, quote=False)

        return result

    def handle_define_inline_function(self, terms: List[str]) -> str:
        f, *args = terms
        args = [arg for arg in args if arg != '']

        if not args or not args[0].startswith('(') or not args[-1].endswith(')'):
            lhs = ' '.join(terms)
            raise ShellError(f'Invalid syntax for inline function: {lhs}')

        # strip braces
        if args[0] == '()':
            args = []
        else:
            args[0] = args[0][1:]
            args[-1] = args[-1][:-1]

        self.locals.set(DEFINE_FUNCTION,
                        InlineFunction('', *args, func_name=f,
                                       line_indent=self.locals[RAW_LINE_INDENT]))

    def _define_multiline_function(self, indented_line: str):
        line = indented_line.lstrip()

        if line.startswith(RETURN + ' ') and (
                self.locals[RAW_LINE_INDENT] <= self.locals[DEFINE_FUNCTION].line_indent or
                not self.locals[DEFINE_FUNCTION].inner):

            if self.locals[RAW_LINE_INDENT] < self.locals[DEFINE_FUNCTION].line_indent:
                raise ShellError(
                    f'Function defintion did not end with {RETURN}')

            # TODO fix indent
            line = removeprefix(line, RETURN + ' ')
            self.locals[DEFINE_FUNCTION].command = line
            self._save_inline_function()

        else:
            # update line indent on the first line
            if self.locals[DEFINE_FUNCTION].inner == []:
                self.locals[DEFINE_FUNCTION].line_indent = self.locals[RAW_LINE_INDENT]

            self.locals[DEFINE_FUNCTION].inner.append(indented_line)

    def _save_inline_function(self) -> str:
        func = self.locals[DEFINE_FUNCTION]
        self.locals.rm(DEFINE_FUNCTION)

        f = func.func_name
        if has_method(self, f'do_{f}'):
            raise ShellError(
                f'Name conflict: Cannot define inline function {f}, '
                f'because there already exists a method do_{f}.')

        if not is_valid_method_name(f):
            raise ShellError(f'Invalid function name format: {f}')

        if not func.multiline:
            func.command = expand_variables_inline(func.command, self.env,
                                                   self.completenames_options,
                                                   self.ignore_invalid_syntax)

        self.env[f] = func
        positionals = ' '.join(func.args)
        log(f'function {f}({positionals});')


def is_function_definition(terms: List[str]) -> bool:
    terms = [term for term in terms if term != '']

    if len(terms) < 2:
        return

    if len(terms) == 2:
        term = terms[-1]
        first = term
        last = term
    else:
        _f, first, *_, last = terms

    return first.startswith('(') and last.endswith(')')


def to_bool(line: str) -> bool:
    return TRUE if line != FALSE else FALSE


def is_public(key: str) -> bool:
    return not is_private(key)


def is_private(key: str) -> bool:
    return key.startswith('_')


def filter_private_keys(env: dict) -> dict:
    env = env.copy()
    for k in list(env.keys()):
        if is_private(k):
            del env[k]
    return env


def scope() -> dict:
    return defaultdict(dict)


@contextmanager
def enter_new_scope(cls: BaseShell, scope_name=INNER_SCOPE):
    """Create a new scope, then change directory into that scope. 
    Finally exit the new scope.
    """
    cls.locals.set(scope_name, scope())
    try:
        with cd(cls.locals, scope_name):
            cls.init_current_scope()
            yield
    finally:
        pass
