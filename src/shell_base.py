#!/usr/bin/python3
from cmd import Cmd
from copy import deepcopy
from typing import Any, Callable, Dict, List
import logging
import subprocess

import io_util
from io_util import log, shell_ready_signal, print_shell_ready_signal, has_output, read_file

confirmation_mode = False


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
    intro = 'Welcome.  Type help or ? to list commands.\n' + shell_ready_signal + '\n'
    prompt = '$ '
    exception = None
    ignore_invalid_syntax = True
    do_char_method = None
    chars_allowed_for_char_method = []
    completenames_options = []

    # TODO save stdout in a tmp file

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

    def onecmd(self, line):
        """Parse and run `line`.
        Return 0 on success and None otherwise
        """
        # force a custom precmd hook to be used outside of loop mode
        line = self.onecmd_prehook(line)

        self.last_command_has_failed = False

        if '|' in line:
            return self.onecmd_with_pipe(line)

        result = super().onecmd(line)
        if result is not None:
            print(result)
        return 0

    def onecmd_with_pipe(self, line):
        # TODO escape quotes
        # TODO properly handle delimiters in quotes
        if '|' in line:
            line, *lines = line.split('|')
        else:
            lines = []

        logging.info(f'Piped cmd = {line}')
        result = super().onecmd(line)

        if not result:
            self.last_command_has_failed = True

        if self.last_command_has_failed:
            log('Abort - No return value')
            return

        elif lines:
            try:
                result = self.run_cmd_sequence(lines, result)
            except subprocess.CalledProcessError:
                return

            if result is None:
                return

        print(result)
        return 0

    def run_cmd_sequence(self, lines: list, result: str):
        for line in lines:
            if line[0] == '>':
                result = self.pipe_cmd_py(line[1:], result)
            else:
                result = self.pipe_cmd_sh(line, result)

            if result is None:
                log('Abort - No return value in sequence')
                return

        return result

    def pipe_cmd_py(self, line: str, result: str):
        line = line.lstrip()

        # append arguments
        line = f'{line} {result}'

        return super().onecmd(line)

    def pipe_cmd_sh(self, line: str, result: str) -> str:
        line = line.lstrip()

        # pass last result to stdin
        line = f'echo {result} | {line}'

        logging.info(f'Cmd = {line}')

        try:
            result = subprocess.run(args=line,
                                    capture_output=True,
                                    check=True,
                                    shell=True)
        except subprocess.CalledProcessError as e:
            returncode, stderr = e.args
            log(f'Shell exited with {returncode}: {stderr}')
            raise

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
                return ''

        return line
