from __future__ import annotations
from typing import Iterable, List, Type, TypeVar, Union

from mash.shell.errors import ShellTypeError
from mash.shell2.ast.node import Data, Node
from mash.shell2.ast.term import Integer
from mash.shell2.env import Environment

T = TypeVar('T', bound=Data)


class ArrayList[T](Data):
    """An array with a list-like interface.

    ..code-block:: python

        vector = [1, 2, 3, 4]
        matrix = [[1, 2], [3, 4]]
    """

    def __init__(self, child_type: Type[T], items: List[T]):
        self.items = []
        self.child_types = [child_type]

        self.items = list(_init_items(child_type, items))

        # infer child types
        if child_type is ArrayList:
            if items:
                self.child_types.extend(self.items[0].child_types)
            else:
                # use an arbitrary type
                self.child_types.append(Integer.instance_type())

    def run(self, env: Environment) -> ArrayList[T]:
        # expand variables in children
        items = [item.run(env) for item in self.items]
        return ArrayList(self.child_types, items)

    @property
    def type(self):
        inner = self.child_types[-1].instance_type()

        # nesting level
        n = len(self.child_types)
        # e.g. [[[int]]]
        return f"{'[' * n}{inner}{']' * n}"

    def __repr__(self) -> str:
        inner = ', '.join(repr(item) for item in self.items)
        return f'[{inner}]'

    def __eq__(self, other: Node) -> bool:
        # handle empty lists
        if not self.items and isinstance(other, ArrayList) and not other.items:
            return True

        if isinstance(other, list):
            raise ShellTypeError(
                'Faulty comparison between Python and Mash types.')

        try:
            return self.items == other.items and self.type == other.type

        except AttributeError:
            return False

    def __len__(self) -> int:
        return len(self.items)

    @classmethod
    def zero(cls) -> ArrayList[Integer]:
        return cls.empty()

    @classmethod
    def empty(cls) -> ArrayList[Integer]:
        return cls(Integer, [])


U = Union[T, ArrayList[T]]


def _init_items(constructor: Type[U], items: U) -> Iterable[U]:
    for item in items:
        if constructor is ArrayList:
            if isinstance(item, list):
                item = ArrayList(constructor, item)

            assert isinstance(item, ArrayList)

        else:
            item = constructor(item)

        yield item
