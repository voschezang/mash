import src.crud

items = ['a', 'b', 'c']


class CRUD(src.crud.CRUD):
    def __init__(self, **kwds):
        super().__init__(**kwds)

    def ls(self):
        return items


def init():
    return CRUD(path=[])


def test_ls():
    init().ls() == items


def test_cd_single_folder():
    assert init().path == []

    o = init()
    assert o.prev_path == []

    o.cd('a')
    assert o.path == ['a']
    assert o.prev_path == []


def test_cd_multiple_folders():
    o = init()
    o.cd('a')
    o.cd('b', 'c')
    assert o.path == ['a', 'b', 'c']
    assert o.prev_path == ['a', 'b']  # TODO this is not intuitive


def test_cd_special():
    o = init()
    o.cd('a', 'b')
    assert o.path == ['a', 'b']

    o.cd()
    assert o.path == []

    o.cd('-')
    assert o.path == ['a', 'b']

    o.cd('.')
    assert o.path == ['a', 'b']

    o.cd('..')
    assert o.path == ['a']
    assert o.prev_path == ['a', 'b']

    o.cd('-')
    assert o.path == ['a', 'b']
    assert o.prev_path == ['a']
