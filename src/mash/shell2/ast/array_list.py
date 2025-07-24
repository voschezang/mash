

from mash.shell2.ast.nodes import Nodes
from mash.shell2.env import Environment


class ArrayList(Nodes):
    def __init__(self, child_type, nodes: Nodes):
        self.child_type = child_type
        self.items = nodes

    def run(self, env: Environment):
        # expand variables in children
        items = [item.run(env) for item in self.items]
        return ArrayList(self.child_type, items)

    @property
    def type(self):
        return f'list[{self.child_type}]'
