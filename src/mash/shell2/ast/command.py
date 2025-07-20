
from typing import Callable, List, Tuple, Union
from mash.shell.errors import ShellError, ShellTypeError
from mash.shell2.ast.node import Node
from mash.shell2.ast.term import Term
from mash.shell2.builtins import Builtins
from mash.shell2.env import Environment
from mash.util import infer_variadic_args


class Command(Node):
    """A command is a function with input arguments.

    .. code-block:: sh

        f (args)
    """

    def __init__(self, f: str, *args: Term):
        self.f = f
        self.args = args

    def run(self, env: Environment):
        # handle f, args
        f = str(self.f.run(env))
        args = [arg.run(env) for arg in self.args]

        # handle f(args)
        if f in Builtins:
            func = Builtins[f]
            verify_function_args(func, args)
            return func(*args)

        # if self.f in env['functions']:
        #     return env['functions'][self.f](args)

        raise ShellError(f'Command not found: {self.f}')

    def __repr__(self):
        if self.args is None:
            return self.f

        args = ' '.join(repr(t) for t in self.args)
        return f'[{type(self).__name__}] {self.f} {args}'

    def __eq__(self, other):
        try:
            return self.f == other.f \
                and self.args == other.args \
                and type(self) == type(other)

        except AttributeError:
            return False


def verify_function_args(func: Callable, args: List[Node]):
    """Verify function arguments.

    Parameters
    ----------
    func: Callable
        A function with annotated positional and/or variadic arguments.
    args: List[Node]
        The arguments to the function.
    """
    pos_args, var_arg = infer_variadic_args(func)
    verify_arg_count(args, pos_args, var_arg)
    verify_arg_types(args, func, pos_args, var_arg)


def verify_arg_count(args: list, pos_args: list, var_arg: Union[str, None]):
    """Verify the number of arguments in `args`

    - Verify that `args` contains at least as many arguments as `pos_args`.
    - Verify that `args` does not contain too many arguments.
    """
    if var_arg:
        if len(args) < len(pos_args):
            raise ShellTypeError(
                f'Not enough arguments. Expected at least {len(pos_args)} but got {len(args)}')

    elif len(args) != len(pos_args):
        raise ShellTypeError(
            f'Not enough arguments. Expected {len(pos_args)} but got {len(args)}')


def verify_arg_types(args: List[Node], func: Callable, pos_args: list, var_arg: list):
    """Verify the types of arguments in `args`.

    Parameters
    ----------
    args: List[Node]
        The arguments to verify
    func: Callable
        A function with annotated positional and/or variadic arguments.
    pos_args: List[str]
        The names of the positional arguments.
    var_arg: Union[str, None]
        The name of the variadic argument.
    """
    pos_arg_types = []
    for k in pos_args:
        pos_arg_types.append(infer_arg_type(func, k))

    # verify positional arguments
    for expected_type, arg in zip(pos_arg_types, args):
        verify_arg(arg, expected_type)

    # verify variadic arguments
    if var_arg:
        var_arg_type = infer_arg_type(func, var_arg)
        for arg in args[len(pos_args):]:
            verify_arg(arg, var_arg_type)


def verify_arg(arg: Node, expected_type: type):
    if not isinstance(arg, expected_type):
        raise ShellTypeError(
            f'Invalid type. Expected {expected_type.__name__} but got {type(arg)}')


def infer_arg_type(func, k):
    try:
        return func.__annotations__[k]
    except KeyError:
        raise ShellError(
            f'Type not defined for argument: {k} of command: {func}')
