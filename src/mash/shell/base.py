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
from mash.shell.delimiters import DEFINE_FUNCTION, FALSE, IF, LEFT_ASSIGNMENT, RETURN, RIGHT_ASSIGNMENT, THEN, TRUE
from mash.shell.env import ENV, Environment, show
from mash.shell.errors import ShellError, ShellPipeError
from mash.shell.function import InlineFunction
from mash.shell.parsing import expand_variables, expand_variables_inline, filter_comments, infer_infix_args, parse_commands
from mash.util import for_any, has_method, identity, is_valid_method_name, omit_prefixes, removeprefix, split_prefixes, translate_terms


confirmation_mode = False
default_session_filename = '.shell_session.json'

COMMENT = '#'
INNER_SCOPE = 'inner_scope'

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

        self.env = Environment(self.locals)
        if env:
            for k, v in env.items():
                self.env[k] = v

        self.auto_save = False
        self.auto_reload = False

        # internals
        self._do_char_method = self.none
        self._chars_allowed_for_char_method: List[str] = []

        # TODO use self.local to allow nesting
        self._last_results = []
        self._last_result_index = 0

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
        return items

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
            args = (shlex.quote(arg) for arg in args)

        args = list(filter_comments(args))

        if not args:
            return ''

        if not self.is_function(args[0]):
            args = ['echo'] + args

        k = '_eval_output'
        line = ' '.join(args)
        line = f'{line} |> export {k}'

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
        log(f'_save_result [{self._last_result_index}]: {value}')
        if len(self._last_results) < self._last_result_index:
            raise ShellError('Invalid state')
        if len(self._last_results) == self._last_result_index:
            self._last_results.append(None)

        self._last_results[self._last_result_index] = value

    def is_function(self, func_name: str) -> bool:
        return has_method(self, f'do_{func_name}') or self.is_inline_function(func_name)

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
        self._last_results = []

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

            self._last_result_index = j
            results.append(self.run_single_command(line))

        self._last_result_index = 0
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
        if args == FALSE:
            return TRUE
        return FALSE

    ############################################################################
    # Overrides
    ############################################################################

    def onecmd(self, line: str, print_result=True) -> bool:
        """Parse and run `line`.
        Returns 0 on success and None otherwise
        """

        try:
            line = self.onecmd_prehook(line)

            if DEFINE_FUNCTION in self.locals and self.locals[DEFINE_FUNCTION].multiline:
                self._define_multiline_function(line)
            else:
                lines = list(parse_commands(line,
                                            self.delimiters,
                                            self.ignore_invalid_syntax))
                result = self.run_commands(lines)

                if print_result and result is not None:
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

        self.locals.set(IF, [])
        if LEFT_ASSIGNMENT in self.locals:
            self.locals.rm(LEFT_ASSIGNMENT)

        for i, line in enumerate(lines):

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

        if prefixes:
            if THEN in prefixes:
                if not self.locals[IF]:
                    if self.ignore_invalid_syntax:
                        return ''
                    raise ShellError(
                        f'If-then clause requires an {IF} statement')

                self.locals[IF][-1]['depth'] += 1

                if len(prefixes) <= 1 and self.locals[IF][-1]['depth'] >= 2:
                    raise ShellError(
                        f'If-then clause requires an {IF} statement')

                if not self.locals[IF][-1]['value']:
                    # skip
                    return ''
                # otherwise continue

            if prefixes[-1] in delimiters.bash:
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

            elif prefixes[-1] == IF:
                assert_if_then_is_closed = False
                if assert_if_then_is_closed:
                    if self.locals[IF] and self.locals[IF][-1]['depth'] == 0:
                        raise ShellError(
                            f'The previous if-then statement was not closed')

                if self.locals[IF] and not self.locals[IF][-1]['value']:
                    # force value to be false when previous conditions are false
                    value = False
                else:
                    f, *_ = line.split(' ')
                    if self.is_function(f):
                        result = self.eval(line.split(' '), quote=False)
                        value = result != FALSE
                    else:
                        value = line != FALSE

                self.locals[IF].append({'value': value, 'depth': 0})
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
            self._last_results = []

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
        if len(lhs) != 1:
            raise ShellError()

        k = lhs[0]
        self.set_env_variable(k, *rhs)
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
        env = self.locals[ENV]

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
        show(env)

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

            for line in f.inner:
                self.onecmd(line, print_result=False)

            terms = [term for term in f.command.split(' ') if term != '']
            if not f.multiline:
                terms = list(translate_terms(terms, translations))

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
                        InlineFunction('', *args, func_name=f))

    def _define_multiline_function(self, line: str):
        line = line.lstrip()
        if line.startswith(RETURN + ' '):
            line = removeprefix(line, RETURN + ' ')
            self.locals[DEFINE_FUNCTION].command = line
            self._save_inline_function()

        else:
            self.locals[DEFINE_FUNCTION].inner.append(line)

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
