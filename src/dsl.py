#!/usr/bin/python3
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import shlex
from types import TracebackType
from typing import Dict, List
import cmd
import logging
import os
import subprocess
import sys
import traceback

import util
from util import generate_docs, bold

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
    ./dsl.py !echo abc; echo def # Bash

Run multiple Python commands by separating each command with colons or newlines.
E.g.
    ./dsl.py 'print abc; print def \n print ghi'

{bold('Interopability')}
Interopability with Bash can be done with pipes: 
    `|` for Bash 
    `|>` for Python.

1. To stdin and stdout
E.g.
    echo abc | ./dsl.py print
    ./dsl.py print abc | echo

2. Within the dsl
E.g.
    ./dsl.py print abc # Python
    ./dsl.py 'print abc | echo'
    ./dsl.py 'print abc |> print'
"""


class Shell(cmd.Cmd):
    intro = 'Welcome.  Type help or ? to list commands.\n'
    prompt = '$ '
    exception = None
    shell_result = ''
    suppress_shell_output = False

    # TODO save stdout in a tmp file

    def do_shell(self, args):
        """System call
        """
        logging.info(f'Cmd = !{args}')
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
        raise NotImplementedError()

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
        self.last_command_has_failed = True
        super().default(line)

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
        result = self.onecmd_supress_output(line)

        if not result:
            self.last_command_has_failed = True

        if self.last_command_has_failed:
            print('Abort - No return value (3)')
            return

        # TODO pipe shell output back to Python after |>

        elif lines:
            for line in lines:
                if line[0] == '>':
                    # use Python

                    # rm first '>'
                    line = line[1:]

                    # append arguments
                    line = f'{line} {result}'

                    # result = super().onecmd(line)
                    result = self.onecmd_supress_output(line)

                else:
                    # use shell

                    # pass last result to stdin
                    line = f'echo {result} | {line}'

                    logging.info(f'Cmd = {line}')

                    result = subprocess.run(
                        args=line, capture_output=True, shell=True)

                    if result.returncode != 0:
                        print(
                            f'Shell exited with {result.returncode}: {result.stderr.decode()}')
                        return

                    # self.stderr.append(f'stderr: {result.stderr.decode()}')

                    # TODO don't ignore stderr
                    result = result.stdout.decode().rstrip('\n')

                if result is None:
                    print('Abort - No return value')
                    return

        print(result)
        return 0

    def onecmd_supress_output(self, line):
        # TOOD strip trailing '\n'
        return super().onecmd(line)

    def onecmd_prehook(self, line):
        """Similar to cmd.precmd but executed before cmd.onecmd
        """
        if confirmation_mode:
            assert util.interactive
            print('Command:', line)
            if not util.confirm():
                return ''

        return line


class Function:
    def __init__(self, func, func_name=None, synopsis: str = None, args: Dict[str, str] = None, doc: str = None) -> None:
        help = generate_docs(func, synopsis, args, doc)

        self.help = help
        self.func = deepcopy(func)

        if func_name is not None:
            util.rename(self.func, func_name)

    def __call__(self, args: str = ''):
        args = args.split(' ')

        try:
            result = self.func(*args)
        except Exception:
            self.handle_exception()
            return

        return result

    def handle_exception(self):
        global last_exception, last_traceback

        etype, last_exception, last_traceback = sys.exc_info()

        print(etype.__name__, exception_hint)
        print('\t', last_exception)


def set_functions(functions: Dict[str, Function]):
    """Extend `Shell` with a set of functions
    """
    for key, func in functions.items():
        if not isinstance(func, Function):
            func = Function(func)

        setattr(Shell, f'do_{key}', func)
        setattr(getattr(Shell, f'do_{key}'), '__doc__', func.help)


def shell(cmd: str):
    def func(*args):
        args = ' '.join(args)
        return os.system(''.join(cmd + ' ' + args))
    func.__name__ = cmd
    return func


def set_cli_args():
    global confirmation_mode

    util.set_parser(description=description, epilog=epilog)

    util.parser.add_argument(
        'cmd', nargs='*', help='A comma- or newline-separated list of commands')
    util.parser.add_argument(
        '-s', '--safe', action='store_true', help='Safe-mode. Ask for confirmation before executing commands')
    util.add_and_parse_args()

    if util.parse_args.safe:
        confirmation_mode = True
        util.interactive = True


def run_command(command='', shell: Shell = None, delimiters='\n;'):
    if shell is None:
        shell = Shell()

    for line in util.split(command, delimiters):
        if not line:
            continue

        result = shell.onecmd(line)

        if result != 0:
            raise RuntimeError(f'Abort - No return value (2): {result}')


def read_stdin():
    if sys.stdin.isatty():
        return ''
    yield from sys.__stdin__


def run(shell=None):
    set_cli_args()

    if shell is None:
        shell = Shell()

    # print('parse', util.parse_args.cmd, sys.__stdin__, sys.stdin.isatty())

    logging.info(f'args = {util.parse_args}')
    commands = ' '.join(util.parse_args.cmd + list(read_stdin()))
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
