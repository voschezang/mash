#!/usr/bin/python3
if __name__ == '__main__':
    import _extend_path  # noqa

from dataclasses import dataclass
from enum import auto, Enum
from json import dumps
from typing import Dict, List

from mash.object_parser.oas import OAS, path_create
from mash.object_parser import build, OAS
from mash.object_parser.errors import SpecError


@dataclass
class C:
    x: int = 1
    y = 2


@dataclass
class B:
    c: float


@dataclass
class A:
    a: int
    b: B
    c: bool
    d: C


User = str


class Capacity(int):
    """An example of a subclass of `int`
    """

    def __new__(cls, value):
        if value < 0:
            raise SpecError(value)

        return super().__new__(cls, value)


class SuperUser(User):
    """An example of a subclass of `str`
    """
    def __new__(cls, value):
        # transform example 1
        value = value.lower()

        return super().__new__(cls, value)

    @staticmethod
    def parse_value(name):
        # transform example 2
        return name.title()


class TeamType(Enum):
    A = auto()
    B = auto()

    @staticmethod
    def parse_value(value):
        # standardize casing
        value = value.upper()

        # allow synonyms
        value = value.upper()
        if value in 'CDE':
            value = 'A'

        return value


@dataclass
class Team:
    members: List[User]
    stakeholders: Dict[str, SuperUser]
    team_type: TeamType = 'A'
    active: bool = True
    capacity: Capacity = 1
    value: float = 1.
    secret: str = ''
    manager: User = 'admin'


@dataclass
class Department:
    manager: User
    teams: List[Team]


@dataclass
class Organization:
    board: List[User]
    ceo: SuperUser
    departments: List[Department]

    _key_synonyms = {'ceo': ['boss']}

    def __post_init__(self):
        if self.ceo in self.board:
            raise SpecError('Incompatible values')


example_data = {
    'board': ['alice'],
    'boss': 'bob',
    'departments': [{
            'manager': 'charlie',
            'teams': [{
                'manager': 'donald',
                'members': ['ernie', 'felix'],
                'stakeholders': {'e27': 'goofy'},
                'team_type': 'a',
                'capacity': 2,
                'value': 3.1
            }]
    }]
}


if __name__ == '__main__':
    org = build(Organization, example_data)

    print(org)
    oas = OAS()
    oas.extend(org)
    oas['servers'] = [{'url': 'http://localhost:5000/v1'}]
    oas['paths']['/organizations'] = path_create('Organization')
    print(dumps(oas))
