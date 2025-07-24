from mash.shell2.ast.node import Node


class Nodes(Node):
    """A container that holds `Node` instances.  
    """

    def __init__(self, *nodes: Node):
        self.items = nodes

    def extend(self, other):
        self.items.extend(other.values)

    def __repr__(self):
        return f'[{type(self).__name__}] {repr(self.items)}'

    def __eq__(self, other):
        try:
            return self.items == other.values and type(self) == type(other)
        except AttributeError:
            return False
