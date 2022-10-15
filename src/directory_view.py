#!/usr/bin/python3
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Union

from crud import Path

Key = Union[str, int]
Trace = List[Tuple[Key, Union[dict, list]]]


@dataclass
class View:
    """A tree of dict's. Tree traversal is managed with the methods cd, up.
    """
    tree: dict
    _trace: Trace

    @property
    def trace(self) -> Trace:
        """A copy of the interal field `_trace`.
        """
        return list(self._trace)

    @property
    def path(self) -> Path:
        return [k for k, _ in self.trace]

    def up(self) -> Key:
        key, self.tree = self._trace.pop()
        return key

    def down(self, key: Key):
        self._trace.append((key, self.tree))
        # assume that tree[key] is a dict or list
        self.tree = self.tree[key]

    def ls(self) -> Iterable[Key]:
        try:
            return self.tree.keys()
        except AttributeError:
            return range(len(self.tree))

    def cp(self, *references: Key):
        *sources, dst = references

        if not sources:
            raise ValueError(
                f'At least two arguments are required, but got {references}')
        elif len(sources) == 1:
            src = sources[0]
            self.tree[dst] = self.tree[src]
        else:
            if dst not in self.tree or self.tree[dst] is None:
                self.tree[dst] = {}

            for k in sources:

                self.tree[dst][k] = self.tree[k]

    def mv(self, *references: Key):
        # first copy references
        self.cp(*references)

        # de-reference src keys
        *src, dst = references
        for src in src:
            if src != dst and src in self.tree:
                del self.tree[src]
