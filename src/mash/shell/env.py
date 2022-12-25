from typing import Iterable
from mash.filesystem.filesystem import FileSystem, cd
from mash.util import crop

ENV = 'env'


class Environment:
    """A dict-like interface for a FileSystem instance.
    It mixes local and global scopes.
    """

    def __init__(self, data: FileSystem, **kwds):
        self.data = data
        if ENV not in self.data:
            self.data.set(ENV, {})

        self.update(kwds)

    def __setitem__(self, key: str, item):
        """Let `key` point to `item` in the current scope. 
        """
        with cd(self.data, ENV):
            self.data.set(key, item)

    def __getitem__(self, key: str) -> str:
        """Find `key` in all scopes and return the corresponding value.
        """
        while True:
            if key in self.data[ENV]:
                return self.data.get([ENV, key])

            try:
                self.data.cd('..')
            except IndexError:
                raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        return True

    def __delitem__(self, key):
        while True:
            if key in self.data[ENV]:
                with cd(self.data, ENV):
                    self.data.rm(key)
                return

            try:
                self.data.cd('..')
            except IndexError:
                raise KeyError(key)

    # def __iter__(self):
    #     return iter(self.data[ENV])

    def __str__(self) -> str:
        return str({k: crop(self[k], 15) for k in self.keys()})

    def asdict(self) -> str:
        return {k: self[k] for k in self.keys()}

    def keys(self) -> Iterable[str]:
        """Return the keys of all environment variables. 
        Keys of global variables that are shadowed by local variables are ignored.
        """
        # use an ordered list
        keys = []
        with cd(self.data, '.'):
            while True:
                # iterate over all scopes, from local to global
                for key in self.data[ENV]:
                    # skip duplicate keys
                    if key not in keys:
                        keys.append(key)

                try:
                    self.data.cd('..')
                except IndexError:
                    break
        return keys

    def update(self, env: dict):
        for k, v in env.items():
            self[k] = v


def show(env=None):
    if not env:
        return

    print('Env')
    for k in env:
        print(f'\t{k}: {env[k]}')
