import pytest
from object_parser import init_recursively, init_values, JSONFactory
from object_parser.object_parser import SpecError
from examples.object_parser_example import A, B, Department, DepartmentData, Organization, SuperUser, Team, TeamType, User, example_data

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

    # alt init method, using Factory
    team = JSONFactory(Team).build(data)
    assert team.manager == manager
    assert team.active

    with pytest.raises(SpecError):
        team = Team(**data, an_incorrect_key=[])
        a = 1

    with pytest.raises(SpecError):
        invalid_data = data.copy()
        invalid_data['an_incorrect_key'] = []
        team = JSONFactory(Team).build(invalid_data)

    # missing mandatory key
    with pytest.raises(SpecError):
        team = Team(manager=manager)

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

        # alt init method, using Factory
        d = JSONFactory(Department).build(department)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']


def test_DepartmentData():
    for department in json['departments']:

        d = init_recursively(DepartmentData, department)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']

        # alt init method, using Factory
        d = JSONFactory(DepartmentData).build(department)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']


def test_DepartmentData2():
    for department in json['departments']:

        fields = init_values(DepartmentData, department)
        d = DepartmentData(**fields)

        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']


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


def test_dataclass():

    b = {'c': False}
    b = init_recursively(B, b)

    a = {'a': 1, 'b': 2, 'c': False}
    a = init_recursively(A, a)

    a = {'a': 'nan', 'b': 2, 'c': 'yes'}
    with pytest.raises(SpecError):
        a = init_recursively(A, a)
