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


class TeamMembers:
    @staticmethod
    def get_all(path: Path) -> List[str]:
        i = path.find('department') + 1
        department = path[i]
        return generate(3, f'department_{department}_team')


class TeamMembers(User):
    pass


class Team:
    members: TeamMembers

    # @staticmethod
    # def get_all(department: str):
    #     return generate(3, f'{department}_team')


class Teams(Team):
    # @staticmethod
    # def get_all(department: str):
    #     return generate(3, f'{department}_team')
    @staticmethod
    def get_all(path: Path) -> List[str]:
        i = path.find('department') + 1
        department = path[i]
        return generate(3, f'{department}_team')


@dataclass
class Department:
    teams: Teams
    # @staticmethod
    # def get_all(organization: str):
    #     return generate(3, f'department')


class Departments(Department):
    @staticmethod
    def get_all(path: Path):
        return generate(2, f'department')


@dataclass
class Organization:
    departments: Departments
    data: str = 'abc'


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
    path = [k]
    print('\npath', path)
    # result = obj.crud.ll(*path)
    print(result)

    k = 'department_1'
    # k = result.split('\n')[0]
    path.append(k)
    print('\npath', path)
    result = obj.crud.ll(*path)
    print(result)
