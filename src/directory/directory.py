#!/usr/bin/python3
from enum import Enum
from pprint import pformat
from typing import Callable, Iterable, List, Union

from util import accumulate_list, first, has_method, is_Dict_or_List, none
from directory.view import NAME, Key, Path, View

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
            option = Option(value)
        except ValueError:
            # conversion failed means that `value` is not an Option
            return False
        return True


Options = [o.value for o in Option]


class Directory:
    def __init__(self, *args,
                 home: Path = None,
                 get_hook: Callable[[Key, View], Key] = first,
                 post_cd_hook: Callable = none,
                 **kwds):
        self.root = dict(*args, **kwds)
        # super().__init__(*args, **kwds)

        self.get_hook = get_hook
        self.post_cd_hook = post_cd_hook

        self.init_states()
        self.init_home(home)

    def init_home(self, home: Path):
        # set tmp default
        self._home = []

        if home is None:
            home = []

        self.cd(Option.root.value)
        self.cd(*home)

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

    def tree(self, *path: str) -> str:
        cwd = self.get(path)
        return pformat(cwd, indent=2)

    def ls(self, *paths: Union[Path, str]) -> List[Key]:
        """List all objects in the dir associated with each path.
        If this dir is a path, then its properties are returned.
        Objects that start with HIDE_PREFIX are ignored.
        """
        if not paths:
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

    def get(self, path: Union[Path, str], relative=True):
        """Return the value of the file associated with `path`.
        """
        # TODO implement get('..') and get(['..', '1'])
        if relative:
            cwd = View(self.state.tree)
        else:
            cwd = View(self.root)

        if path in [(), []]:
            return cwd.tree
        elif isinstance(path, str):
            path = [path]

        if relative:
            full_path = self.full_path[1:] + list(path)
        else:
            full_path = list(path)

        *parents, key = path
        self.traverse_view(parents, cwd)

        key = self.get_hook(key, cwd, full_path)
        _, value = cwd.get(key)
        return value

    def traverse_view(self, path: Path, cwd: View) -> View:
        """Return a view of `path`
        """
        for key in path:
            key = self.get_hook(key, cwd)
            cwd.down(key)

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
            self.cd_option(Option.default)
            self.post_cd_hook()
            return

        # cache current position
        origin = View(self.state.tree, self.state.trace)

        # change dirs
        for k in path:
            self._cd_step(k)

        # store origin
        self.prev = origin

    @property
    def semantic_path(self) -> Path:
        """Convert indices in path to semantic values.
        """
        result = self.path
        for i, path in enumerate(accumulate_list(self.path)):
            *path, key = path
            result[i] = self.infer_key_name(path, key, relative=False)

        return result

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

    ############################################################################
    # Internals
    ############################################################################

    def _cd_step(self, k: Key):
        if Option.verify(k):
            self.cd_option(Option(k))
            self.post_cd_hook()
        else:
            k = self.get_hook(k)
            self.state.down(k)
            self.post_cd_hook()

    def cd_option(self, option: Option):
        if option == Option.root:
            self.goto([])
        elif option == Option.home:
            self.goto(self._home)

        elif option == Option.switch:
            self.state, self.prev = self.prev, self.state

        elif option == Option.up:
            self.state.up()

        elif option == Option.upup:
            self.cd_option(Option.up)
            self.cd_option(Option.up)

        elif option == Option.upupup:
            self.cd_option(Option.up)
            self.cd_option(Option.up)
            self.cd_option(Option.up)

    def goto(self, path: Path):
        if self.full_path == path:
            return

        if path:
            view = self.traverse_view(self._home, View(self.root))
        else:
            view = View(self.root)

        self.prev = self.state
        self.state = view

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

    def __getitem__(self, k):
        return self.root[k]

    def __contains__(self, k):
        return k in self.root