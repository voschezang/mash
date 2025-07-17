from mash.functional_shell.ast.nodes import Nodes
from mash.functional_shell.env import Environment


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

    def __str__(self):
        return '\n'.join(str(v) for v in self.values)
