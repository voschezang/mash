#!/usr/bin/python3
from dataclasses import dataclass
from random import randint
from typing import Dict, List
import pandas as pd

if __name__ == '__main__':
    import _extend_path

from mash.filesystem.discoverable import observe
from mash.filesystem.view import Path
from mash.shell.shell import main
from mash.shell import ShellWithFileSystem


def generate(prefix: str, n=2):
    return [f'{prefix}_{randint(0, 1000)}' for i in range(n)]


@dataclass
class Member:
    id: str
    value: int

    @staticmethod
    def get_value(path: Path) -> dict:
        return {'id': path[-1], 'value': 100}

    @staticmethod
    def get_all(path: Path) -> List[str]:
        return generate('u')


@dataclass
class Team:
    members: List[Member]
    name: str
    first_member: Member

    @staticmethod
    def get_all(path: Path) -> List[str]:
        return generate('t')


@dataclass
class Department:
    teams: List[Team]

    @staticmethod
    def refresh(*_) -> bool:
        return 0

    @staticmethod
    def get_all(*_) -> Dict[str, type]:
        keys = generate('department')
        return {k: Department for k in keys}

    @staticmethod
    def show(department: dict):
        data = {k: {'name': 'Team ' + k, '#members': len(v['members'].keys())}
                for k, v in department['teams'].items()}
        return pd.DataFrame(data).T


@dataclass
class Organization:
    departments: Dict[str, Department]
    field1: str = 'abc'
    field2: str = 'abc'

    @staticmethod
    def show(organization: dict):
        data = {k: {'name': 'Dep ' + k, '#teams': len(v['teams'].keys())}
                for k, v in organization['departments'].items()}
        return pd.DataFrame(data).T


if __name__ == '__main__':
    shell = ShellWithFileSystem(data={'repository': Organization},
                                get_value_method=observe)
    obj = shell.repository
    result = obj.ll()
    obj.init_home(['repository'])

    path = []
    result = 'departments'

    obj.init_home(['repository', 'departments'])
    main(shell=shell.shell)
