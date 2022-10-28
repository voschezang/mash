#!/usr/bin/python3
from dataclasses import dataclass
from functools import lru_cache
from json import dumps
from random import randint
from typing import Dict, List
import sys

if __name__ == '__main__':
    sys.path.append('src')


from object_parser.object_parser import JSONFactory
from object_parser.oas import OAS, path_create
from directory.view import Path
from directory.discoverable import DiscoverableDirectory


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


@dataclass
class Organization:
    departments: Dict[str, Department]
    field1: str = 'abc'
    field2: str = 'abc'


if __name__ == '__main__':
    obj = DiscoverableDirectory(repository=Organization)
    result = obj.ll()
    print('Org')
    print(result)
    obj.cd('repository')

    path = []
    result = 'departments'

    for i in range(7):
        k = result.split('\n')[-1]
        path.append(k)
        print('\npath', path)
        result = obj.ll(*path)
        print(result)

    print(obj)
    json = JSONFactory(Organization).build(obj['repository'])
    oas = OAS()
    oas.extend(json)
    oas['servers'] = [{'url': 'http://localhost:5000/v1'}]
    oas['paths']['/organizations'] = path_create('Organization')
    print(dumps(oas))
