from typing import List

from mash.shell.errors import ShellTypeError
from mash.shell2.ast.node import Node
from mash.shell2.ast.nodes import Nodes
from mash.shell2.env import Environment


class ArrayList(Nodes):
    def __init__(self, child_type: Node, items: List[Node]):
        self._verify_types(child_type, items)

        self.child_type = child_type
        self.items = items

    def _verify_types(self, expected: type, items: List[Node]):
        for item in items:
            if not isinstance(item, expected):
                raise ShellTypeError(
                    f'All list items must be of type {expected}. Got {item.type}')

    def run(self, env: Environment):
        # expand variables in children
        items = [item.run(env) for item in self.items]
        return ArrayList(self.child_type, items)

    def __len__(self):
        return len(self.items)

    @property
    def type(self):
        return f'list[{self.child_type}]'

    def __repr__(self):
        inner = ', '.join(repr(item) for item in self.items)
        return f'[{inner}]'
