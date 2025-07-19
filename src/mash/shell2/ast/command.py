
from mash.shell.errors import ShellError
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
        f = self.f.run(env)
        args = [arg.run(env) for arg in self.args]

        if f in Builtins:
            return Builtins[f](*args)

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
