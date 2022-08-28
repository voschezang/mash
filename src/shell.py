#!/usr/bin/python3
from argparse import ArgumentParser
from copy import deepcopy
from types import TracebackType
from typing import Callable, Dict, List
import cmd
import logging
import os
import subprocess
import sys
import traceback
from doc_inference import generate_docs

import io_util
from io_util import ArgparseWrapper, bold, has_argument, log, shell_ready_signal, print_shell_ready_signal, has_output
import util

# this data is impacts by both the classes Function and Shell, hence it should be global
exception_hint = '(run `E` for details)'

# global cache: sys.last_value and sys.last_traceback don't store exceptions raised in cmd.Cmd
last_exception: Exception = None
last_traceback: TracebackType = None

confirmation_mode = False

description = 'If no arguments are given then an interactive subshell is started.'
epilog = f"""
--------------------------------------------------------------------------------
{bold('Default Commands')}
Run shell commands by prefixing them with `!`.
E.g.
    ./shell.py !echo abc; echo def # Bash

Run multiple Python commands by separating each command with colons or newlines.
E.g.
    ./shell.py 'print abc; print def \n print ghi'

{bold('Interopability')}
Interopability with Bash can be done with pipes:
    `|` for Bash
    `|>` for Python.

1. To stdin and stdout
E.g.
    echo abc | ./shell.py print
    ./shell.py print abc | echo

2. Within the dsl
E.g.
    ./shell.py print abc # Python
    ./shell.py 'print abc | echo'
    ./shell.py 'print abc |> print'
"""


class ShellException(RuntimeError):
    pass


class Shell(cmd.Cmd):
    intro = 'Welcome.  Type help or ? to list commands.\n' + shell_ready_signal + '\n'
    prompt = '$ '
    exception = None
    ignore_invalid_syntax = True
    do_char_method = None
    chars_allowed_for_char_method = []

    # TODO save stdout in a tmp file

    def set_do_char_method(self, method: Callable, chars: List[str]):
        """Allow special chars to be used as commands. 
        E.g. transform `do_$` into `do_f $`
        """
        self.do_char_method = method
        self.chars_allowed_for_char_method = chars

    def do_exit(self, args):
        """exit [code]

        Wrapper for sys.exit(code) with default code: 0
        """
        if not args:
            args = 0
        sys.exit(int(args))

    def do_shell(self, args):
        """System call
        """
        logging.info(f'Cmd = !{args}')
        # TODO add option to forward environment variables
        os.system(args)

    def do_print(self, args):
        """Mimic Python's print function
        """
        logging.debug(f'Cmd = print {args}')
        return args

    def do_echo(self, args):
        """Mimic Bash's print function
        """
        logging.debug(f'Cmd = echo {args}')
        return args

    def do_export(self, args):
        # TODO set environment variables
        raise ShellException('NotImplemented')

    def do_E(self, args):
        """Show the last exception
        """
        traceback.print_exception(
            type(last_exception), last_exception, last_traceback)

    def emptyline(self):
        # this supresses the default behaviour of repeating the previous command
        # TODO fixme
        pass

    def default(self, line):
        if line in self.chars_allowed_for_char_method and self.do_char_method:
            return self.do_char_method(line)

        self.last_command_has_failed = True

        if self.ignore_invalid_syntax:
            super().default(line)
        else:
            raise ShellException(f'Unknown syntax: {line}')

    # TODO temporarily override completenames, based on the current state
    # def completenames(self, text, *ignored):
    #     self.state_specific_complete_names = ['abc', 'dev']
    #     if self.state_specific_complete_names:
    #         return [a for a in self.state_specific_complete_names if a.startswith(text)]
    #     return super().completenames(text, *ignored)

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

    def postcmd(self, stop, _):
        print_shell_ready_signal()
        return stop

    @staticmethod
    def all_commands():
        for cmd in vars(Shell):
            if cmd.startswith('do_') and util.has_method(Shell, cmd):
                yield cmd.lstrip('do_')

    def last_method(self):
        """Find the method corresponding to the last command run in `shell`.
        It has the form: do_{cmd}

        Return a the last method if it exists and None otherwise.
        """
        # TODO integrate this into Shell and store the last succesful cmd

        if not self.lastcmd:
            return

        cmd = self.lastcmd.split(' ')[0]
        return Shell.get_method(cmd)

    @staticmethod
    def get_method(method_suffix: str):
        method_name = f'do_{method_suffix}'
        if not util.has_method(Shell, method_name):
            return

        method = getattr(Shell, method_name)

        if isinstance(method, Function):
            # TOOD use method.func.synopsis
            return method.func

        return method


class Function:
    def __init__(self, func, func_name=None, synopsis: str = None, args: Dict[str, str] = None, doc: str = None) -> None:
        help = generate_docs(func, synopsis, args, doc)

        self.help = help
        try:
            self.func = deepcopy(func)
        except TypeError as e:
            logging.warning('Cannot deepcopy func:' + e.args[0])
            self.func = func

        if func_name is not None:
            util.rename(self.func, func_name)

    def __call__(self, args: str = ''):
        args = args.split(' ')
        args = [arg for arg in args if arg != '']

        try:
            return self.func(*args)
        except Exception:
            self.handle_exception()
            return

    def handle_exception(self):
        global last_exception, last_traceback

        etype, last_exception, last_traceback = sys.exc_info()

        log(etype.__name__, exception_hint)
        if str(last_exception):
            log('\t', last_exception)


def set_functions(functions: Dict[str, Function]):
    """Extend `Shell` with a set of functions
    Note that this modifies the class Shell directly, rather than an instance.
    """
    for key, func in functions.items():
        if not isinstance(func, Function):
            func = Function(func)

        setattr(Shell, f'do_{key}', func)
        setattr(getattr(Shell, f'do_{key}'), '__doc__', func.help)


def set_completions(functions: Dict[str, Callable]):
    for key, func in functions.items():
        setattr(Shell, f'complete_{key}', func)


def sh_to_py(cmd: str):
    """A wrapper for shell commands
    """
    def func(*args):
        args = ' '.join(args)
        return os.system(''.join(cmd + ' ' + args))

    func.__name__ = cmd
    return func


def add_cli_args(parser: ArgumentParser):
    if not has_argument(parser, 'cmd'):
        parser.add_argument('cmd', nargs='*',
                            help='A comma- or newline-separated list of commands')
    if not has_argument(parser, 'safe'):
        parser.add_argument('-s', '--safe', action='store_true',
                            help='Safe-mode. Ask for confirmation before executing commands.')


def set_cli_args():
    global confirmation_mode

    with ArgparseWrapper() as parser:
        add_cli_args(parser)

    if io_util.parse_args.safe:
        confirmation_mode = True
        io_util.interactive = True


def has_input():
    # ensure argparse has been called
    with ArgparseWrapper():
        pass

    return io_util.parse_args.cmd != []


def run_command(command='', shell: Shell = None, delimiters='\n;'):
    if shell is None:
        shell = Shell()

    for line in util.split(command, delimiters):
        if not line:
            continue

        result = shell.onecmd(line)

        if result != 0:
            raise ShellException(f'Abort - No return value (2): {result}')


def read_stdin():
    if not has_output(sys.stdin):
        return ''

    try:
        yield from sys.__stdin__

    except KeyboardInterrupt as e:
        print()
        logging.info(e)
        exit(130)


def run(shell=None):
    set_cli_args()

    if shell is None:
        shell = Shell()

    logging.info(f'args = {io_util.parse_args}')
    commands = ' '.join(io_util.parse_args.cmd + list(read_stdin()))

    if commands:
        # compile mode
        run_command(commands, shell)
    else:
        # run interactively
        util.interactive = True
        shell.cmdloop()


def main(functions: Dict[str, Function] = {}):
    if functions:
        set_functions(functions)

    shell = Shell()
    run(shell)


if __name__ == '__main__':
    run()
