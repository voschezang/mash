from typing import Generic, Iterable, List, Type, TypeVar, Union

from mash.shell2.ast.node import Node
from mash.shell2.ast.nodes import Nodes
from mash.shell2.ast.term import Integer
from mash.shell2.env import Environment

T = TypeVar('T')


class ArrayList(Nodes, Generic[T]):
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

    def run(self, env: Environment):
        # expand variables in children
        items = [item.run(env) for item in self.items]
        return ArrayList(self.child_types, items)

    # def extend(self, items: List[Node]):
    #     if self.child_types[0] is ArrayList:
    #         for item in items:
    #             if isinstance(item, ArrayList):
    #                 self.items.append(item)
    #             if isinstance(item, list):
    #                 child = ArrayList(self.child_types[1:], item)
    #                 self.items.append(child)
    #     else:
    #         # convert each item to the proper type
    #         for item in items:
    #             self.items.append(self.child_types[0](item))

    # def _infer_child_types(self, child_type: type):
    #     self.child_types.append(child_type)

    #     # handle nested lists
    #     # if child_type is ArrayList:
    #     #     child: ArrayList = child_type.zero()
    #     #     self.child_types.extend(child.child_types)

    @property
    def type(self):
        if self.child_types is ArrayList:
            return 'list[list]'

        inner = self.child_types[-1].instance_type()

        # nesting level
        n = len(self.child_types)
        # e.g. [[[int]]]
        return f"{'[' * n}{inner}{']' * n}"

    def __repr__(self):
        inner = ', '.join(repr(item) for item in self.items)
        return f'[{inner}]'

    def __eq__(self, other: Node) -> bool:
        if not self.items and isinstance(other, ArrayList) and not other.items:
            return True

        return super().__eq__(other)

    def __len__(self):
        return len(self.items)

    @classmethod
    def zero(cls):
        return cls.empty()

    @classmethod
    def empty(cls):
        return cls(Integer, [])


def _init_items(constructor: Type[T], items: Union[List[T], ArrayList[T]]) -> Iterable[Node]:
    for item in items:
        if constructor is ArrayList:
            if isinstance(item, list):
                item = ArrayList(constructor, item)

            assert isinstance(item, ArrayList)

        else:
            item = constructor(item)

        yield item
