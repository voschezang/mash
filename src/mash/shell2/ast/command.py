
import inspect
from typing import Callable, List, Tuple, Union
from mash.shell.errors import ShellError, ShellTypeError
from mash.shell2.ast.node import Node
from mash.shell2.ast.term import Term
from mash.shell2.builtins import Builtins
from mash.shell2.env import Environment


class Command(Node):
    """A command is a function with input arguments.

    .. code-block:: sh

        f (args)
    """

    def __init__(self, f: str, *args: Term):
        self.f = f
        self.args = args

    def run(self, env: Environment):
        f = str(self.f.run(env))
        args = [arg.run(env) for arg in self.args]

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
    pos_args, var_arg = infer_args(func)

    # list expected types of function arguments
    pos_arg_types = []
    for k in pos_args:
        pos_arg_types.append(infer_arg_type(func, k))

    if var_arg is not None and len(args) > len(pos_args):
        var_arg_type = infer_arg_type(func, var_arg)

    # verify number of arguments
    if var_arg is not None:
        if len(args) < len(pos_args):
            raise ShellTypeError(
                f'Not enough arguments. Expected at least {len(pos_args)} but got {len(args)}')

    elif len(args) != len(pos_args):
        raise ShellTypeError(
            f'Not enough arguments. Expected {len(pos_args)} but got {len(args)}')

    # verify type
    for expected_type in pos_arg_types:
        k = args.pop(0)
        if not isinstance(k, expected_type):
            raise ShellTypeError(
                f'Invalid type. Expected {expected_type.__name__} but got {type(k)}')

    # verify remaining variadic args
    for k in args:
        k = args.pop(0)
        if not isinstance(k, var_arg_type):
            raise ShellTypeError(
                f'Invalid type. Expected {var_arg_type.__name__} but got {type(k)}')


def infer_arg_type(func, k):
    try:
        return func.__annotations__[k]
    except KeyError:
        raise ShellError(
            f'Type not defined for argument: {k} of command: {func}')


def infer_args(func: Callable) -> Tuple[list, Union[str, None]]:
    sig = inspect.signature(func)
    pos_args = []
    var_args = []
    for arg, param in sig.parameters.items():
        if param.kind == param.POSITIONAL_OR_KEYWORD:
            pos_args.append(arg)
        elif param.kind == param.VAR_POSITIONAL:
            var_args.append(arg)
        else:
            raise NotImplementedError(f'{arg} {param}')

    if var_args:
        assert len(var_args) == 1
        return pos_args, var_args[0]

    return pos_args, None
