from pytest import raises

from examples.discoverable_example import Organization
from directory.discoverable import DiscoverableDirectory


def test_discoverable_ll():
    k = 'repository'
    d = DiscoverableDirectory(repository=Organization)
    assert d.ll() == k


def test_discoverable_unhappy():
    k = 'repository'
    d = DiscoverableDirectory(repository=Organization)

    with raises(TypeError):
        d.get(int)

    for k in ['never', ['never'], [100], [int]]:
        with raises(ValueError):
            d.get(k)

        with raises(ValueError):
            d.ls(k)

    for k in ['never', 100, int, float]:
        with raises(ValueError):
            d.cd(k)


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

    d.cd('...')
    d.cd(departments[0], 'teams')

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


def test_discoverable_ls_double():
    d = DiscoverableDirectory(repository=Organization)

    departments = d.ls(['repository', 'departments'])
    assert departments[0].startswith('department')


def test_discoverable_show():
    d = DiscoverableDirectory(repository=Organization)
    d.cd('repo')
    data = d.show(())
    for v in data.values():
        assert 'Dep department' in v['name']
        assert v['#teams'] == 2

    d.cd('dep', 'd')
    data = d.show(())
    for v in data.values():
        assert 'Team t' in v['name']
        assert v['#members'] == 2
