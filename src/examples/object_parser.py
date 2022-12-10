#!/usr/bin/python3
if __name__ == '__main__':
    import _extend_path

from dataclasses import dataclass
from enum import auto, Enum
from json import dumps
from typing import Dict, List

from mash.object_parser.oas import OAS, path_create
from mash.object_parser.factory import JSONFactory
from mash.object_parser.spec import Spec
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


class CustomSpec(Spec):
    key_synonyms = {'ceo': ['boss']}

    def parse_key(key):
        return key.lower()


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
class TeamData:
    members: List[User]
    stakeholders: Dict[str, SuperUser]
    team_type: TeamType = 'A'
    active: bool = True
    capacity: Capacity = 1
    value: float = 1.
    manager: User = 'admin'


class Team(CustomSpec):
    """An example of a subclass of custom Spec type
    """
    manager: User = 'admin'
    members: List[User]
    stakeholders: Dict[str, SuperUser]
    team_type: TeamType = 'A'
    active: bool = True
    capacity: Capacity = 1
    value: float = 1.
    secret: complex = 1j


@dataclass
class DepartmentData:
    manager: User
    teams: List[TeamData]


class Department(CustomSpec):
    manager: User
    teams: List[Team]


@dataclass
class OrganizationData:
    board: List[User]
    ceo: SuperUser
    departments: List[DepartmentData]

    _key_synonyms = {'ceo': ['boss']}

    def __post_init__(self):
        if self.ceo in self.board:
            raise SpecError('Incompatible values')


class Organization(CustomSpec):
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
                'stakeholders': {'goofy': 'goofy'},
                'team_type': 'a',
                'capacity': 2,
                'value': 3.1
            }]
    }]
}


if __name__ == '__main__':
    if 0:
        org = Organization(example_data)
    else:
        org = JSONFactory(Organization).build(example_data)
        org = JSONFactory(OrganizationData).build(example_data)

    print(org)
    oas = OAS()
    oas.extend(org)
    oas['servers'] = [{'url': 'http://localhost:5000/v1'}]
    oas['paths']['/organizations'] = path_create('Organization')
    print(dumps(oas))
