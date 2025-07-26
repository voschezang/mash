from mash.shell.errors import ShellTypeError
from mash.shell2.ast.node import Node


class Nodes(Node):
    """A container that holds `Node` instances.  
    """

    def __init__(self, *nodes: Node):
        self.items = nodes

    def extend(self, other):
        self.items.extend(other.values)

    def __repr__(self) -> str:
        return f'[{type(self).__name__}] {repr(self.items)}'

    def __eq__(self, other: Node) -> bool:
        """Compare types and child nodes.
        """
        if isinstance(other, list):
            raise ShellTypeError(
                'Faulty comparison between Python and Mash types.')

        try:
            return self.items == other.items and self.type == other.type
        except AttributeError:
            return False
