#!/usr/bin/python3
from dataclasses import dataclass
from pprint import pformat
from typing import Any, Callable, Iterable, List, Tuple, Union

from crud import Option, Path
from util import accumulate_list, has_method, identity, none
from directory_view import Key, View


class Directory(dict):
    def __init__(self, *args,
                 get_hook: Callable[[Key, View], Key] = identity,
                 post_cd_hook: Callable = none,
                 **kwds):
        super().__init__(*args, **kwds)

        self.get_hook = get_hook
        self.post_cd_hook = post_cd_hook

        self.init_states()

    def init_states(self):
        self.state = View(self)
        self.prev = View(self)

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

    def tree(self, *path: str) -> str:
        cwd = self.get(path)
        return pformat(cwd, indent=2)

    def ls(self, *paths: Union[Path, str]) -> List[Key]:
        """List all objects in the dir associated with each path.
        If this dir is a path, then its properties are returned.
        """
        if not paths:
            return list(self.state.ls())

        return list(self._ls_inner(paths))

    def ll(self, *path: str, delimiter='\n', include_list_indices=False) -> str:
        """Return a formatted result of ls(). 
        """
        keys = self.ls(path)
        value = self.get(path)

        if getattr(value, '_name', '') in ['Dict', 'List']:
            keys = map(str, keys)
        elif isinstance(value, type):
            keys = [value.__name__]

        elif isinstance(value, list):
            names = (self.infer_key_name(path, k) for k in keys)

            if include_list_indices:
                keys = (f'{i}: {k}' for i, k in enumerate(names))
            else:
                keys = names

        return delimiter.join(keys)

    def get(self, path: Union[Path, str], relative=True):
        """Return the value of the file associated with `path`.
        """
        if relative:
            cwd = View(self.state.tree)
        else:
            cwd = View(self)

        if not path:
            return cwd.tree

        *path, key = path
        for k in path:
            k = self.get_hook(k, cwd)
            cwd.down(k)

        key = self.get_hook(key, cwd)
        _, value = cwd.get(key)
        return value

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
                k = self.get_hook(k)
                self.state.down(k)
                self.post_cd_hook()

        # store origin
        self.prev = origin

    @property
    def semantic_path(self) -> Path:
        """Convert indices in path to semantic values.
        """
        result = self.state.path
        for i, path in enumerate(accumulate_list(self.state.path)):
            *path, key = path
            result[i] = self.infer_key_name(path, key, relative=False)

        return result

    def infer_key_name(self, path: Path, k: Key, relative=True) -> str:
        if isinstance(k, int):
            value = self.get(list(path) + [k], relative=relative)

            try:
                if 'name' in value:
                    return value['name']
            except TypeError:
                pass

            value = str(value)
            n = 100
            if len(value) > n:
                return value[:n] + '..'
            return value
        return str(k)

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

            if getattr(result, '_name', '') in ['Dict', 'List']:
                results = ['Dict of x']
                # results = [result]
            elif isinstance(result, type) or isinstance(result, str):
                results = [result]
            elif has_method(result, 'keys'):
                results = result.keys()
            elif isinstance(result, list):
                results = range(len(result))
            else:
                try:
                    results = list(result)
                except TypeError:
                    results = [result]

            yield from results

# def format_type():
#         if getattr(data, '_name', '') == 'Dict':
#             cls = data.__args__[1]
#             container_cls = dict
#             is_container = True
#         elif getattr(data, '_name', '') == 'List':
#             cls = data.__args__[0]
#             container_cls = list
#             is_container = True
