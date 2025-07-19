
from typing import List
from mash.functional_shell.ast.node import Node
from mash.functional_shell.ast.term import Term
from mash.functional_shell.env import Environment


class Command(Node):
    """A command is a function with input arguments.

    .. code-block:: sh

        f (args)
    """

    def __init__(self, f: str, args: List[Term] = None):
        self.f = f
        self.args = args

    def run(self, env: Environment):
        raise NotImplementedError()

    @property
    def data(self):
        if self.args is None:
            return self.f
        return self.f + ' ' + ' '.join(str(t) for t in self.args)
