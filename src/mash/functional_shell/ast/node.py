from collections import UserString
from typing import List

from mash.functional_shell.env import Environment


class Node(UserString):
    """A node (edge) of an abstract syntax tree (AST).
    """

    # def __init__(self, data: str):
    #     # store value transparently
    #     self.data = data

    def run(self, env: Environment):
        raise NotImplementedError()


class Nodes:
    """A container node that holds a list of Node instances.  
    """

    def __init__(self, *values: Node):
        self.values = values

    def insert(self, values: List[Node]):
        self.values = [values] + self.values

    def __str__(self):
        return ' '.join(str(v) for v in self.values)

    def __repr__(self):
        return f'{type(self).__name__}( {repr(str(self))} )'

    def __eq__(self, other):
        try:
            return self.values == other.values and type(self) == type(other)
        except AttributeError:
            return False
