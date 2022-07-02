import cmd
import os
import sys
from util import constant

debug = 0


def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))


class Shell(cmd.Cmd):
    intro = 'Welcome.  Type help or ? to list commands.\n'
    prompt = '$ '

    def do_shell(arg):
        """System call
        """
        os.system(arg)


def infer(k, data: dict):
    if k in data:
        return f'{k}: {data[k]}'
    return k


def infer_args(func) -> list:
    args = list(func.__code__.co_varnames)
    n_default_args = len(func.__defaults__) if func.__defaults__ else 0
    default_args = args[-n_default_args:]
    return args[:-n_default_args] + [f'[{a}]' for a in default_args]


def infer_synopsis(func) -> str:
    items = [func.__name__]
    if func.__code__.co_varnames:
        return ' '.join([func.__name__] + infer_args(func))
    return func.__name__


def infer_signature(func) -> list:
    def format(k):
        key = k
        if func.__defaults__ and k in func.__defaults__:
            key = f'[{k}]'

        if k in func.__annotations__:
            v = func.__annotations__[k].__name__
            return f'{key}: {v}'

        return key

    return [format(var) for var in func.__code__.co_varnames]


class Function:
    def __init__(self, func, synopsis=None, args=None, doc=None) -> None:
        # synopsis = func.__name__ + '-' + '[a] b c'
        if synopsis is None:
            synopsis = infer_synopsis(func)
        if args is None:
            args = infer_signature(func)
        if doc is None:
            if func.__doc__:
                doc = func.__doc__
            else:
                if args:
                    prefix = '\tParameters\n\t----------\n\t\t'
                    parameters = '\n\t\t'.join(args)
                    doc = prefix + parameters

        help = synopsis
        if doc:
            help += '\n\n' + doc

        self.func = func
        self.args = args
        self.help = help

    def __call__(self, args):
        # TODO verify min_args < n_args < max_args
        try:
            result = self.func(*args.split(' '))
        except TypeError as e:
            print('TypeError:', e)
            return

        print(result)


def shell(cmd: str):
    def func(*args):
        return os.system(''.join(cmd + args))
    func.__name__ = cmd
    return func


def constant(value):
    def K(*args):
        return value
    return K


def set_functions(shell: cmd.Cmd, functions: dict):
    for key, func in functions.items():
        if not isinstance(func, Function):
            func = Function(func)

        setattr(Shell, f'do_{key}', func)
        setattr(getattr(Shell, f'do_{key}'), '__doc__', func.help)

        if debug:
            print(func, '\n', func.args, '\n', func.help, '\n',)


if __name__ == '__main__':
    shell = Shell()
    shell.cmdloop()
