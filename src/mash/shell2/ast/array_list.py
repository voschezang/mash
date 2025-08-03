from __future__ import annotations
from functools import singledispatchmethod
import itertools
from typing import Iterable, List, Type, TypeVar

from mash.shell.errors import ShellTypeError
from mash.shell2.ast.node import Data, Node
from mash.shell2.ast.term import Integer
from mash.shell2.ast.variable import Variable
from mash.shell2.env import Environment

T = TypeVar('T', bound=Data)


class ArrayList[T](Data):
    """An array with a list-like interface.

    ..code-block:: python

        vector = [1, 2, 3, 4]
        matrix = [[1, 2], [3, 4]]
    """

    def __init__(self, items: Iterable[Data], child_type: Type[T] = Variable):
        self.items = list(_init_items(items, child_type))
        self.child_types = _init_child_types(self.items, child_type)

    def run(self, env: Environment) -> ArrayList:
        if not self.items:
            return ArrayList.zero()

        # expand variables in child elements
        items = (item.run(env) for item in self.items)

        # peek at the first element to deduce the type
        peek = next(items)
        return ArrayList(itertools.chain([peek], items),
                         child_type=type(peek))

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

    def __bool__(self) -> bool:
        return bool(self.items)

    @singledispatchmethod
    def __eq__(self, other) -> bool:
        raise ShellTypeError(
            'Faulty comparison between Python and Mash types.')

    @__eq__.register
    def _(self, other: Data) -> bool:
        if not isinstance(other, ArrayList):
            return False

        return (not self.items and not other.items) or \
            (self.items == other.items and
             self.type == other.type)

    @__eq__.register
    def _(self, other: Node) -> bool:
        return False

    def __len__(self) -> int:
        return len(self.items)

    @classmethod
    def zero(cls) -> ArrayList[Integer]:
        return cls.empty()

    @classmethod
    def empty(cls) -> ArrayList[Integer]:
        return cls([])


U = T | Variable


def _init_items(items: List[Data], child_type: Type[T]) -> Iterable[U]:
    """Initialize each item in `items` using .cast()
    to ensure that each item is an instance of `child_type`.
    """
    for item in items:
        if isinstance(item, list) and not isinstance(item, ArrayList):
            item = ArrayList(item)

        if child_type is not Variable and not isinstance(item, ArrayList):
            item = child_type.cast(item)

        assert isinstance(item, Node)

        yield item


def _init_child_types(items: List[U], child_type: Type[T]) -> List[Type[U]]:
    """Create a list of child types corresponding to `items`.
    Returns a list similar to:

    - [U]
    - [ArrayList, U]
    - [ArrayList, ArrayList, U]
    - ...
    """
    if child_type is ArrayList or (items and isinstance(items[0], ArrayList)):
        return [ArrayList] + items[0].child_types

    return [child_type]
