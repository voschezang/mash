
from collections import defaultdict
from mash.filesystem.filesystem import FileSystem, cd
from mash.shell.env import ENV, Environment


def init():
    fs = FileSystem({})
    return Environment(fs)


def test_setitem():
    env = init()
    assert env.keys() == []

    env['a'] = 1
    assert 'a' in env.data.ls(ENV)
    assert 'a' in env

    assert env.data.get([ENV, 'a']) == 1


def test_getitem():
    env = init()

    with cd(env.data, ENV):
        env.data.set('a', 1)

    assert env['a'] == 1


def test_contains():
    env = init()

    assert 'a' not in env
    env['a'] = 1
    assert 'a' in env


def test_delitem():
    env = init()

    env['a'] = 1
    del env['a']
    assert 'a' not in env


def test_keys():
    env = init()
    keys = ['a', 'b']
    for k in keys:
        env[k] = 1

    assert env.keys() == keys
