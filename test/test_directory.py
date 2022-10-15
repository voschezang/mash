from copy import deepcopy
from pytest import raises

from directory import Directory

root = {'a': {'1': '1', '2': 2, '3': ['A', 'B', 10, 20]},
        'b': [{'1': '1'}, {'2': 2}],
        'c': None
        }
keys = ['a', 'b', 'c']
inner_keys = ['1', '2', '3']
list_values = ['A', 'B', 10, 20]
indices_a = [0, 1, 2, 3]
indices_b = [0, 1]


def init():
    return Directory(deepcopy(root))


def test_get_exact():
    d = init()
    assert list(d.get('a')) == inner_keys
    assert list(d.get(['a'])) == inner_keys
    assert d.get(['a', '1']) == '1'
    assert d.get(['a', '2']) == 2
    assert d.get(['a', '3']) == list_values

    assert d.get(['b', 0]) == {'1': '1'}
    assert d.get(['b', 0, '1']) == '1'
    assert d.get(['b', 1, '2']) == 2


def test_get_unhappy():
    d = init()
    with raises(ValueError):
        d.get(['abc'])

    with raises(ValueError):
        d.get([0])

    with raises(TypeError):
        d.get(0)


def test_get_index():
    d = init()
    value = 'A'
    assert d.get(['a', '3', value]) == value

    value = 20
    path = ['a', '3']
    assert value in d.get(path)
    assert value == d.get(path + [-1])
    with raises(ValueError):
        d.get(['a', '3', 10])


def test_ls():
    d = init()
    assert d.ls() == keys
    assert d.ls(['a']) == inner_keys
    assert d.ls('a') == inner_keys
    assert d.ls('a', 'a') == inner_keys + inner_keys
    assert d.ls('a', 'b') == inner_keys + indices_b

    assert d.ls(['a', '1']) == ['1']
    assert d.ls(['a', '2']) == [2]
    assert d.ls(['a', '3']) == indices_a
    assert d.ls(['a', '3', 0]) == ['A']

    assert d.ls(['b', 0]) == ['1']


def test_cd():
    d = init()
    assert d.path == []

    k = 'a'
    d.cd(k)
    assert d.path == [k]
    assert list(d.ls()) == inner_keys

    d.cd()
    assert d.path == []
    assert d.prev.path == [k]


def test_cd_switch():
    d = init()
    assert d.path == []
    assert d.state.path == []
    assert d.prev.path == []

    d.cd('b')
    assert d.path == ['b']
    assert list(d.ls()) == indices_b
    assert d.prev.path == []

    d.cd('-')
    assert d.path == []
    assert d.state.path == []
    assert d.prev.path == ['b']


def test_cd_up():
    d = init()

    path = ['a', '3', 0]
    d.cd(*path)
    assert d.path == path

    d.cd('.')
    assert d.path == path

    d.cd('..')
    assert d.path == path[:-1]

    d.cd('-')
    assert d.path == path

    d.cd('...')
    assert d.path == path[:-2]

    d.cd('-')
    d.cd('....')
    assert d.path == []


def test_cp_single():
    d = init()

    d.cp('a', 'A')
    assert d.ls('a') == d.ls('A')

    with raises(ValueError):
        d.cp()

    with raises(ValueError):
        d.cp('a')


def test_cp_multi():
    d = init()

    d.cp('a', 'b', 'c')
    assert d.get(['c', 'a']) == d.get('a')
    assert d.get(['c', 'b']) == d.get('b')


def test_mv_rename():
    d = init()

    a = d['a']
    d.mv('a', 'c')
    assert d.get(['c']) == a
    assert 'a' not in d


def test_mv_to():
    d = init()

    a = d['a']
    d.mv('a', 'a', 'c')
    assert d.get(['c', 'a']) == a
