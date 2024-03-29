from pytest import raises

from examples.discoverable import Organization
from mash.filesystem.discoverable import Discoverable, observe


def init():
    return Discoverable(repository=Organization,
                        get_value_method=observe)


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
    d = init()

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

    # default value
    d.cd('t')
    assert d.get('name') == ''

    member = d.get('first_member')
    assert member['value'] == 100
    d.cd('-')

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


def test_discoverable_cd_after_ls():
    k = 'repository'
    d = init()

    d.cd(k)
    k = 'departments'
    d.ls(['departments', 'd', 'teams', 't'])
    d.cd('departments', 'd', 'teams', 't')
    team = d.ls()
    assert team == ['members', 'name', 'first_member']


def test_discoverable_ls_double():
    d = init()

    departments = d.ls(['repository', 'departments'])
    assert departments[0].startswith('department')


def test_discoverable_reset():
    d = init()
    path = ['repository', 'departments']
    d.cd(*path)
    items = d.ls()

    d.cd(items[0])
    inner_items = d.ls()
    d.cd('-')

    d.reset()
    new_items = d.ls()
    assert new_items != items

    d.cd(new_items[0]) != inner_items

    # verify that the prev working directory is reset
    d.cd('-')


def test_discoverable_show():
    d = init()
    d.cd('repo')
    data = d.show(())
    item = next(iter(data.values()))
    assert item['name'].startswith('Dep department_')
    assert item['#teams'] == 2

    d.cd('dep')
    items = d.ls()
    data = d.show(items[0])
    item = next(iter(data.values()))
    assert item['name'].startswith('Team t_')
    assert item['#members'] == 2

    d.cd('d')
    data = d.show(())
    item = next(iter(data.values()))
    assert item['name'].startswith('Team t')
    assert item['#members'] == 2


def test_discoverable_load_snapshot():
    fn = '.pytest.discoverable.pickle'
    path = ['repository', 'departments']

    d = init()
    items = d.ls(path)

    d.snapshot(fn)

    d = init()
    assert d.ls(path) != items

    d.load(fn)
    assert d.ls(path) == items
