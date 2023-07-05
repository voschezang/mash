from copy import deepcopy
from typing import Dict, List
import pytest

# TODO avoid the need for relative imports
from mash.object_parser.errors import SpecError
from mash.object_parser.factory import JSONFactory, build
from examples.object_parser import Department, Department, Organization, Organization, SuperUser, Team, TeamType, User, example_data
from examples import discoverable_with_oas

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
    team = build(Team, data)
    assert team.manager == manager
    assert team.active

    with pytest.raises(SpecError):
        team = build(Team, {'a': 1})

    # missing mandatory key
    with pytest.raises(SpecError):
        team = build(Team, {'manger': 'a'})


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
        JSONFactory(Team).build({'manager': manager})

    with pytest.raises(SpecError):
        JSONFactory(Team).build({})


def test_Team_enum():
    team_type = 'B'
    data = {'manager': 'a', 'members': [],
            'team_type': team_type, 'stakeholders': {}}

    team = build(Team, data)
    assert team.team_type == TeamType.B

    with pytest.raises(SpecError):
        data['team_type'] = 'none'
        build(Team, data)


def test_Department():
    for department in json['departments']:

        d = build(Department, department)

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


def test_Department():
    for department in json['departments']:

        d = JSONFactory(Department).build(department)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']

    with pytest.raises(SpecError):
        JSONFactory(Department).build({})


def test_Organization():
    org = JSONFactory(Organization).build(json)
    assert org.board == json['board']


def test_Organization():
    org = build(Organization, json)
    assert org.board == json['board']

    # alt init method, using Factory
    org = JSONFactory(Organization).build(json)
    assert org.board == json['board']


def test_Organization_with_translated_key():
    org = build(Organization, json)
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


def test_object_parser_discoverable():
    oas = discoverable_with_oas.main()
    assert 'paths' in oas
    assert '/organizations' in oas['paths']

    assert 'components' in oas
    assert 'schemas' in oas['components']
    assert 'Organization' in oas['components']['schemas']
