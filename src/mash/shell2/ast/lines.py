from __future__ import annotations

from mash.shell2.ast.node import Node
from mash.shell2.env import Environment


class Lines(Node):
    """
    E.g.

    .. code-block:: sh

        print 1; print 2
        print outer:
            print inner

    """

    def __init__(self, *nodes: Node):
        self.items = list(nodes)

    def run(self, env: Environment) -> Lines:
        for line in self.items:
            line.run(env)

        return self

    def __repr__(self):
        if self.items is None:
            return f'({type(self).__name__})'

        lines = '\n'.join(repr(t) for t in self.items)
        return f'({type(self).__name__}) {lines}'

    @property
    def type(self):
        return 'lines'
