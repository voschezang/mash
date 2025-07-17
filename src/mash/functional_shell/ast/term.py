
from mash.functional_shell.ast.node import Node
from mash.functional_shell.ast.nodes import Nodes
from mash.functional_shell.env import Environment


class Term(Node):
    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other):
        return self.value == other

    @property
    def data(self):
        return self.value


class Word(Term):
    def run(self, env: Environment):
        return self.value
