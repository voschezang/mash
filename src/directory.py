#!/usr/bin/python3
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Tuple, Union

from crud import Option, Path
from util import has_method, identity, none
from directory_view import Key, View


class Directory(dict):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self.pre_cd_hook: Callable[[Key], Any] = identity
        self.post_cd_hook: Callable = none

        self.init_states()

    def init_states(self):
        self.state = View(self, [])
        self.prev = View(self, [])

    @property
    def path(self):
        return self.state.path

    def cp(self, *references: Key):
        """Copy references.

        Usage
        -----
        ```sh
        cp(a, b) # Let b point to the value referenced by a.
        cp(*a, b) # let b contain the pointers *a.
        ```
        """
        self.state.cp(*references)

    def mv(self, *references: Key):
        """Move references.

        Usage
        -----
        ```sh
        mv(a, b) # rename the reference a to b.
        mv(*a, b) # move references *a to b
        ```
        """
        self.state.mv(*references)

    def ls(self, *paths: Union[Path, str]) -> List[Key]:
        """List all objects in the dir associated with each path.
        If this dir is a path, then its properties are returned.
        """
        if not paths:
            return list(self.state.ls())

        return list(self._ls_inner(paths))

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
        origin = View(self.state.tree, self.state.trace)

        # change dirs
        for k in path:
            if Option.verify(k):
                self._cd_option(Option(k))
                self.post_cd_hook()
            else:
                k = self.pre_cd_hook(k)
                self.state.down(k)
                self.post_cd_hook()

        # store origin
        self.prev = origin

    ############################################################################
    # Internals
    ############################################################################

    def _cd_option(self, option: Option):
        if option == Option.root:
            self.prev = self.state
            self.state = View(self, [])

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

    def _ls_inner(self, paths: Tuple[Union[Path, str]]) -> Iterable[Key]:
        """A helper method for self.ls()
        """
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
