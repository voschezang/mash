from discoverable_example import Organization
from discoverable_directory import DiscoverableDirectory


def test_discoverable_ll():
    k = 'repository'
    d = DiscoverableDirectory(repository=Organization)
    assert d.ll() == k


def test_discoverable_cd():
    k = 'repository'
    d = DiscoverableDirectory(repository=Organization)
    d.cd(k)
    assert d.ls() == ['departments', 'field1', 'field2']

    k = 'departments'
    d.cd(k)
    departments = d.ls()
    assert departments[0].startswith('department')

    d.cd(departments[0], 'teams')
    teams = d.ls()
    assert teams[0].startswith('t_')

    path = [teams[0], 'members']
    members = d.ls([teams[0], 'members'])
    i = 1
    assert members[i].startswith('u_')

    # listing an object should return a singleton of itself
    properties = d.ls(path + [members[i]])
    assert 'id' in properties
    assert 'value' in properties
    member = d.get(path + [members[i]])
    assert member['id'] == members[i]
