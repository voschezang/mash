
from collections import UserString
from mash.shell2.ast.node import Node
from mash.shell2.ast.nodes import Nodes
from mash.shell2.env import Environment


class Term(Node):
    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other):
        return self.value == other


class Word(Term, UserString):
    """Wrapper for strings that represent a single word.
    This is a subclass from UserString, so it can be compared to other strings.
    """

    def run(self, env: Environment):
        return self.value

    def __repr__(self):
        return self.value

    @property
    def data(self):
        return self.value
