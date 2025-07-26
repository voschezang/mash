from typing import Callable, List

from mash.shell2.ast.node import Node
from mash.shell2.ast.nodes import Nodes
from mash.shell2.env import Environment


class ArrayList(Nodes):
    def __init__(self, child_type: type, items: List[Node]):
        self.child_type = child_type
        self.items = []

        # convert and append each item
        return self.extend(items)

    def run(self, env: Environment):
        # expand variables in children
        items = [item.run(env) for item in self.items]
        return ArrayList(self.child_type, items)

    def extend(self, items):
        convert: Callable = self.child_type

        # if self.child_type is ArrayList:
        #     def convert(value):
        #         return ArrayList(self.child_type, value)

        for item in items:
            self.items.append(convert(item))

    def __len__(self):
        return len(self.items)

    @property
    def type(self):
        if self.child_type is ArrayList:
            return 'list[list]'

        return f'list[{self.child_type.instance_type()}]'

    def __repr__(self):
        inner = ', '.join(repr(item) for item in self.items)
        return f'[{inner}]'

    @classmethod
    def zero(cls):
        return cls(ArrayList, [])
