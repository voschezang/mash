from copy import deepcopy
from pytest import raises

from mash.filesystem import FileSystem, Option, OPTIONS
from mash.filesystem.filesystem import cd

root = {'a': {'1': '1', '2': 2, '3': ['A', 'B', 10, 20, [30]]},
        'b': [{'1': '1'}, {'2': 2}],
        'c': {'a_long_name': True}
        }
keys = ['a', 'b', 'c']
inner_keys = ['1', '2', '3']
list_values = ['A', 'B', 10, 20, [30]]
indices_a = [0, 1, 2, 3, 4]
indices_b = [0, 1]


def init(**kwds):
    return FileSystem(deepcopy(root), **kwds)


def test_Option():
    for op in OPTIONS:
        assert Option.verify(op)

    assert not Option.verify('=')
    assert not Option.verify('$')

    assert Option('..') == Option.up
    assert Option('~') == Option.home
    assert Option.default == Option.home


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


def test_get_fuzzy():
    d = init()

    assert d.get(['abc', '1']) == '1'
    assert d.get(['c', 'a_long_n'])

    with raises(ValueError):
        d.get(['Z'])


def test_get_unhappy():
    d = init()
    with raises(ValueError):
        d.get(['def'])

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
    assert value == d.get(path + [3])

    with raises(ValueError):
        d.get(['a', '3', 10])


def test_getitem():
    d = init()
    assert d['a'] == d.get('a')


def test_set():
    d = init()
    assert 'x' not in d.ls()

    d.set('x', 10)
    assert 'x' in d.ls()
    assert d.get('x') == 10


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


def test_ll():
    d = init()
    assert d.ll('a') == '\n'.join(inner_keys)
    assert d.ll('a', '3', delimiter=', ') == 'A, B, 10, 20, [30]'

    assert d.ll('a', '3', delimiter=', ',
                include_list_indices=True) == '0: A, 1: B, 2: 10, 3: 20, 4: [30]'

    assert d.ll('b', delimiter=',') == "{'1': '1'},{'2': 2}"
    assert d.ll('b', 0, delimiter=',') == '1'
    assert d.ll('b', 0, '1', delimiter=',') == '1'

    with raises(ValueError):
        d.ll('b', 0, '1', '1')

    with raises(ValueError):
        d.ll('b', 0, '1', 1)


def test_cd_a():
    d = init()
    assert d.path == []

    k = 'a'
    d.cd(k)
    assert d.path == [k]
    assert list(d.ls()) == inner_keys
    assert d.ll(delimiter=',') == ','.join(inner_keys)

    d.cd()
    assert d.path == []
    assert d.prev.path == [k]


def test_cd_b():
    d = init()
    assert d.path == []

    k = 'b'
    d.cd(k)
    assert d.path == [k]
    assert list(d.ls()) == indices_b
    assert d.ll(delimiter=',') == "{'1': '1'},{'2': 2}"


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

    path = ['a', '3']
    d.cd(*path)
    assert d.path == path
    assert d.ls() == indices_a

    # cd into file should fail
    with raises(ValueError):
        d.cd(0)

    d.cd()
    assert d.path == []

    path = ['a', '3', 4]
    d.cd(*path)
    assert d.path == path

    d.cd('.')
    assert d.path == path

    d.cd('..')
    assert d.path == path[:-1]
    assert d.ls() == indices_a

    d.cd('-')
    assert d.path == path
    assert d.ls() == [0]

    d.cd('...')
    assert d.path == path[:-2]
    assert d.ls() == inner_keys

    d.cd('-')
    d.cd('....')
    assert d.path == []
    assert d.ls() == keys


def test_cd_up_down():
    d = init()

    path = ['a', '3']
    d.cd(*path)
    assert d.path == path

    d.cd('..')
    assert d.path == ['a']

    d.cd('3')
    assert d.path == path

    d.cd('...')
    assert d.path == []

    d.cd(*path)
    assert d.path == path


def test_copy():
    d = init()
    e = d.copy()
    e.cd('a')
    assert d.path != e.path
    assert e.path == ['a']


def test_simulate_cd():
    d = init()
    d.cd('a')
    view = d.simulate_cd('3', relative=True)
    assert view.path == ['a', '3']
    view = d.simulate_cd(['..'], relative=True)
    assert view.path == []
    view = d.simulate_cd(['..', 'a', '3'], relative=True)
    assert view.path == ['a', '3']
    view = d.simulate_cd(['..', 'a', '3', '..'], relative=True)
    assert view.path == ['a']


def test_ls_after_cd():
    d = init()
    path = ['a', '3']
    d.cd(*path)
    assert d.ls() == indices_a


def test_ls_up():
    d = init()
    path = ['a', '3']
    d.cd(*path)
    assert d.get('..') == root['a']
    assert d.ls('..') == inner_keys
    assert d.ls('...') == keys
    assert d.ls(['..', '..', '.']) == keys
    assert d.ls(['...'] + path) == indices_a
    assert d.ls(['...'] + path + ['..']) == inner_keys


def test_cd_home():
    d = init()
    assert d.in_home()
    assert d.path == []

    d.cd('a')
    assert d.in_home()
    assert d.path == ['a']
    assert d.full_path == ['/', 'a']

    d._home = ['b']
    assert not d.in_home()
    assert d.path == ['/', 'a']

    d.cd('~')
    assert d.path == []
    assert d.full_path == ['/', 'b']

    d.cd('-')

    d.cd('3')
    assert d.path == ['/', 'a', '3']

    with raises(ValueError):
        d.cd('a')

    d.cd()
    assert d.path == []
    assert d.full_path == ['/', 'b']

    d.cd('/')
    assert d.path == ['/']
    assert d.full_path == ['/']


def test_foreach():
    d = init()
    result = d.foreach(['a', '3'])
    assert len(result) == 5
    assert ['a', '3', 0] in result
    assert ['a', '3', 4] in result


def test_set_home():
    d = init(home=['a'])
    assert d.path == []
    assert d.full_path == ['/', 'a']

    assert d.ls() == inner_keys
    d.cd('..')
    assert d.path == ['/']
    assert d.full_path == ['/']

    d.cd()
    assert d.path == []
    assert d.full_path == ['/', 'a']


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

    a = d.get('a')
    d.mv('a', 'c')
    assert d.get(['c']) == a
    assert 'a' not in d


def test_mv_to():
    d = init()

    a = d.get('a')
    d.mv('a', 'a', 'c')
    assert d.get(['c', 'a']) == a


def test_rm():
    d = init()
    assert 'a' in d.ls()

    d.rm('a')
    assert 'a' not in d.ls()


def test_with_cd():
    d = init()
    d.cd('a')
    assert d.full_path == ['/', 'a']

    with cd(d, '3'):
        assert d.full_path == ['/', 'a', '3']

    assert d.full_path == ['/', 'a']

    with cd(d, '3'):
        d.cd('/')

    assert d.full_path == ['/', 'a']


def test_with_cd_multiple_keys():
    d = init()
    assert d.full_path == ['/']

    keys = ['a', '3']
    with cd(d, *keys):
        assert d.full_path == ['/'] + keys

    assert d.full_path == ['/']
