from mash import io_util
from mash.filesystem.filesystem import FileSystem, cd
from mash.filesystem.scope import Scope, show

ENV = 'env'


def init() -> Scope:
    fs = FileSystem({})
    return Scope(fs)


def test_env_setitem():
    env = init()
    assert env.keys() == []

    env['a'] = 1
    assert 'a' in env.data.ls(ENV)
    assert 'a' in env

    assert env.data.get([ENV, 'a']) == 1


def test_env_getitem():
    env = init()

    with cd(env.data, ENV):
        env.data.set('a', 1)

    assert env['a'] == 1


def test_env_contains():
    env = init()

    assert 'a' not in env
    env['a'] = 1
    assert 'a' in env


def test_env_delitem():
    env = init()

    env['a'] = 1
    del env['a']
    assert 'a' not in env


def test_env_keys():
    env = init()
    keys = ['a', 'b']
    for k in keys:
        env[k] = 1

    assert env.keys() == keys


def test_env_cd_in_FileSystem():
    env = init()
    fs = env.data
    fs.set('dir', {})
    env['a'] = 1
    assert fs.ls() == [ENV, 'dir']
    assert fs.ls('env') == ['a']

    fs.cd('dir')
    assert fs.ls() == []
    fs.set(ENV, {})
    assert fs.ls() == [ENV]
    assert fs.ls('env') == []

    env['b'] = 2
    assert fs.ls('env') == ['b']
    assert env.keys() == ['b', 'a']
    assert env['a'] == 1
    assert env['b'] == 2
    assert fs.ls('env') == ['b']

    fs.cd()
    assert fs.ls('env') == ['a']


def test_env_show():
    env = init()
    env['a'] = 1
    assert 'a' in io_util.catch_output(env, show)
