#!/usr/bin/python3
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

from crud import Option, Path
from util import has_method, identity, none

Key = Union[str, int]
Trace = List[Tuple[Key, Union[dict, list]]]


@dataclass
class State:
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

    def ls(self) -> Iterable[Key]:
        try:
            return self.tree.keys()
        except AttributeError:
            return range(len(self.tree))

    def cd(self, key: Key):
        self._trace.append((key, self.tree))
        # assume that tree[key] is a dict or list
        self.tree = self.tree[key]

    def up(self) -> Key:
        key, self.tree = self._trace.pop()
        return key


class Directory(dict):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.pre_cd_hook: Callable[[Key], Any] = identity
        self.post_cd_hook: Callable = none

        self.init_states()

    def init_states(self):
        self.state = State(self, [])
        self.prev = State(self, [])

    @property
    def path(self):
        return self.state.path

    def mv(self, src: Key, dst: Key):
        del self.tree[src]
        self.tree[dst] = self.tree[src]

    def cp(self, src: Key, dst: Key):
        self.tree[dst] = self.tree[src]

    def ls(self, *paths: Union[Path, str]) -> Iterable[Key]:
        """List all objects in the dir associated with path.
        If this dir is a path, then its properties are returned.
        """
        if not paths:
            yield from self.state.ls()
            return

        for path in paths:
            if isinstance(path, str):
                path = [path]

            result = self.get(path)

            if has_method(result, 'keys'):
                results = result.keys()
            elif isinstance(result, list):
                results = range(len(result))
            else:
                try:
                    results = list(result)
                except TypeError:
                    results = [result]

            yield from results

    def ll(self, *path: str, delimiter='\n') -> str:
        """Return a formatted result of ls(). 
        """
        items = map(str, self.ls(path))
        return delimiter.join(items)

    def get(self, path: Union[Path, str]):
        """Return the value of the file associated with `path`.
        """
        cwd = self.state.tree
        for k in path:
            cwd = cwd[k]

        return cwd

    def append(self, k, v):
        """Associate key k with value v and then change the working directory to k 
        """
        self.state.tree[k] = v
        self.cd(k)

    def cd(self, *path: Key):
        """Change working directory to `path`.
        """
        if not path:
            self._cd_option(Option.default)
            self.post_cd_hook()
            return

        # cache current position
        origin = State(self.state.tree, self.state.trace)

        # change dirs
        for k in path:
            if Option.verify(k):
                self._cd_option(Option(k))
                self.post_cd_hook()
            else:
                k = self.pre_cd_hook(k)
                self.state.cd(k)
                self.post_cd_hook()

        # store origin
        self.prev = origin

    def _cd_option(self, option: Option):
        if option == Option.root:
            self.prev = self.state
            self.state = State(self, [])

        elif option == Option.switch:
            self.state, self.prev = self.prev, self.state

        elif option == Option.up:
            self.state.up()

        elif option == Option.upup:
            self._cd_option(Option.up)
            self._cd_option(Option.up)

        elif option == Option.upupup:
            self._cd_option(Option.up)
            self._cd_option(Option.up)
            self._cd_option(Option.up)
