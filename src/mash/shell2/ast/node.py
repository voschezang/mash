from mash.shell2.env import Environment


class Node:
    """A node (edge) of an abstract syntax tree (AST).
    """

    def run(self, env: Environment):
        raise NotImplementedError()

    def __repr__(self):
        raise NotImplementedError()

    def __eq__(self, other):
        raise NotImplementedError()
