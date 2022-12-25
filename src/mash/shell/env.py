from mash.filesystem.filesystem import FileSystem, cd

ENV = 'env'


class Environment:
    """A dict-like interface for a FileSystem instance.
    It mixes local and global scopes.
    """

    def __init__(self, data: FileSystem, **kwds):
        self.data = data
        self.data[ENV].update(kwds)

    def __setitem__(self, key: str, item):
        self.data[ENV][key] = item

    def __getitem__(self, key: str) -> str:
        while True:
            if key in self.data[ENV]:
                return self.data[ENV][key]

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

    def __iter__(self):
        return iter(self.data[ENV])

    def update(self, env: dict):
        for k, v in env.items():
            self.data[ENV][k] = v


def show(env=None):
    if not env:
        return

    print('Env')
    for k in env:
        print(f'\t{k}: {env[k]}')
