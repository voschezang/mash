from mash.shell2.ast.nodes import Nodes
from mash.shell2.env import Environment


# class Line(Node):
#     def __init__(self, value: Node):
#         self.value = value

#     def run(self, env: Environment):
#         #     for line in self.values:
#         #         line.run(env)
#         raise NotImplementedError()


class Lines(Nodes):
    """
    E.g.

    .. code-block:: sh

        print 1; print 2
        print outer:
            print inner

    """

    def run(self, env: Environment):
        for line in self.values:
            line.run(env)

    def __repr__(self):
        if self.values is None:
            return self.f

        lines = '\n'.join(repr(t) for t in self.values)
        return f'[{type(self).__name__}] {lines}'
