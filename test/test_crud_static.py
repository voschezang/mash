from pytest import raises

from crud_static import StaticCRUD
from crud_example import repository


def init():
    return StaticCRUD(repository)


def test_ls():
    crud = init()
    items = crud.ls()
    assert items[0].name == 'worlds'

    items = crud.ls('worlds')
    assert items[0].name == 'earth'

    items = crud.ls('w')
    assert items[0].name == 'earth'

    with raises(ValueError):
        crud.ls('0')


def test_cd():
    crud = init()

    assert crud.path == []

    crud.cd('w')
    assert crud.path == ['worlds']

    crud.cd('earth')
    assert crud.path == ['worlds', 0]


def test_cd_ls():
    crud = init()
    assert crud.path == []

    crud.cd('w')
    assert crud.path == ['worlds']

    assert crud.ls()[0].name == 'earth'

    crud.cd('earth')
    assert len(crud.ls('animals')) == 2

    # TODO
    # assert crud.ls('..') == []
