from mash.shell2.ast.nodes import Nodes
from mash.shell2.env import Environment


class Lines(Nodes):
    """
    E.g.

    .. code-block:: sh

        print 1; print 2
        print outer:
            print inner

    """

    def run(self, env: Environment):
        for line in self.items:
            line.run(env)

    def __repr__(self):
        if self.items is None:
            return self.f

        lines = '\n'.join(repr(t) for t in self.items)
        return f'[{type(self).__name__}] {lines}'

    @property
    def type(self):
        return 'lines'
