from pytest import raises

from mash.shell.errors import ShellTypeError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.term import Float, Integer, Word


def test_list_numbers():
    ints = ArrayList(Float, [Integer(1), Float(0.1), Integer(2)])

    assert ints.items == [1, 0.1, 2]
    assert str(ints) == '[1, 0.1, 2]'

    for i in ints.items:
        assert isinstance(i, Float)


def test_mixeded_list():
    with raises(ShellTypeError):
        ArrayList(Integer, [Integer(1), Word('a')])
