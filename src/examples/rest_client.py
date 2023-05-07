#!/usr/bin/python3
from dataclasses import dataclass
from json import loads
from time import time
from typing import Dict, List

if __name__ == '__main__':
    import _extend_path

from mash.filesystem.discoverable import observe
from mash.filesystem.view import Path
from mash.shell.shell import main
from mash.shell import ShellWithFileSystem
from mash.server import basepath, init as server_init


def get_user(id):
    data = init_client().get(f'{basepath}users/{id}')
    return loads(data.data)


def init_client():
    app = server_init()
    client = app.test_client()
    return client


def infer_query_parameter(path, key):
    i = path.index(key) + 1
    id = path[i]
    return id


@dataclass
class User:
    id: int
    name: str
    email: int

    @staticmethod
    def get_value(path: Path) -> dict:
        id = infer_query_parameter(path, 'users')

        # get raw object
        user = get_user(id)

        # enrich object
        user['id'] = id
        user['updated'] = time()

        return user

    @staticmethod
    def get_all(path: Path) -> List[str]:
        data = init_client().get(basepath + 'users')
        return {k: User for k in loads(data.data)}


@dataclass
class Organization:
    users: Dict[str, User]


def init():
    shell = ShellWithFileSystem(data={'repository': Organization},
                                get_value_method=observe)
    obj = shell.repository
    obj.init_home(['repository'])
    return shell, obj


if __name__ == '__main__':
    shell, obj = init()
    main(shell=shell.shell)
