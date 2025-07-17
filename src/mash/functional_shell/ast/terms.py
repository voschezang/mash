
from mash.functional_shell.ast.nodes import Nodes
from mash.functional_shell.env import Environment


class Terms(Nodes):
    def run(self, env: Environment):
        return str(self)
