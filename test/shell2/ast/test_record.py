
from pytest import raises
from mash.shell.errors import ShellError
from mash.shell2.ast.record import Record
from mash.shell2.ast.term import Integer, Word
from mash.shell2.ast.variable import Variable


def test_init_record():
    data = Record((Word('x'), Integer(1)),
                  (Word('y'), Integer(2)))

    assert str(data) == '{x: 1, y: 2}'
    assert data.type == '{x: int, y: int}'


def test_run_record():
    data = Record((Word('x'), Variable('y')))
    updated = data.run({'y': 10})

    assert updated.data['x'] == 10

    with raises(ShellError):
        data.run({'z': 10})


def test_compare_record():
    data = Record((Word('x'), Integer(1)),
                  (Word('y'), Integer(2)))

    assert data == data
    assert data.run({}) == data

    updated = data.copy()
    updated.data['x'] = Integer(2)

    assert data == data

    updated.data['x'] = Integer(20)

    assert data != updated
