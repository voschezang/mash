from logging import debug
from typing import Any, Iterable, Tuple
from mash.filesystem.filesystem import FileSystem, cd
from mash.util import constant, crop


class Scope:
    """A dict-like interface for a FileSystem instance.
    It exposes behaviour of global and local variables.

    It mixes local and global scopes, like 

    If a file is not present in the current directory,
    then this class attempts to acces it in each parent directory.
    """

    def __init__(self, data: FileSystem, key='env', **kwds):
        self.data = data
        self.key = key
        if self.key not in self.data:
            self.data.set(self.key, {})

        self.update(kwds)

    def __setitem__(self, key: str, item):
        """Let `key` point to `item` in the current scope. 
        """
        with cd(self.data, self.key):
            # warn on overriding a non-local variable
            if key not in self.data and key in self.keys():
                debug(f'Warning: shadowing a global variable: {key}')
            self.data.set(key, item)

    def __getitem__(self, key: str) -> str:
        """Find `key` in all scopes and return the corresponding value.
        """
        with cd(self.data):
            while True:
                if key in self.data[self.key]:
                    return self.data.get([self.key, key])

                try:
                    self.data.cd_up()
                except IndexError:
                    raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        return True

    def __delitem__(self, key):
        with cd(self.data):
            while True:
                if key in self.data[self.key]:
                    self.data.cd(self.key)
                    self.data.rm(key)
                    return

                try:
                    self.data.cd_up()
                except IndexError:
                    raise KeyError(key)

    def __str__(self) -> str:
        return str({k: crop(str(self[k]), 15) for k in self.keys()})

    def __iter__(self):
        return iter(self.keys())

    def asdict(self) -> dict:
        return {k: self[k] for k in self.keys()}

    def keys(self) -> Iterable[str]:
        """Return the keys of all environment variables.
        Keys of global variables that are shadowed by local variables are ignored.
        """
        # use an ordered list
        keys = []
        with cd(self.data):
            while True:
                # iterate over all scopes, from local to global
                if self.key in self.data:
                    for key in self.data[self.key]:
                        # skip duplicate keys
                        if key not in keys:
                            keys.append(key)

                try:
                    self.data.cd_up()
                except IndexError:
                    break
        return keys

    def update(self, env: dict = {},
               items: Tuple[str, Any] = []):
        for k, v in env.items():
            self[k] = v

        for k, v in items:
            self[k] = v


def show(env: Scope = None, when=constant(True)):
    if not env:
        return

    for k in env:
        if when(k):
            print(f'\t{k}: {env[k]}')
