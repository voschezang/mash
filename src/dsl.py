#!/usr/bin/python3
from contextlib import redirect_stdout
import subprocess
from copy import deepcopy
from io import StringIO
from types import TracebackType
from typing import Dict, List
import cmd
import os
import sys
import traceback

import util
from util import generate_docs

# this data is impacts by both the classes Function and Shell, hence it should be global
exception_hint = '(run `E` for details)'

# global cache: sys.last_value and sys.last_traceback don't store exceptions raised in cmd.Cmd
last_exception: Exception = None
last_traceback: TracebackType = None

confirmation_mode = False


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
        os.system(args)

    def do_echo(self, args):
        return args

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
        if '|' in line:
            line, *lines = line.split('|')
        else:
            lines = []

        result = self.onecmd_supress_output(line)
        if not result:
            self.last_command_has_failed = True

        if self.last_command_has_failed:
            print('Abort - No return value (3)')
            return

        # TODO pipe shell output back to Python after |>

        elif lines:
            for line in lines:
                line = f'{line} {result}'
                if line[0] == '>':
                    # use Python
                    line = line[1:]
                    # result = super().onecmd(line)
                    result = self.onecmd_supress_output(line)
                else:
                    # use shell
                    result = subprocess.run(
                        args=line, capture_output=True, shell=True)
                    if result.returncode != 0:
                        print(
                            f'Shell exited with {result.returncode}: {result.stderr.decode()}')
                        return

                    # self.stderr.append(f'stderr: {result.stderr.decode()}')

                    # TODO don't ignore stderr
                    result = result.stdout.decode()

                if result is None:
                    print('Abort - No return value')
                    return

        print(result)
        return 0

    def onecmd_supress_output(self, line):

        # TODO rm this block
        if 0:
            # modify self.stdout
            original_stdout = self.stdout
            self.stdout = StringIO()
            r = super().onecmd(line)
            result = self.stdout.getvalue()
            self.stdout = original_stdout
            return result

        # TODO rm this block
        if 0:
            out = StringIO()
            with redirect_stdout(out):
                r = super().onecmd(line)
                result = out.getvalue()[:-1]

            return result

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

    util.add_default_args()
    util.parser.add_argument(
        'cmd', nargs='*', help='A comma separated list of commands')
    util.parser.add_argument(
        '-s', '--safe', action='store_true', help='Safe-mode. Ask for confirmation before executing commands')
    util.parse_args = util.parser.parse_args()

    if util.parse_args.safe:
        confirmation_mode = True
        util.interactive = True


def run_commands(commands=[], shell: Shell = None, delimiter=','):
    commands = ' '.join(commands)

    run_command(commands, shell, delimiter)


def run_command(commands=[], shell: Shell = None, delimiter=','):
    if shell is None:
        shell = Shell()

    for line in commands.split(delimiter):
        if line:
            result = shell.onecmd(line)
            if result != 0:
                print('Abort - No return value (2)', result)
                return


def run(shell=None):
    set_cli_args()

    if shell is None:
        shell = Shell()

    if util.parse_args.cmd:
        # compile mode
        run_commands(util.parse_args.cmd, shell)
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
