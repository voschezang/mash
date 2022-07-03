import cmd
import traceback
import os
import sys
from typing import Dict, List
from types import TracebackType
from util import generate_docs

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


def set_functions(shell: cmd.Cmd, functions: Dict[str, Function]):
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


if __name__ == '__main__':
    shell = Shell()
    shell.cmdloop()
