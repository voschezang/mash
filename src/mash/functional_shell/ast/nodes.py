from mash.functional_shell.ast.node import Node


class Nodes:
    """A container that holds `Node` instances.  
    """

    def __init__(self, *values: Node):
        self.values = values

    def insert(self, value: Node):
        self.values = (value,) + self.values

    def __str__(self):
        return ' '.join(str(v) for v in self.values)

    def __repr__(self):
        return f'{type(self).__name__}( {repr(str(self))} )'

    def __eq__(self, other):
        try:
            return self.values == other.values and type(self) == type(other)
        except AttributeError:
            return False
