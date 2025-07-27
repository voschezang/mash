from typing import Dict, Tuple

from mash.shell2.ast.node import Node
from mash.shell2.ast.nodes import Nodes
from mash.shell2.ast.term import Word
from mash.shell2.env import Environment

Data = Dict[str, Node]


class Record(Nodes):
    def __init__(self, *items: Tuple[Word, Node]):
        self.data: Data = {str(k): v for k, v in items}

    def run(self, env: Environment):
        data = [(k, v.run(env)) for k, v in self.data.items()]
        return Record(*data)

    def copy(self):
        data = [(k, v.copy()) for k, v in self.data.items()]
        return self.__class__(*data)

    @property
    def type(self):
        inner = ', '.join(f'{k}: {v.type}' for k, v in self.data.items())
        return f'{{{inner}}}'

    def __repr__(self):
        inner = ', '.join(f'{k}: {repr(v)}' for k, v in self.data.items())
        return f'{{{inner}}}'

    def __eq__(self, other) -> bool:
        return isinstance(other, Record) and self.data == other.data
