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
from mash.filesystem.scope import Scope, show
from mash.io_util import log, shell_ready_signal, print_shell_ready_signal, check_output
from mash.shell import delimiters
from mash.shell.delimiters import INLINE_ELSE, INLINE_THEN, DEFINE_FUNCTION, FALSE, IF, LEFT_ASSIGNMENT, RIGHT_ASSIGNMENT, THEN, TRUE, to_bool
from mash.shell.errors import ShellError, ShellPipeError, ShellSyntaxError
from mash.shell.function import InlineFunction
from mash.shell.if_statement import LINE_INDENT, Abort, close_prev_if_statement, close_prev_if_statements,  handle_prev_then_else_statements
from mash.shell.lex_parser import parse
from mash.shell.model import LAST_RESULTS, LAST_RESULTS_INDEX, Else, ElseCondition, Indent, Lines, Map, Node, Term, Terms, Then, Word
from mash.shell.parsing import expand_variables, filter_comments, indent_width, infer_infix_args, quote_items
from mash.util import for_any, has_method, identity, is_valid_method_name, omit_prefixes, quote_all, split_prefixes


confirmation_mode = False
default_session_filename = '.shell_session.json'
default_prompt = '$ '

COMMENT = '#'
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

    intro = 'Press ctrl-d to exit, ctrl-c to cancel, ? for help, ! for shell interop.\n' + \
        shell_ready_signal + '\n'

    prompt = default_prompt

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
        self._default_method = identity

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
            or func_name in self._chars_allowed_for_char_method \
            or func_name == '?'

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
        self.set_env_variables(keys, '')

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

    def do_map(self, args=''):
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
        log('Expected arguments')
        return ''

    def _do_foreach(self, ast: tuple, prev_results: str) -> Iterable:
        """Apply a function to every term or word.

        Usage
        ```sh
        echo a b |> foreach echo
        echo a b |> foreach echo prefix $ suffix
        ```
        """
        prev_results = '\n'.join(prev_results.split(' '))
        return Map.map(ast, prev_results, self, delimiter=' ')

    def foldr(self, commands: List[Term], prev_results: str, delimiter='\n'):
        items = parse(prev_results).values
        k, acc, *args = commands

        for item in items:
            command = Terms([k, acc] + args)
            acc = self.run_commands(command, item, run=True)

            if acc.strip() == '' and self._last_results:
                acc = self._last_results[-1]
                self.env[LAST_RESULTS] = []

        return acc

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
        if lines == 'EOF':
            logging.debug('Aborting: received EOF')
            exit()

        result = ''
        try:
            lines = self.onecmd_prehook(lines)
            ast = parse(lines)
            if ast is None:
                raise ShellError('Invalid syntax: AST is empty')

            result = self.run_commands_new_wrapper(ast, result, run=True)

        except ShellSyntaxError as e:
            if self.ignore_invalid_syntax:
                log(e)
            else:
                raise

        except CancelledError:
            pass

    def run_commands_new_wrapper(self, *args, **kwds):
        try:
            result = self.run_commands(*args, **kwds)
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

    def run_commands(self, ast: Tuple, prev_result='', run=False):
        print_result = True
        if isinstance(ast, Term):
            return ast.run(prev_result, shell=self, lazy=not run)

        elif isinstance(ast, str):
            return self.run_commands(Term(ast), prev_result, run=run)

        if isinstance(ast, Node):
            key, values = None, []
        else:
            key, *values = ast

        if DEFINE_FUNCTION in self.locals:
            # TODO change prompt to reflect this mode

            # self._extend_inline_function_definition(line)
            f = self.locals[DEFINE_FUNCTION]

            if isinstance(ast, Indent):
                # TODO compare indent width
                width = ast.indent
                if ast.data is None:
                    return

                if f.line_indent is None:
                    f.line_indent = width

                if width >= f.line_indent:
                    self.locals[DEFINE_FUNCTION].inner.append(ast)
                    return

                self._finalize_define_function(f)

            elif not isinstance(ast, Lines):
                # TODO this will only be triggered after a non-Word command
                self._finalize_define_function(f)

        if not isinstance(ast, ElseCondition) and \
                not isinstance(ast, Indent) and \
                not isinstance(ast, Lines):
            try:
                handle_prev_then_else_statements(self)
            except Abort:
                return prev_result

        if isinstance(ast, Node):
            return ast.run(prev_result, shell=self, lazy=not run)
        elif key == 'assign':
            return self.run_handle_assign(values, prev_result, run)

        elif key == 'pipe':
            a, b = values
            prev = self.run_commands(a, prev_result, run=run)
            next = self.run_commands(b, prev, run=run)
            return next

        elif key == 'bash':
            op, a, b = values
            prev = self.run_commands(a, prev_result, run=run)
            line = self.run_commands(b, run=False)

            # TODO also quote prev result
            if not isinstance(line, str) and not isinstance(line, Term):
                line = ' '.join(quote_all(line, ignore=['*']))

            next = self.pipe_cmd_sh(line, prev, delimiter=op)
            return next

        elif key == 'math':
            _key, values = ast
            args = self.run_commands(values, prev_result)

            if not run:
                return ['math'] + args

            line = 'math ' + ' '.join(quote_all(args,
                                                ignore=list('*$<>') + ['>=', '<=']))
            return self.pipe_cmd_py(line, '')


        elif key == 'define-inline-function':
            f, args, body = values
            if args:
                args = self.run_commands(args)

            self._define_function(f, args, run)

            # TODO use parsing.expand_variables_inline
            self.env[f] = InlineFunction(body, args, func_name=f)

        elif key == 'define-function':
            f, args = values

            self._define_function(f, args, run)

            if isinstance(args, Terms):
                args = [str(arg) for arg in args]
            else:
                args = [str(args)]

            # TODO use line_indent=self.locals[RAW_LINE_INDENT]
            self.locals.set(DEFINE_FUNCTION,
                            InlineFunction('', args, func_name=f))
            self.prompt = '>>>    '

        elif key == 'return':
            line = values[0]
            result = self.run_commands(line, run=run)
            return ('return', result)

        elif key == '!':
            terms = self.run_commands(values[0])
            if isinstance(terms, str) or isinstance(terms, Term):
                line = str(terms)
            else:
                line = ' '.join(terms)

            if line == '' and prev_result == '':
                print('No arguments received for `!`')
                return FALSE

            if run:
                return self.pipe_cmd_sh(line, prev_result, delimiter=None)
            return ' '.join(line)

        else:
            raise NotImplementedError()

    def _finalize_define_function(self, f):
        self.env[f.func_name] = f
        self.locals.rm(DEFINE_FUNCTION)
        self.prompt = default_prompt

    def run_handle_indent(self, args, prev_result, run):
        width, inner = args
        if inner is None:
            return

        if self.locals[IF]:
            if not run:
                raise NotImplementedError()

            closed = self._last_if['branch'] in (INLINE_THEN, INLINE_ELSE)

            if width < self._last_if['line_indent'] or (
                    width == self._last_if['line_indent'] and
                inner[0] not in ['then', 'else'] and
                    not isinstance(inner[0], Then) and
                    not isinstance(inner[0], Else)):

                close_prev_if_statements(self, width)

            if self.locals[IF] and width > self._last_if['line_indent']:
                if closed:
                    raise ShellSyntaxError(
                        'Unexpected indent after if-else clause')
                try:
                    handle_prev_then_else_statements(self)
                except Abort:
                    return prev_result

        self.locals.set(LINE_INDENT, width)
        return self.run_commands(inner, prev_result, run=run)

    def run_handle_terms(self, values, prev_result: str, run: bool):
        items = values[0]
        if len(items) >= 2 and run:
            k, *args = items
            if k == 'map':
                args = Terms(list(args))
                return Map.map(args, prev_result, self)
            elif k == 'foreach':
                args = Terms(list(args))
                return self._do_foreach(args, prev_result)
            elif k in ['reduce', 'foldr']:
                return self.foldr(args, prev_result)

        # TODO expand vars in other branches as well
        wildcard_value = ''
        if '$' in items:
            wildcard_value = prev_result
            prev_result = ''

        items = list(expand_variables(items, self.env,
                                      self.completenames_options,
                                      self.ignore_invalid_syntax,
                                      wildcard_value))

        k = items[0]
        if run:
            if k == 'echo':
                args = items[1:]
                if prev_result:
                    args += [prev_result]
                line = ' '.join(str(arg) for arg in args)
                return line

            if self.is_function(k):
                # TODO if self.is_inline_function(k): ...
                # TODO standardize quote_all args
                line = ' '.join(quote_all(items, ignore='*$?'))
                return self.pipe_cmd_py(line, prev_result)

        if prev_result:
            items += [prev_result]
        if run:
            return ' '.join(str(v) for v in items)
        return items

    def run_handle_lines(self, values, prev_result: str, run: bool, print_result: bool):
        items = values[0]
        for item in items:

            width = indent_width('')
            if self.locals[IF] and not isinstance(item, Indent) and width > self._last_if['line_indent']:
                close_prev_if_statements(self, width)

            if self.locals[IF] and not isinstance(item, Indent):
                if not isinstance(item, Then) and \
                        not isinstance(item, ElseCondition):
                    close_prev_if_statement(self)

            result = self.run_commands(item, run=run)

            # TODO if isinstance(result, tuple):
            # return ('return', result)
            if isinstance(result, tuple) and result[0] == 'return':
                return result[1]

            if isinstance(result, list):
                # result = ' '.join(quote_all(result))
                # result = ' '.join(str(s) for s in result)
                result = str(result)

            if print_result and result is not None:
                if result or not self.locals[IF]:
                    print(result)

    def run_handle_assign(self, values, prev_result, run):
        op, a, b = values
        a = self.run_commands(a)
        if op == '=':
            b = self.run_commands(b)
            if run:
                self.set_env_variables(a, b)
                return TRUE
            return a, op, b

        elif op == LEFT_ASSIGNMENT:
            values = self.run_commands(b, run=run)

            if values is None:
                values = ''

            if values.strip() == '' and self._last_results:
                values = self._last_results
                self.env[LAST_RESULTS] = []

            if run:
                self.set_env_variables(a, values)
                return TRUE
            return a, op, values

        elif op == RIGHT_ASSIGNMENT:
            raise NotImplementedError(RIGHT_ASSIGNMENT)

        raise NotImplementedError()

    def _define_function(self, f, args, run):
        if not run:
            raise NotImplementedError()

        if has_method(self, f'do_{f}'):
            raise ShellError()
        elif self.is_function(f):
            logging.debug(f'Re-define existing function: {f}')

        if self.auto_save:
            logging.warning(
                'Instances of InlineFunction are incompatible with serialization')
            self.auto_save = False

        if isinstance(args, Terms):
            args = [str(arg) for arg in args]
        else:
            args = [str(args)]
        return args

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

        raise ShellSyntaxError(f'Unknown syntax: {line}')

    ############################################################################
    # Pipes
    ############################################################################

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
        assert delimiter in delimiters.bash or delimiter is None

        if delimiter == '>-':
            delimiter = '>'

        if delimiter is not None:
            # pass last result to stdin
            line = f'echo {shlex.quote(prev_result)} {delimiter} {line}'

        logging.info(f'Cmd = {line}')

        result = subprocess.run(line,
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
                raise ShellSyntaxError(msg)

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

        if isinstance(keys, str) or isinstance(keys, Term):
            keys = keys.split(' ')

        try:
            if len(result) == len(keys):
                self.env.update(items=zip(keys, result))
                return
        except TypeError:
            pass

        if len(keys) == 1:
            if isinstance(result, list):
                result = ' '.join(quote_all(result))
            self.env[keys[0]] = result
        elif isinstance(result, str) or isinstance(result, Term):
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
            msg = f'Invalid number of arguments: {len(f.args)} arguments expected.'
            if self.ignore_invalid_syntax:
                log(msg)
                return FALSE
            else:
                raise ShellError(msg)

        # translate variables in inline functions
        for i, k in enumerate(f.args):
            # quote item to preserve `\n`
            translations[k] = shlex.quote(args[i])

        with enter_new_scope(self):

            for i, k in enumerate(f.args):
                # quote item to preserve `\n`
                # self.env[k] = shlex.quote(args[i])
                self.env[k] = args[i]

            if f.inner == []:
                return self.run_commands(f.command, run=True)

            # TODO rm impossible state
            assert f.command == ''

            result = ''
            for ast in f.inner:
                result = self.run_commands(ast, prev_result=result,
                                           run=True)
                if isinstance(result, tuple) and result[0] == 'return':
                    return result[1]

            if isinstance(result, tuple) and result[0] == 'return':
                return result[1]

    def parse(self, results: str):
        return parse(results)


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
