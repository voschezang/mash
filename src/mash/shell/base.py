from asyncio import CancelledError
from cmd import Cmd
from collections import defaultdict
from dataclasses import asdict
from itertools import chain
from json import dumps, loads
from operator import contains
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union
import logging
import shlex
import subprocess

from mash import io_util
from mash.filesystem.filesystem import FileSystem
from mash.io_util import log, shell_ready_signal, print_shell_ready_signal, check_output
from mash.util import for_any, has_method, identity, is_alpha, is_globbable, omit_prefixes, split_prefixes, split_sequence, glob
from mash.shell.function import InlineFunction

confirmation_mode = False
bash_delimiters = ['|', '>', '>>', '1>', '1>>', '2>', '2>>']
py_delimiters = [';', '|>', '>>=']
other_delimiters = ['=', '<-', '->']
default_session_filename = '.shell_session.json'


Command = Callable[[Cmd, str], str]
Types = Union[str, bool, int, float]


class ShellError(RuntimeError):
    pass


class ShellPipeError(RuntimeError):
    pass


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

        self.env = {}
        self.locals = FileSystem(defaultdict(dict))
        self.update_env(env)

        self.auto_save = False
        self.auto_reload = False

        # internals
        self._do_char_method = self.none
        self._chars_allowed_for_char_method: List[str] = []
        self._last_results = None

        self.set_infix_operators()
        if self.auto_reload:
            self.try_load_session()

    @property
    def delimiters(self):
        # Return the latest values of these lists
        return py_delimiters + bash_delimiters + ['->']

    def set_infix_operators(self):
        # use this for infix operators, e.g. `a = 1`
        self.infix_operators = {'=': self.handle_equation,
                                '<-': self.eval_and_set_env_variable}
        # the sign to indicate that a variable should be expanded
        self.variable_prefix = '$'

    def set_do_char_method(self, method: Command, chars: List[str]):
        """Use `method` to interpret commands that start any item in `chars`.
        This allow special chars to be used as commands.
        E.g. transform `do_$` into `do_f $`

        Naming conflicts with existing `delimiters` are resolved.
        """
        self._do_char_method = method
        self._chars_allowed_for_char_method = chars
        self.resolve_char_name_conflicts()

    def resolve_char_name_conflicts(self):
        # TODO don't mutate global vars
        for char in self._chars_allowed_for_char_method:
            if char in bash_delimiters:
                logging.warning(
                    f'Overriding default sh delimiters: remove {char}')
                bash_delimiters.remove(char)

            if char in py_delimiters:
                logging.warning(
                    f'Overriding default py delimiters: remove {char}')
                py_delimiters.remove(char)

    def update_env(self, env: Dict[str, Any] = None):
        if env is None:
            return

        for k in self.env:
            if k not in env:
                env[k] = self.env[k]

        self.env = env

    def eval(self, args: Iterable[str]) -> Types:
        """Evaluate / run `args` and return the result.
        """
        # convert args to a shell command

        k = '_eval_output'

        args = ' '.join(shlex.quote(arg) for arg in args)
        line = f'{args} |> export {k}'

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
            return self.env[k]

        elif self._last_results:
            return self._last_results.pop()

        raise RuntimeError('Cannot retrieve result')

    def handle_equation(self, lhs: Tuple[str], *rhs: str):
        if len(lhs) == 1:
            k = lhs[0]
            return self.set_env_variable(k, *rhs)

        f, *args = lhs
        implementation = ' '.join(rhs[1:])
        return self.add_inline_function(f, args, implementation)

    def add_inline_function(self, f, args, inner) -> str:
        if has_method(self, f'do_{f}'):
            raise ShellError(
                f'Name conflict: Cannot define inline function {f}, '
                f'because there already exists a method do_{f}.')

        inner = self.expand_variables_inline(inner)

        # TODO use custom class with attr .functions instead of a string
        self.locals['functions'][f] = InlineFunction(inner, *args)

        positionals = ' '.join(args)
        log(f'function {f}({positionals});')
        return ''

    def call_inline_function(self, f: InlineFunction, *args: str):
        translations = {}

        for i, k in enumerate(f.args):
            translations[k] = args[i]

        terms = list(self.translate_terms(f.command.split(' '), translations))
        line = ' '.join(terms)

        first_func = terms[0]
        if not has_method(self, f'do_{first_func}') \
                and first_func not in self.locals['functions']:
            terms = ['print'] + terms

        line = ' '.join(terms)
        return super().onecmd(line)

    def set_env_variable(self, k: str, *values: str):
        """Set the variable `k` to `values`
        """
        self.env[k] = ' '.join(values)
        return k

    def eval_and_set_env_variable(self, k: Tuple[str], *values: str):
        """Evaluate `values` as an expression and store the result in the variable `k`
        """
        k: str = k[0]

        try:
            result = self.eval(values)
        except ShellError:
            log(f'Error, cannot set {k}')
            return

        self.env[k] = result
        return k

    def show_env(self, env=None):
        if env is None:
            env = self.env

        if not env:
            return

        print('Env')
        for k in env:
            print(f'\t{k}: {env[k]}')

    def onecmd_prehook(self, line):
        """Similar to cmd.precmd but executed before cmd.onecmd
        """
        if confirmation_mode:
            assert io_util.interactive
            log('Command:', line)
            if not io_util.confirm():
                raise CancelledError()

        return line

    def save_session(self, session=default_session_filename):
        self.save_session_prehook()

        if not self.env:
            logging.info('No env data to save')
            return

        with open(session, 'w') as f:
            try:
                json = dumps(self.env)
            except TypeError:
                logging.debug('Cannot serialize self.env')
                try:
                    json = dumps(self.env, skip_keys=True)
                except TypeError:
                    json = dumps(asdict(self.env))

            f.write(json)

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

        log(f'Using session: {session}')
        self.show_env(env)

        # TODO handle key conflicts
        self.update_env(env)

        self.load_session_posthook()

    ############################################################################
    # Commands: do_*
    ############################################################################

    def do_export(self, args: str):
        """Set an environment variable.
        `export(k, *values)`
        """
        if not args:
            return ''

        k, *values = args.split()

        if len(values) == 0:
            log(f'unset {k}')
            if k in self.env:
                del self.env[k]
            else:
                logging.warn('Invalid key')
            return

        log(f'set {k}')
        self.set_env_variable(k, *values)

    def do_shell(self, args):
        """System call
        """
        logging.info(f'Cmd = !{args}')
        return check_output(args)

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
        lines = args.split(delimiter)
        msg = 'Not enough arguments. Usage: `map f [args] *`.'
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
        for line in lines:
            local_args = args.copy()
            line = line.split(' ')

            if i == -1:
                local_args += line
            else:
                local_args[i:i+1] = line

            line = [f] + local_args

            results.append(self.run_single_command(line))

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

    def do_int(self, args: str) -> str:
        self._save_result(int(args))
        return ''

    def do_float(self, args: str) -> str:
        self._save_result(float(args))
        return ''

    def do_bool(self, args: str) -> str:
        self._save_result(bool(args))
        return ''

    ############################################################################
    # Overrides
    ############################################################################

    def onecmd(self, line: str) -> bool:
        """Parse and run `line`.
        Returns 0 on success and None otherwise
        """
        try:
            line = self.onecmd_prehook(line)
            lines = self.parse_commands(line)
            self.run_commands(lines)

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
        if head in self.locals['functions']:
            f = self.locals['functions'][head]
            return self.call_inline_function(f, *tail)

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

        for line in lines:
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

        if result is not None:
            print(result)

    def run_single_command(self, command_and_args: List[str], result: str = '') -> str:
        result = self.filter_result(command_and_args, result)

        prefixes, line, infix_operator_args = self.parse_single_command(
            command_and_args)

        if prefixes:
            if prefixes[-1] in bash_delimiters:
                return self.pipe_cmd_sh(line, result, delimiter=prefixes[-1])

            elif prefixes[-1] == '>>=':
                # monadic bind
                # https://en.wikipedia.org/wiki/Monad_(functional_programming)
                line = f'map {line}'
                return self.pipe_cmd_py(line, result)

            elif prefixes[-1] == '->':
                # TODO verify syntax
                assert ' ' not in line
                return self.set_env_variable(line, result)

        if infix_operator_args:
            return self.infix_command(*infix_operator_args)

        return self.pipe_cmd_py(line, result)

    def filter_result(self, command_and_args, result):
        if ';' in command_and_args:
            # print prev result & discard it
            if result is not None:
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

        if prefix in bash_delimiters:
            return prefix

    def parse_single_command(self, command_and_args: List[str]) -> Tuple[List[str], str, List[str]]:
        # strip right-hand side delimiters
        all_args = list(omit_prefixes(command_and_args, self.delimiters))
        f, *args = all_args
        args = list(self.expand_variables(args))
        line = ' '.join(chain.from_iterable(([f], args)))

        # TODO make this check quote-aware
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
        assert delimiter in bash_delimiters

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

    ############################################################################
    # Argument Parsing
    ############################################################################

    def parse_commands(self, line: str) -> Iterable[List[str]]:
        """Split up `line` into an iterable of single commands.
        """
        try:
            # split lines and handle quotes
            # e.g. convert 'echo "echo 1"' to ['echo', 'echo 1']
            terms = shlex.split(line, comments=True)

        except ValueError as e:
            msg = f'Invalid syntax: {e} for {str(line)[:10]} ..'
            if self.ignore_invalid_syntax:
                log(msg)
                return []

            raise ShellError(msg)

        if not terms:
            return []

        ################################################################################
        # handle lines that end with `;`
        # e.g. 'echo 1; echo 2;'
        # TODO this doesn't preserve ; when it was originally enclosed in quotes
        # terms = chain.from_iterable([split_tips(term.strip(), ';') for term in terms])
        ################################################################################

        # group terms based on delimiters
        return split_sequence(terms, self.delimiters, return_delimiters=True)

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
                lhs, rhs = self.infer_infix_args(op, *args)
            except ValueError:
                msg = f'Invalid syntax for infix operator {op}'
                if self.ignore_invalid_syntax:
                    log(msg)
                    return
                raise ShellError(msg)

            return method(lhs, *rhs)

        raise ValueError()

    def infer_infix_args(self, op: str, *args: str) -> Tuple[Tuple[str], Tuple[str]]:
        if args[1] == op:
            lhs, _, *rhs = args
            lhs = (lhs,)
        else:
            i = args.index(op)
            lhs = args[:i]
            rhs = args[i:]
        return lhs, rhs

    def expand_variables(self, variables: List[str]) -> Iterable[str]:
        """Replace variables with their values. 
        E.g.
        ```sh
        a = 1
        print $a # gets converted to `print 1`
        ```
        """
        for v in variables:
            if len(v) >= 2 and v[0] == self.variable_prefix:
                k = v[1:]

                if not self.variable_name_is_valid(k):
                    # ignore this variable silently
                    yield v
                    continue

                error_msg = f'Variable `{v}` is not set'

                if k in self.env:
                    yield self.env[k]
                    continue
                elif self.ignore_invalid_syntax:
                    log(error_msg)
                else:
                    raise ShellError(error_msg)

            elif is_globbable(v):
                try:
                    matches = glob(v, self.completenames_options, strict=True)
                    yield ' '.join(matches)
                    continue

                except ValueError as e:
                    if self.ignore_invalid_syntax:
                        log(f'Invalid syntax: {e}')
                    else:
                        raise ShellError(e)

            yield v

    def expand_variables_inline(self, line: str):
        """Expand $variables in `line`.
        """
        terms = line.split(' ')
        expanded_terms = self.expand_variables(terms)
        line = ' '.join(expanded_terms)
        return line

    def variable_name_is_valid(self, k: str) -> bool:
        return is_alpha(k, ignore='_')

    def none(self, _: str) -> str:
        """Do nothing. Similar to util.none.
        This is a default value for self._do_char_method.
        """
        return ''

    def _save_result(self, value, overwrite=True):
        if overwrite:
            self._last_results = [value]
        else:
            self._last_results.append(value)

    def translate_terms(self, terms: Iterable[str], translations: dict):
        for term in terms:
            term = term.strip()
            if term in translations:
                yield str(translations[term])
                continue

            yield term
