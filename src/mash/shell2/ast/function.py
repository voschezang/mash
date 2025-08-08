from typing import List

from mash.shell.errors import ShellError
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.node import Data, Node
from mash.shell2.ast.variable import Variable
from mash.shell2.env import Environment


class Function(Data):
    def __init__(self, name: str, args: List[Variable], body: Lines):
        self.name = name
        self.args = args
        self.body = body

    def run(self, env: Environment):
        env[self.name] = self
        return self

    @property
    def type(self) -> str:
        return 'function'

    def __eq__(self, other):
        return self is other

    def __call__(self, env: Environment, *args: Node):
        """Apply the function to argument and return the result.
        """
        # copy env to prevent leaking variables
        env = env.copy()

        # expose function arguments to the environment
        if len(self.args) != len(args):
            raise ShellError(
                f'Not enough arguments for function {self}. Expected {len(self.args)} but got {len(args)}')

        for i, k in enumerate(self.args):
            try:
                env[k.value] = args[i]
            except IndexError:
                raise ShellError(f'Not enough arguments for function {self}')

        return self.body.run(env)

    def __repr__(self) -> str:
        args = ', '.join(repr(arg) for arg in self.args)
        return f'{self.name} ({args})'
