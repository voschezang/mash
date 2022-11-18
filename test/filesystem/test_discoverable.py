from pytest import raises

from examples.discoverable_example import Organization, generate
from filesystem.discoverable import Discoverable


def test_discoverable_ll():
    k = 'repository'
    d = Discoverable(repository=Organization)
    assert d.ll() == k


def test_discoverable_unhappy():
    k = 'repository'
    d = Discoverable(repository=Organization)

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
    d = Discoverable(repository=Organization)
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
    d = Discoverable(repository=Organization)

    departments = d.ls(['repository', 'departments'])
    assert departments[0].startswith('department')


def test_discoverable_show():
    d = Discoverable(repository=Organization)
    d.cd('repo')
    data = d.show(())
    assert data.values[0][0].startswith('Dep department_')
    assert data['#teams'][0] == 2

    d.cd('dep')
    items = d.ls()
    data = d.show(items[:1])
    assert data.values[0][0].startswith('Team t')
    assert data['#members'][0] == 2

    d.cd('d')
    data = d.show(())
    assert data.values[0][0].startswith('Team t')
    assert data['#members'][0] == 2


def test_discoverable_load_snapshot():
    fn = '.pytest.discoverable.pickle'
    path = ['repository', 'departments']

    d = Discoverable(repository=Organization)
    items = d.ls(path)

    d.snapshot(fn)

    d = Discoverable(repository=Organization)
    assert d.ls(path) == items

    # invalidating cache should result in mismatching data
    generate.cache_clear()

    d = Discoverable(repository=Organization)
    assert d.ls(path) != items

    d.load(fn)
    assert d.ls(path) == items
