import argparse
import cmd
import traceback
import os
import sys
from typing import Dict, List
from types import TracebackType
import util
from util import generate_docs, add_and_parse_args, add_default_args

# this data is impacts by both the classes Function and Shell, hence it should be global
exception_hint = '(run `E` for details)'

# global cache: sys.last_value and sys.last_traceback don't store exceptions raised in cmd.Cmd
last_exception: Exception = None
last_traceback: TracebackType = None


class Shell(cmd.Cmd):
    intro = 'Welcome.  Type help or ? to list commands.\n'
    prompt = '$ '
    exception = None

    def do_shell(self, args):
        """System call
        """
        os.system(args)

    def do_E(self, args):
        """Show the last exception
        """
        traceback.print_exception(
            type(last_exception), last_exception, last_traceback)


class Function:
    def __init__(self, func, synopsis: str = None, args: List[str] = None, doc: str = None) -> None:
        help = generate_docs(func, synopsis, args, doc)

        self.func = func
        # self.args = args
        self.help = help

    def __call__(self, args: str = ''):
        args = args.split(' ')

        try:
            result = self.func(*args)
        except Exception:
            self.handle_exception()
            return

        print(result)

    def handle_exception(self):
        global last_exception, last_traceback

        etype, last_exception, last_traceback = sys.exc_info()

        print(etype.__name__, exception_hint)
        print('\t', last_exception)


def set_functions(functions: Dict[str, Function]):
    for key, func in functions.items():
        if not isinstance(func, Function):
            func = Function(func)

        setattr(Shell, f'do_{key}', func)
        setattr(getattr(Shell, f'do_{key}'), '__doc__', func.help)


def shell(cmd: str):
    def func(*args):
        return os.system(''.join(cmd + args))
    func.__name__ = cmd
    return func


def set_cli_args():
    add_default_args()
    util.parser.add_argument(
        'cmd', nargs='*', help='A comma separated list of commands')
    util.parse_args = util.parser.parse_args()


def run_commands(shell: Shell, commands: list, delimiter=','):
    commands = ' '.join(commands) + delimiter
    for line in commands.split(delimiter):
        if line:
            shell.onecmd(line)


def run(shell=None):
    set_cli_args()

    if shell is None:
        shell = Shell()

    if util.parse_args.cmd:
        # compile mode
        run_commands(shell, util.parse_args.cmd)
    else:
        # run interactively
        shell.cmdloop()


if __name__ == '__main__':
    run()
