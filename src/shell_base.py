#!/usr/bin/python3
from asyncio import CancelledError
from cmd import Cmd
from codecs import ignore_errors
from copy import deepcopy
from itertools import chain
from typing import Any, Callable, Dict, List, Literal, Union
import logging
import shlex
import subprocess

import io_util
from io_util import log, shell_ready_signal, print_shell_ready_signal
from util import omit_prefixes, split_sequence, split_tips

confirmation_mode = False
delimiters = ['|', '|>', ';']

Error = None
Success = 0


class ShellException(RuntimeError):
    pass


class BaseShell(Cmd):
    """Extend CMD with various capabilities. 
    This is meant as a base for the child-class Shell. 

    Functionality:
    - pipes that can be used to combine shell commands and python functions
    - command names that start with symbols
    - error handling
    - confirmation mode to allow a user to accept or decline commands
    """
    # exception = None
    intro = 'Welcome.  Type help or ? to list commands.\n' + shell_ready_signal + '\n'
    prompt = '$ '

    # TODO save stdout in a tmp file

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.last_command_has_failed = False
        self.ignore_invalid_syntax = True

        self.completenames_options = []
        self.chars_allowed_for_char_method = []

        self.do_char_method = None

    def completenames(self, text, *ignored):
        """Conditionally override CMD.completenames
        """
        if self.completenames_options:
            return [a for a in self.completenames_options if a.startswith(text)]

        return super().completenames(text, *ignored)

    def default(self, line):
        if line in self.chars_allowed_for_char_method and self.do_char_method:
            return self.do_char_method(line)

        self.last_command_has_failed = True

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

    def postcmd(self, stop, _):
        """Display the shell_ready_signal to indicate termination to a parent process.
        """
        print_shell_ready_signal()
        return stop

    ############################################################################
    # Pipes
    ############################################################################

    def onecmd(self, line: str) -> Union[Literal[0], Error]:
        """Parse and run `line`.
        Return 0 on success and None otherwise
        """
        # TODO refactor this function

        self.last_command_has_failed = False

        # force a custom precmd hook to be used outside of loop mode
        try:
            line = self.onecmd_prehook(line)
        except CancelledError:
            return Success

        try:
            # split lines and handle quotes
            # e.g. convert 'echo "echo 1"' to ['echo', 'echo 1']
            terms = shlex.split(line, comments=True)
        except ValueError as e:
            if self.ignore_invalid_syntax:
                return Success
            raise ShellException(
                f'Invalid syntax: {e} for {str(line)[:10]} ..')

        if not terms:
            # return silently
            return Success

        ################################################################################
        # handle lines that end with `;`
        # e.g. 'echo 1; echo 2;'
        # TODO this doesn't preserve ; when it was originally enclosed in quotes
        # terms = chain.from_iterable([split_tips(term.strip(), ';') for term in terms])
        ################################################################################

        # group terms based on delimiters
        lines = split_sequence(terms, delimiters, return_delimiters=True)

        lines = list(lines)

        try:
            line, *lines = lines
        except ValueError:
            if self.ignore_invalid_syntax:
                return Success
            raise ShellException(f'Invalid syntax for {str(lines)[:10]} ..')

        line = omit_prefixes(line, delimiters)
        line = ' '.join(line)
        result = super().onecmd(line)

        if not lines:
            # allow absent return values
            if result is not None:
                print(result)

            return Success

        elif result is None:
            self.last_command_has_failed = True
            log('Abort - No return value')
            return Error

        try:
            result = self.run_cmd_sequence(lines, result)
        except subprocess.CalledProcessError as e:
            returncode, stderr = e.args
            log(f'Shell exited with {returncode}: {stderr}')

            if self.ignore_invalid_syntax:
                return Success
            raise ShellException(str(e))

        if result is None:
            return Error

        print(result)
        return Success

    def onecmd_with_pipe(self, lines: List[str]):
        pass

    def run_cmd_sequence(self, lines: list, result: str):
        for line in lines:
            # assume there is at most 1 delimiter in `line`
            # use_sh = '|' in line and '|>' not in line
            use_py = '|>' in line or ';' in line
            # use_no_shell = ';' in line

            if ';' in line:
                # print prev result & discard it

                if result is not None:
                    print(result)

                result = ''

            line = omit_prefixes(line, delimiters)
            line = ' '.join(line).lstrip()

            if use_py:
                result = self.pipe_cmd_py(line, result)
            else:
                result = self.pipe_cmd_sh(line, result)

            if result is None:
                log('Abort - No return value in sequence')
                return

        return result

    def pipe_cmd_py(self, line: str, result: str):
        # append arguments
        line = f'{line} {result}'

        return super().onecmd(line)

    def pipe_cmd_sh(self, line: str, result: str) -> str:
        """
        May raise subprocess.CalledProcessError
        """
        # pass last result to stdin
        line = f'echo {result} | {line}'

        logging.info(f'Cmd = {line}')

        result = subprocess.run(args=line,
                                capture_output=True,
                                check=True,
                                shell=True)

        stdout = result.stdout.decode().rstrip('\n')
        stderr = result.stdout.decode().rstrip('\n')

        log(stderr)
        return stdout

    def onecmd_prehook(self, line):
        """Similar to cmd.precmd but executed before cmd.onecmd
        """
        if confirmation_mode:
            assert io_util.interactive
            log('Command:', line)
            if not io_util.confirm():
                raise CancelledError()

        return line
