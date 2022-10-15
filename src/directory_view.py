#!/usr/bin/python3
from dataclasses import dataclass, field
import logging
from typing import Any, Iterable, List, Tuple, Union

from crud import Path
from util import find_fuzzy_matches, find_prefix_matches, identity, is_digit, list_prefix_matches, none, take

Key = Union[str, int]
Trace = List[Tuple[Key, Union[dict, list]]]

NAME = 'name'


@dataclass
class View:
    """A tree of dict's. Tree traversal is managed with the methods cd, up.
    """
    tree: dict
    _trace: Trace = field(default_factory=list)

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
        key, value = self.get(key)

        self.tree = value
        self._trace.append((key, self.tree))

    def get(self, k: Key) -> Tuple[Key, Any]:
        """Return the value that is refrences by k.
        May raises ValueError.
        """
        if isinstance(self.tree, list):
            return self._get_from_list(k)
        return self._get_from_dict(k)

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

    ############################################################################
    # Internals
    ############################################################################

    def infer_index(self, key: Key):
        if is_digit(key):
            return int(key)

        items = self.ls()
        try:
            names = [item[NAME] for item in items]
        except TypeError:
            names = list(map(str, items))

        if key not in names:
            logging.debug(f'Dir {key} is not present in `ls()`')

        match = next(find_fuzzy_matches(key, names))
        return names.index(match)

    def _get_from_dict(self, k):
        try:
            if k not in self.tree:
                keys = self.ls()
                k = next(find_prefix_matches(str(k), keys))

            return k, self.tree[k]

        except KeyError:
            raise ValueError(self._file_not_found(k))

    def _get_from_list(self, k):
        # convert key to an index
        i = self.infer_index(k)

        try:
            return i, self.tree[i]
        except (IndexError, KeyError):
            raise ValueError(self._file_not_found(k))

    def _file_not_found(self, k):
        preview = ', '.join([str(s) for s in take(self.ls(), 5)])[:80]
        return f'No such file or directory: `{k}` not in [{preview}..]'
