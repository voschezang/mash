from dataclasses import dataclass
from enum import auto, Enum
from json import dumps
from typing import List

from object_parser.oas import OAS, path_create
from object_parser.object_parser import JSONFactory, Spec, SpecError


@dataclass
class B:
    c: float


@dataclass
class A:
    a: int
    b: B
    c: bool


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
    team_type: TeamType = 'A'
    active: bool = True
    capacity: Capacity = 1
    value: float = 1.


@dataclass
class DepartmentData:
    manager: User
    teams: List[Team]


class Department(CustomSpec):
    manager: User
    teams: List[Team]


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
                'manager': 'danny',
                'members': ['ernie', 'felix'],
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

    print(org)
    oas = OAS()
    oas.extend(org)
    oas['servers'] = [{'url': 'http://localhost:5000/v1'}]
    oas['paths']['/organizations'] = path_create('Organization')
    print(dumps(oas))
