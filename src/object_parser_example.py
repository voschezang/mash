from typing import List
from dataclasses import dataclass
from object_parser import Spec, SpecError

class CustomSpec(Spec):
    translations = {'ceo': ['boss']}

User = str

class Team(CustomSpec):
    manager: User = 'admin'
    members: List[User]


class Department(CustomSpec):
    manager: User
    teams: List[Team]


class Organization(CustomSpec):
    board: List[User]
    ceo: User
    departments: List[Department]

    def _validate(self):
        if self.ceo in self.board:
            raise SpecError('Incompatible values')


        #'boss': 'bob',
example_data = {
        'board': ['alice'],
        'ceo': 'bob',
        'departments': [{
            'manager': 'charlie',
            'teams': [{
                'manager': 'danny', 
                'members': ['ernie', 'felix']
                }]
            }]
        }


if __name__ == '__main__':
    org = Organization(example_data)
    print(vars(org))
