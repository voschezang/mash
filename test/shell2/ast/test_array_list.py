from pytest import raises

from mash.shell.errors import ShellTypeError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.node import Node
from mash.shell2.ast.term import Float, Integer, Word


def test_list_init():
    ArrayList(ArrayList, [])
    ArrayList(Float, [])
    ArrayList(Integer, [])
    ArrayList(Word, [])

    array = ArrayList.empty()
    assert array.items == []


def test_list_numbers():
    # assert ArrayList.zero().items == []
    numbers = ArrayList(Float, [Integer(1), Float(0.1), Integer(2)])

    assert numbers.items == [1, 0.1, 2]
    assert str(numbers) == '[1.0, 0.1, 2.0]'
    assert len(numbers) == 3
    assert numbers.type == '[float]'

    for i in numbers.items:
        assert isinstance(i, Float)


def test_list_comparisons():
    # empty lists evaluate to False, but are not the same als the literal False
    assert not ArrayList.zero()
    assert ArrayList.zero() != False

    # nonempty lists evaluate to True
    assert ArrayList(Integer, [1]) and True

    # lists of different types are not equal
    assert ArrayList(Integer, [1]) != ArrayList(Float, [1])

    # comparisons with zero are lenient
    assert ArrayList.zero() == ArrayList(Float, [])
    assert ArrayList.zero() == ArrayList(Integer, [])
    assert ArrayList.zero() == ArrayList(Word, [])

    # comparisons with Python types are illegal
    with raises(ShellTypeError):
        ArrayList.zero() == []


def test_list_words():
    words = ArrayList(Word, [Word('ab'), Word('cd')])

    assert words.items == ['ab', 'cd']
    assert str(words) == '[ab, cd]'
    assert len(words) == 2


def test_mixed_list():
    with raises(ShellTypeError):
        ArrayList(Integer, [Integer(1), Word('a')])


def test_nested_list():
    inner = ArrayList(Float, [Integer(1), Float(0.1), Integer(2)])
    outer = ArrayList(ArrayList, [inner, inner])

    assert len(outer) == 2
    assert str(outer) == '[[1.0, 0.1, 2.0], [1.0, 0.1, 2.0]]'
    assert outer.type == '[[float]]'

    for i in outer.items:
        assert isinstance(i, ArrayList)

    inner = ArrayList(ArrayList, [[]])
