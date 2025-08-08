
from mash.shell2.ast.command import Command
from mash.shell2.ast.node import Data, Node
from mash.shell2.env import Environment


class IfElse(Node):
    def __init__(self, condition: Command | Data, then: Node, otherwise: Node):
        self.condition = condition
        self.then = then
        self.otherwise = otherwise

    def run(self, env: Environment):
        if bool(self.condition.run(env)):
            return self.then.run(env)
        else:
            return self.otherwise.run(env)

    def __repr__(self) -> str:
        return f'(?) ({self.condition})'
