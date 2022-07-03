from types import TracebackType
from typing import Dict, List
import cmd
import os
import sys
import traceback
import util
from util import generate_docs, add_default_args

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

    # TODO save stdout in a tmp file

    def do_shell(self, args):
        """System call
        """
        os.system(args)

    def do_E(self, args):
        """Show the last exception
        """
        traceback.print_exception(
            type(last_exception), last_exception, last_traceback)

    def emptyline(self, line):
        # supresses the default behaviour of repeating the previous command
        pass

    def onecmd(self, line):
        # force precmd hook to be used outside of loop mode
        line = self.onecmd_prehook(line)
        super().onecmd(line)

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
    # def __init__(self, func, synopsis: str = None, args: List[str] = None, doc: str = None) -> None:
    def __init__(self, func, synopsis: str = None, args: Dict[str, str] = None, doc: str = None) -> None:
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
        args = ' '.join(args)
        return os.system(''.join(cmd + ' ' + args))
    func.__name__ = cmd
    return func


def set_cli_args():
    global confirmation_mode

    add_default_args()
    util.parser.add_argument(
        'cmd', nargs='*', help='A comma separated list of commands')
    util.parser.add_argument(
        '-s', '--safe', action='store_true', help='Safe-mode. Ask for confirmation before executing commands')
    util.parse_args = util.parser.parse_args()

    if util.parse_args.safe:
        confirmation_mode = True
        util.interactive = True


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
        util.interactive = True
        shell.cmdloop()


def main(functions: Dict[str, Function] = {}):
    shell = Shell()
    if functions:
        set_functions(functions)
    run(shell)


if __name__ == '__main__':
    run()
