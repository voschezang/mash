#!/usr/bin/python3
"""A filesystem-like interface for static and dynamic data.
This can be used to e.g. browse REST APIs.
"""
from enum import Enum
from pickle import dumps, loads
from pprint import pformat
from typing import Callable, Iterable, List, Tuple, Union

from mash.util import accumulate_list, first, has_method, is_Dict_or_List, none
from mash.filesystem.view import Data, NAME, Key, Path, View

HIDE_PREFIX = '.'


class Option(Enum):
    default = '~'
    home = '~'
    root = '/'
    stay = '.'
    switch = '-'
    up = '..'
    upup = '...'
    upupup = '....'

    @staticmethod
    def verify(value):
        try:
            Option(value)
        except ValueError:
            # failed conversion implies that `value` was not an Option
            return False
        return True


OPTIONS = [o.value for o in Option]


class FileSystem:
    def __init__(self,
                 root: dict = None,
                 home: Path = None,
                 get_hook: Callable[[Key, View], Key] = first,
                 post_cd_hook: Callable = none,
                 **dict_kwds):

        if root is None:
            self.root = dict(**dict_kwds)
        else:
            self.root = root

        self.get_hook = get_hook
        self.post_cd_hook = post_cd_hook

        self.init_states()
        self.init_home(home)

    def init_home(self, home: Path):
        if isinstance(home, str):
            home = [home]

        # set temporary default
        self._home = []

        if home is None:
            home = []

        abs_path = [Option.root.value] + home
        self.cd(*abs_path)

        self._home = self.state.path

        # reset path
        self.cd()

    def init_states(self):
        self.state = View(self.root)
        self.prev = View(self.root)

    @property
    def path(self) -> Path:
        if self.in_home():
            i = len(self._home)
            return self.state.path[i:]

        return self.full_path

    @property
    def full_path(self) -> Path:
        return [Option.root.value] + self.state.path

    @property
    def home(self) -> Path:
        return self._home

    @property
    def cwd(self) -> View:
        """A shallow copy of the current working directory.
        """
        return self.state.copy()

    def in_home(self) -> bool:
        """Check whether home is in cwd.
        """
        path = self.state.path
        return len(path) >= len(self._home) and \
            all(path[i] == k for i, k in enumerate(self._home))

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
        # TODO rename copies as well. e.g. in self.prev
        self.state.mv(*references)

    def rm(self, *references: Key):
        """Remove references.
        """
        self.state.rm(*references)

    def tree(self, *path: str) -> str:
        cwd = self.get(path)
        return pformat(cwd, indent=2)

    def ls(self, *paths: Union[Path, str]) -> List[Key]:
        """List all objects in the dir associated with each path.
        If this dir is a path, then its properties are returned.
        Objects that start with HIDE_PREFIX are ignored.
        """
        if not paths:
            self.get_hook(None, self.cwd)
            items = self.state.ls()
        else:
            items = self._ls_inner(paths)

        return [item for item in items if not str(item).startswith(HIDE_PREFIX)]

    def ll(self, *path: str, delimiter='\n', include_list_indices=False) -> str:
        """Return a formatted result of ls(). 
        """
        keys = self.ls(path)
        value = self.get(path)

        if is_Dict_or_List(value):
            keys = map(str, keys)
        elif isinstance(value, type):
            keys = [value.__name__]

        elif isinstance(value, list):
            names = (self.infer_key_name(path, k) for k in keys)

            if include_list_indices:
                keys = (f'{i}: {k}' for i, k in enumerate(names))
            else:
                keys = names

        try:
            return delimiter.join(keys)
        except TypeError:
            return delimiter.join((str(k) for k in keys))

    def get(self, path: Path, relative=True):
        """Return the value of the file associated with `path`.
        """
        key, cwd = self._get_inner(path, relative)
        key = self.get_hook(key, cwd)
        _, value = cwd.get(key)
        return value

    def set(self, k, value: Data, cwd: View = None):
        """Assign a value to the file k.
        """
        if cwd is None:
            cwd = self.cwd

        path = self.path
        prev = self.prev.path

        cwd.set(k, value)
        self.init_states()

        # reset self.prev
        if k not in prev:
            self.cd(*prev)
        else:
            self.cd()

        # reset self.state
        self.cd('-')
        self.cd(*path)

    def append(self, k, v):
        """Associate key k with value v and then change the working directory to k 
        """
        self.state.tree[k] = v
        self.cd(k)

    def cd(self, *path: Key):
        """Change working directory to `path`.
        """
        # cache current position
        origin = self.cwd

        if path:
            # step through path
            for k in path:
                self.cd_step(k)

        else:
            self.cd_option(Option.default)

        # store origin
        self.prev = origin

        self.post_cd_hook()

    @property
    def semantic_path(self) -> Path:
        """Convert indices in path to semantic values.
        """
        result = self.path
        for i, path in enumerate(accumulate_list(self.path)):
            *path, key = path
            result[i] = self.infer_key_name(path, key, relative=False)

        return result

    def simulate_cd(self, path: Path, relative: bool) -> View:
        view = self.copy(post_cd_hook=none)

        if not relative:
            view.cd(Option.root.value)

        if path:
            view.cd(*path)

        return view.cwd

    def snapshot(self) -> bytes:
        return dumps(self.root)

    def load(self, snapshot: bytes):
        self.root = loads(snapshot)
        self.cd()

    def copy(self, post_cd_hook=None):
        if post_cd_hook is None:
            post_cd_hook = self.post_cd_hook

        fs = FileSystem(self.root, self.home, self.get_hook, post_cd_hook)
        fs.state = self.state.copy()
        fs.prev = self.prev.copy()
        return fs

    def __getitem__(self, k):
        return self.root[k]

    def __contains__(self, k):
        return k in self.root

    ############################################################################
    # Internals
    ############################################################################

    def infer_key_name(self, path: Path, k: Key, relative=True) -> str:
        if isinstance(k, int):
            value = self.get(list(path) + [k], relative=relative)

            try:
                if NAME in value:
                    return value[NAME]
            except TypeError:
                pass

            value = str(value)
            n = 100
            if len(value) > n:
                return value[:n] + '..'
            return value
        return str(k)

    def cd_step(self, k: Key):
        if Option.verify(k):
            k = Option(k)
            if k == Option.home:
                self.cd_option(Option.root)
                self.cd(*self._home)
            else:
                self.cd_option(k)

        else:
            # TODO ensure that get_hook is not bound to another instance
            k = self.get_hook(k, self.cwd)
            self.state.down(k)

    def cd_option(self, option: Option):
        # Note that Option default will be matched to another value
        if option == Option.root:
            if self.state._trace:
                _, tree = self.state._trace[0]
                self.state.tree = tree
                self.state._trace = []

        elif option == Option.home:
            if self.path != self.home:
                self.cd_option(Option.root)
                self.cd(*self._home)

        elif option == Option.switch:
            self.state, self.prev = self.prev, self.state

        elif option == Option.up:
            self.state.up()

        elif option == Option.upup:
            self.state.up()
            self.state.up()

        elif option == Option.upupup:
            self.state.up()
            self.state.up()
            self.state.up()

    def _get_inner(self, path: Path, relative: bool) -> Tuple[Key, View]:
        if isinstance(path, str):
            path = [path]
        else:
            path = list(path)

        parents, key = path, None
        if path:
            key_is_option = Option.verify(path[-1])
            if not key_is_option:
                *parents, key = path

        if parents or not relative:
            cwd = self.simulate_cd(parents, relative)
        else:
            cwd = self.cwd

        return key, cwd

    def _ls_inner(self, paths: Iterable[Union[Path, str]]) -> Iterable[Key]:
        """A helper method for self.ls()
        """
        for path in paths:
            if isinstance(path, str):
                path = [path]

            result = self.get(path)

            if has_method(result, 'keys'):
                results = result.keys()
            elif isinstance(result, str):
                results = [result]
            elif isinstance(result, list):
                results = range(len(result))
            else:

                try:
                    results = list(result)
                except TypeError:
                    results = [result]

            yield from results
