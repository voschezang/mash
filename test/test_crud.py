import crud
from crud import Item

list_items = ['a', 'b', 'c']
dict_items = {'a': 1, 'b': 2, 'c': 3}


class CRUD(crud.CRUD):
    """A concrete implementation of the ABC crud.CRUD
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def ls_absolute(self, path=None):
        if path == ['']:
            return [Item(str(i), item) for i, item in enumerate(list_items)]

        return [Item(k, v) for k, v in dict_items.items()]


def init():
    return CRUD(path=[])


def test_ls():
    result = init().ls()
    result = init().ls()
    assert [r.name for r in result] == list(dict_items.keys())

    result = init().ls([''])
    assert [int(r.name) for r in result] == list(range(len(list_items)))
    assert [r.value for r in result] == list_items


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
    assert o.prev_path == ['a', 'b']  # TODO this should be ['a']


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
