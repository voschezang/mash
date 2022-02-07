import pytest
from src.object_parser_example import *

json = example_data

def test_User():
    email = 'email@example.com'
    user = User(email)
    assert user == email

    user = User('')
    assert user != email


def test_Team():
    manager = 'alice'
    team = Team(manager=manager, members=[])
    assert team.manager == manager

    with pytest.raises(SpecError):
        team = Team(manager=manager, an_incorrect_key=[])


def test_Department():
    for department in json['departments']:
        d = Department(department)
        assert d.manager == department['manager']
        i = 0
        assert d.teams[i].manager == department['teams'][i]['manager']
        assert d.teams[i].members == department['teams'][i]['members']


def test_Organization():
    org = Organization(json)
    assert org.board == json['board']


def test_Organization_with_translated_key():
    org = Organization(json)
    boss = json['boss']
    assert org.ceo == boss

