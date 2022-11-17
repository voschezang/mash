#!/usr/bin/python3
from dataclasses import dataclass
from functools import lru_cache
from json import dumps
from random import randint
from typing import Dict, List
import sys

if __name__ == '__main__':
    sys.path.append('src')


from directory.view import Path
from shell import main
from shell.with_directory import ShellWithDirectory


@lru_cache
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

    @staticmethod
    def get_all(path: Path) -> List[str]:
        return generate('t')


@dataclass
class Department:
    teams: List[Team]

    @staticmethod
    def get_all(*_) -> List[type]:
        return generate('department')


@dataclass
class Department:
    teams: List[Team]

    @staticmethod
    def get_all(*_) -> Dict[str, type]:
        keys = generate('department')
        return {k: Department for k in keys}

    # @staticmethod
    # def show(department):
    #     return {i: {'name': item, 'members': len(item['members'])}
    #             for i, item in enumerate(department.teams)}
    @staticmethod
    def show(department: dict):
        return {k: {'name': 'Team ' + k, '#members': len(v['members'].keys())} for k, v in department['teams'].items()}


@dataclass
class Organization:
    departments: Dict[str, Department]
    field1: str = 'abc'
    field2: str = 'abc'

    @staticmethod
    def show(organization: dict):
        return {k: {'name': 'Dep ' + k, '#teams': len(v['teams'].keys())} for k, v in organization['departments'].items()}


if __name__ == '__main__':
    shell = ShellWithDirectory(data={'repository': Organization})
    obj = shell.repository
    # obj = DiscoverableDirectory(repository=Organization)
    result = obj.ll()
    print('Org')
    print(result)
    obj.init_home(['repository'])

    path = []
    result = 'departments'

    # for i in range(7):
    #     k = result.split('\n')[-1]
    #     path.append(k)
    #     print('\npath', path)
    #     result = obj.ll(*path)
    #     print(result)

    # print(obj)
    # json = JSONFactory(Organization).build(obj['repository'])
    # oas = OAS()
    # oas.extend(json)
    # oas['servers'] = [{'url': 'http://localhost:5000/v1'}]
    # oas['paths']['/organizations'] = path_create('Organization')
    # print(dumps(oas))

    obj.init_home(['repository', 'departments'])
    main(shell=shell.shell)
