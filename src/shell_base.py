#!/usr/bin/python3
from asyncio import CancelledError
from cmd import Cmd
from itertools import chain
from operator import contains
from typing import Any, Callable, Dict, Iterable, List, Literal, Sequence, Union
import logging
import shlex
import subprocess

import io_util
from io_util import log, shell_ready_signal, print_shell_ready_signal
from util import for_any, omit_prefixes, split_prefixes, split_sequence, split_tips

confirmation_mode = False
bash_delimiters = ['|', '>', '>>', '1>', '1>>', '2>', '2>>']
py_delimiters = [';', '|>']
delimiters = py_delimiters + bash_delimiters

Error = None
Success = 0


class ShellException(RuntimeError):
    pass


class BaseShell(Cmd):
    """Extend CMD with various capabilities. 

    Functionality:
    - pipes that can be used to combine shell commands and python functions
    - command names that start with symbols
    - error handling
    - confirmation mode to allow a user to accept or decline commands
    """
    intro = 'Welcome.  Type help or ? to list commands.\n' + shell_ready_signal + '\n'
    prompt = '$ '

    # TODO save stdout in a tmp file
    # TODO store/recover sessions using self.env

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.ignore_invalid_syntax = True

        self.completenames_options = []
        self.chars_allowed_for_char_method = []

        self.do_char_method = None

        self.infix_operators = {'=': self.set_env_variable}
        self.variable_prefix = '$'

        self.env = {}

    def completenames(self, text, *ignored):
        """Conditionally override CMD.completenames
        """
        if self.completenames_options:
            return [a for a in self.completenames_options if a.startswith(text)]

        return super().completenames(text, *ignored)

    def default(self, line):
        if line in self.chars_allowed_for_char_method and self.do_char_method:
            return self.do_char_method(line)

        else:
            print('line', line)

        if self.ignore_invalid_syntax:
            super().default(line)
        else:
            raise ShellException(f'Unknown syntax: {line}')

    def emptyline(self):
        # this supresses the default behaviour of repeating the previous command
        # TODO fixme
        pass

    def set_do_char_method(self, method: Callable[[str], Any], chars: List[str]):
        """Allow special chars to be used as commands. 
        E.g. transform `do_$` into `do_f $`
        """
        self.do_char_method = method
        self.chars_allowed_for_char_method = chars

    def set_env_variable(self, k, v):
        self.env[k] = v
        return k

    def postcmd(self, stop, _):
        """Display the shell_ready_signal to indicate termination to a parent process.
        """
        print_shell_ready_signal()
        return stop

    def onecmd(self, line: str) -> Union[Literal[0], Error]:
        """Parse and run `line`.
        Return 0 on success and None otherwise
        """

        try:
            line = self.onecmd_prehook(line)
            lines = self.parse_command(line)
            self.run_commands(lines)

        except CancelledError:
            pass

        return 0

    def onecmd_prehook(self, line):
        """Similar to cmd.precmd but executed before cmd.onecmd
        """
        if confirmation_mode:
            assert io_util.interactive
            log('Command:', line)
            if not io_util.confirm():
                raise CancelledError()

        return line

    ############################################################################
    # Pipes
    ############################################################################

    def parse_command(self, line: str) -> Iterable[List[str]]:
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
        return split_sequence(terms, delimiters, return_delimiters=True)

    def run_commands(self, lines: Iterable[List[str]], result=''):
        """Run each command in `lines`.
        The partial results are passed through to subsequent commands.
        """
        if not lines:
            return

        for line in lines:
            try:
                result = self.run_one_command(line, result)

            except subprocess.CalledProcessError as e:
                returncode, stderr = e.args
                log(f'Shell exited with {returncode}: {stderr}')

                raise ShellException(str(e))

        if result is not None:
            print(result)

    def run_one_command(self, command_and_args: List[str], result: str = '') -> str:
        if ';' in command_and_args:
            # print prev result & discard it

            if result is not None:
                print(result)

            result = ''

        elif result is None:
            raise ShellException('Last return value was absent')

        # assume there is at most 1 delimiter
        prefixes = list(split_prefixes(command_and_args, delimiters))
        use_sh = prefixes and prefixes[-1] in bash_delimiters

        f, *args = list(omit_prefixes(command_and_args, delimiters))
        args = list(self.expand_variables(args))
        cmd = ' '.join(chain.from_iterable(([f], args)))

        # TODO make this check quote-aware
        there_is_an_infix_operator = for_any(
            self.infix_operators, contains, args)

        if use_sh:
            return self.pipe_cmd_sh(cmd, result, prefixes[-1])

        if there_is_an_infix_operator:
            return self.infix_command(f, *args)

        return self.pipe_cmd_py(cmd, result)

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

    def infix_command(self, *args):
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

        raise NotImplementedError()

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
                if k in self.env:
                    yield self.env[k]
                    continue
                else:
                    raise ShellException('Variable `{v}` is not set')
            yield v
