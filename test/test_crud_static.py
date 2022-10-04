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
