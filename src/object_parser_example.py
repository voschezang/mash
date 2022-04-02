from typing import List
from dataclasses import dataclass
from object_parser import Spec, SpecError
from oas import OAS
from enum import Enum, auto
from pprint import pprint


class CustomSpec(Spec):
    key_synonyms = {'ceo': ['boss']}

    def parse_key(key):
        return key.lower()


User = str


class SuperUser(User):
    """An example of a subclass of a native type
    """
    def __new__(cls, value):
        # transform example 1
        value = value.lower()

        return str.__new__(cls, value)

    @staticmethod
    def parse(name):
        # transform example 2
        return name.title()


class TeamType(Enum):
    A = auto()
    B = auto()

    @staticmethod
    def parse(value):
        # standardize casing
        value = value.upper()

        # allow synonyms
        value = value.upper()
        if value in 'CDE':
            value = 'A'

        return value


class Team(CustomSpec):
    """An example of a subclass of custom Spec type
    """
    manager: User = 'admin'
    members: List[User]
    team_type: TeamType = 'A'
    active: bool = True


class Department(CustomSpec):
    manager: User
    teams: List[Team]


class Organization(CustomSpec):
    board: List[User]
    ceo: SuperUser
    departments: List[Department]

    def validate(self):
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
                'team_type': 'a'
            }]
    }]
}


if __name__ == '__main__':
    org = Organization(example_data)
    print(vars(org))

    oas = OAS()
    oas.extend(org)
    print(oas)
