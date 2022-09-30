#!/usr/bin/python3
from asyncio import CancelledError
from cmd import Cmd
from itertools import chain
from json import dumps, loads
from operator import contains
from typing import Any, Callable, Dict, Iterable, List, Literal, Tuple
import logging
import shlex
import subprocess

import io_util
from io_util import log, shell_ready_signal, print_shell_ready_signal
from util import for_any, omit_prefixes, split_prefixes, split_sequence

confirmation_mode = False
bash_delimiters = ['|', '>', '>>', '1>', '1>>', '2>', '2>>']
py_delimiters = [';', '|>']
default_session_filename = '.shell_session.json'


class ShellException(RuntimeError):
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
    # TODO store/recover sessions using self.env

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        # fill this list to customize autocomplete behaviour
        self.completenames_options = []

        # defaults
        self.ignore_invalid_syntax = True
        self.env = {}
        self.auto_save = False
        self.auto_reload = False

        # internals
        self._do_char_method = None
        self._chars_allowed_for_char_method = []

        self.set_infix_operators()
        if self.auto_reload:
            self.try_load_session()

    @property
    def delimiters(self):
        # Return the latest values of these lists
        return py_delimiters + bash_delimiters

    def set_infix_operators(self):
        # use this for infix operators, e.g. `a = 1`
        self.infix_operators = {'=': self.set_env_variable}
        # the sign to indicate that a variable should be expanded
        self.variable_prefix = '$'

    def set_do_char_method(self, method: Callable[[object, str], Any], chars: List[str]):
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

    def set_env_variable(self, k, v):
        self.env[k] = v
        return k

    def show_env(self, env=None):
        if env is None:
            env = self.env

        if not env:
            return

        print('Env')
        for k, v in env.items():
            print(f'\t{k}: {v}')

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
        with open(session, 'w') as f:
            f.write(dumps(self.env))

    def try_load_session(self, session=default_session_filename):
        self.load_session(session, strict=False)

    def load_session(self, session: str, strict=True):
        try:
            with open(session) as f:
                env = loads(f.read())

        except OSError as e:
            if strict:
                raise ShellException(e)

            log(f'Session file not found: {session}: {e}')
            return

        log(f'Using session: {session}')
        self.show_env(env)

        # TODO handle conflicts
        self.env.update(env)

    ############################################################################
    # Overrides
    ############################################################################

    def onecmd(self, line: str) -> Literal[0]:
        """Parse and run `line`.
        Returns 0 on success and None otherwise
        """

        try:
            line = self.onecmd_prehook(line)
            lines = self.parse_commands(line)
            self.run_commands(lines)

        except CancelledError:
            pass

        return 0

    def postcmd(self, stop, _):
        """Display the shell_ready_signal to indicate termination to a parent process.
        """
        if self.auto_save:
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

    def default(self, line):
        if line in self._chars_allowed_for_char_method and self._do_char_method:
            return self._do_char_method(line)

        if self.ignore_invalid_syntax:
            super().default(line)
        else:
            raise ShellException(f'Unknown syntax: {line}')

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

            except subprocess.CalledProcessError as e:
                returncode, stderr = e.args
                log(f'Shell exited with {returncode}: {stderr}')

                raise ShellException(str(e))

        if result is not None:
            print(result)

    def run_single_command(self, command_and_args: List[str], result: str = '') -> str:
        result = self.filter_result(command_and_args, result)

        prefixes, line, infix_operator_args = self.parse_single_command(
            command_and_args)

        if prefixes and prefixes[-1] in bash_delimiters:
            return self.pipe_cmd_sh(line, result, delimiter=prefixes[-1])

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
            raise ShellException('Last return value was absent')

        return result

    def infer_shell_prefix(self, command_and_args):
        # can raise IndexError

        # assume there is at most 1 delimiter
        prefixes = list(split_prefixes(command_and_args, self.delimiters))
        prefix = prefixes[-1]

        if prefix in bash_delimiters:
            return prefix

    def parse_single_command(self, command_and_args: List[str]) -> Tuple[str, List[str], str]:
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
            if self.ignore_invalid_syntax:
                return []

            raise ShellException(
                f'Invalid syntax: {e} for {str(line)[:10]} ..')

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

    def infix_command(self, *args: List[str]):
        """Treat `args` as an infix command.
        Apply the respective infix method to args.
        E.g.  `a = 1`
        """

        # greedy search for the first occurence of `op`
        for op, method in self.infix_operators.items():
            if op not in args:
                continue

            try:
                lhs, _, rhs = args
            except ValueError:
                msg = f'Invalid syntax for infix operator {op}'
                if self.ignore_invalid_syntax:
                    log(msg)
                    return
                raise ShellException(msg)

            return method(lhs, rhs)

        raise ValueError()

    def expand_variables(self, variables: List[str]) -> Iterable[str]:
        """Replace variables with their values. 
        E.g.
        ```sh
        a = 1
        print $a # gets converted to `print 1`
        ```
        """
        for v in variables:
            if len(v) > 1 and v[0] == self.variable_prefix:
                k = v[1:]
                msg = f'Variable `{v}` is not set'

                if k in self.env:
                    yield self.env[k]
                    continue
                elif self.ignore_invalid_syntax:
                    log(msg)
                else:
                    raise ShellException(msg)

            yield v
