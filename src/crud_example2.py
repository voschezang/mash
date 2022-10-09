#!/usr/bin/python3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from object_parser_example import User
from random import randint, random

from shell_with_crud import ShellWithCRUD
from shell import main


def generate(n, prefix='', delimiter='_'):
    return [f'{prefix}_{randint(0, 1000)}' for i in range(n)]


class Team:
    members: List[User]

    # @staticmethod
    # def get_all(department: str):
    #     return generate(3, f'{department}_team')


class Teams:
    # @staticmethod
    # def get_all(department: str):
    #     return generate(3, f'{department}_team')

    @staticmethod
    def get_all(path: Path):
        i = path.find('department') + 1
        department = path[i]
        return generate(3, f'department_{department}_team')


class Department:
    teams: Teams

    # @staticmethod
    # def get_all(organization: str):
    #     return generate(3, f'department')


class Departments(list):
    @staticmethod
    def get_all(path: Path):
        print('get_all', Path)
        r = generate(3, f'department')
        print(r)
        return generate(3, f'department')


@dataclass
class Organization:
    departments: Departments
    # departments: List[Department]
    data: str = 'abc'

    # @staticmethod
    # def get():
    #     return 'The Name'
    # @staticmethod
    # def get_all():
    #     return generate(1, 'org')


repository = Organization
# if hasattr(self.cls, '__dataclass_fields__'):


if __name__ == '__main__':
    obj = ShellWithCRUD(repository=repository)
    # main(shell=obj.shell)
    result = obj.crud.ll()
    print('Org')
    print(result)

    # k = 'data'
    # result = obj.crud.ll(k)
    # print('\n', k)
    # print(result)

    k = 'departments'
    result = obj.crud.ll(k)
    print('\n', k)
    print(result)
