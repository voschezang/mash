#!/usr/bin/python3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List
import requests
from random import randint

from crud_static import StaticCRUD
from shell import main


@lru_cache
def generate(prefix='', n=2):
    return [f'{prefix}_{randint(0, 1000)}' for i in range(n)]


# class RemoteData(ABC):
#     @abstractmethod
#     def get_value(path: Path) -> Any:
#         pass

#     @abstractmethod
#     def get_all(path: Path) -> Dict[str, type]:
#         pass


class Member(str):
    @staticmethod
    def get_value(path: Path) -> str:
        # return path[-1] + '---'
        return [path[-1] + '---', path[-1] + '+++']

    @staticmethod
    def get_all(path: Path) -> List[str]:
        return generate(f'u')


class Team:
    # members: Dict[str, Member]
    members: List[Member]

    @staticmethod
    def get_all(path: Path) -> List[str]:
        return generate(f't')


@dataclass
class Department:
    # teams: List[str, Team]
    teams: List[Team]

    @staticmethod
    def get_all(path: Path) -> Dict[str, type]:
        keys = generate(f'department')
        return {k: Department for k in keys}


@dataclass
class Organization:
    departments: Dict[str, Department]
    field1: str = 'abc'
    field2: str = 'abc'


if __name__ == '__main__':
    obj = StaticCRUD(repository=Organization)
    result = obj.ll()
    print('Org')
    print(result)

    path = []

    result = 'departments'
    for i in range(6):
        k = result.split('\n')[0]
        path.append(k)
        print('\npath', path)
        result = obj.ll(*path)
        print(result)

    print('\npath', path)
    result = obj.ll(*path)
    print(result)
    # print('\npath', path)
    # result = obj.ll(*path)
    # print(result)

    # result = obj.ll(*path)
    # print(result)
    # result = obj.ll(*path)
    # print(path)
    # print(result)
    # TODO ls ..../users/123 returns a list of users
