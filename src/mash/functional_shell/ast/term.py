from collections import UserString

from mash.functional_shell.env import Environment


class Node(UserString):
    """A node (edge) of an abstract syntax tree (AST).
    """

    def __init__(self, data=''):
        # store value transparently
        self.data = data

    def run(self, env: Environment):
        pass
