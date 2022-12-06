from copy import deepcopy
from typing import Dict, List
import pytest

# TODO avoid the need for relative imports
from mash.object_parser.errors import SpecError
from mash.object_parser.factory import JSONFactory
from mash.object_parser.spec import init_recursively
from examples.object_parser import A, B, Department, DepartmentData, Organization, OrganizationData, SuperUser, Team, TeamType, User, example_data

json = example_data


def test_User():
    email = 'email@example.com'
    user = User(email)
    assert user == email

    user = User('')
    assert user != email


def test_SuperUser():
    name = 'somename'
    assert SuperUser.parse_value(SuperUser(name)) == 'Somename'


def test_Team():
    manager = 'alice'
    data = {'manager': manager, 'members': [], 'stakeholders': {}}
    team = Team(**data, active=False)
    assert team.manager == manager
    assert not team.active

    team = Team(data)
    assert team.manager == manager
    assert team.active

    with pytest.raises(SpecError):
        team = Team(**data, an_incorrect_key=[])
        a = 1

    # missing mandatory key
    with pytest.raises(SpecError):
        team = Team(manager=manager)


def test_Team_with_factory():
    manager = 'alice'
    data = {'manager': manager, 'members': [], 'stakeholders': {}}

    # alt init method, using Factory
    team = JSONFactory(Team).build(data)
    assert team.manager == manager
    assert team.active

    with pytest.raises(SpecError):
        invalid_data = data.copy()
        invalid_data['an_incorrect_key'] = []
        team = JSONFactory(Team).build(invalid_data)

    # missing mandatory key
    with pytest.raises(SpecError):
        team = JSONFactory(Team).build({'manager': manager})


def test_Team_enum():
    team_type = 'B'
    team = Team(manager='a', members=[], team_type=team_type, stakeholders={})
    assert team.team_type == TeamType.B

    with pytest.raises(SpecError):
        Team(manager='a', members=[], team_type='none')


def test_Department():
    for department in json['departments']:

        d = Department(department)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']


def test_Department_with_factory():
    for department in json['departments']:

        # alt init method, using Factory
        d = JSONFactory(Department).build(department)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']


def test_DepartmentData():
    for department in json['departments']:

        d = JSONFactory(DepartmentData).build(department)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']


def test_OrganizationData():
    org = JSONFactory(OrganizationData).build(json)
    assert org.board == json['board']


def test_Organization():
    org = Organization(json)
    assert org.board == json['board']

    # alt init method, using Factory
    org = JSONFactory(Organization).build(json)
    assert org.board == json['board']


def test_Organization_with_translated_key():
    org = Organization(json)
    boss = json['boss']
    assert org.ceo.lower() == boss.lower()


def test_Organization_with_uninitialized_values():
    data = deepcopy(json)
    team = deepcopy(data['departments'][0]['teams'][0])

    # append a non-initialized entry
    team['members'] = List[User]
    team['stakeholders'] = Dict[str, SuperUser]
    team = data['departments'][0]['teams'].append(team)

    org = JSONFactory(Organization).build(data)
    assert org.departments[0].teams[0].manager == 'donald'


def test_dataclass():

    b = {'c': False}
    b = init_recursively(B, b)

    a = {'a': 1, 'b': 2, 'c': False}
    a = init_recursively(A, a)

    a = {'a': 'nan', 'b': 2, 'c': 'yes'}
    with pytest.raises(SpecError):
        a = init_recursively(A, a)
