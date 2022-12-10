#!/usr/bin/python3
if __name__ == '__main__':
    import _extend_path

import sys
import rich

from mash.shell.function import ShellFunction as Function
from mash.shell.shell import Shell, has_input, set_cli_args, sh_to_py, main
from mash.io_util import has_output
from mash import cli


def f(x: int): return x
def g(x: int, y=1): return x + y
def h(x: int, y: float, z): return x + y * z


def example(a: int, b, c: float = 3.):
    """An example of a function with a docstring

    Parameters
    ----------
        a: positive number
        b: object
    """
    return a


def inspect(func_name):
    """Inspect a function
    based on rich.inspect
    """
    func = Shell.get_method(func_name)
    if func is None:
        return

    rich.inspect(func)


functions = {
    'a_long_function': f,
    'another_function': f,
    'f': f,
    'g': g,
    'h': h,
    'example': example,
    'inspect': inspect,
    'ls': Function(sh_to_py('ls'), args={'-latr': 'flags', '[file]': ''}),
    'cat': Function(sh_to_py('cat'), args={'file': ''}),
    'vi': Function(sh_to_py('vi'), args={'[file]': ''})}

if __name__ == '__main__':
    # setting cli args is a requirement for shell.has_input
    set_cli_args()

    if has_output(sys.stdin) or has_input():
        main(functions=functions)
    else:
        # use_shell_with_history:
        cli.main(functions=functions)
