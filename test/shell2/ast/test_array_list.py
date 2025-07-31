from pytest import raises

from mash.shell.errors import ShellTypeError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.term import Float, Integer, Word
from mash.shell2.ast.variable import Variable


def test_list_init():
    ArrayList([], Float)

    array = ArrayList.empty()
    assert array.items == []
    assert array.type == '[variable]'


def test_list_numbers():
    numbers = ArrayList([Integer(1), Float(0.1), Integer(2)])

    assert numbers.items == [1, 0.1, 2]
    assert str(numbers) == '[1, 0.1, 2]'
    assert len(numbers) == 3
    assert numbers.type == '[variable]'

    result = numbers.run({})

    assert isinstance(result, ArrayList)
    assert result.type == '[int]'

    for i in result.items:
        assert isinstance(i, Integer)


def test_list_variables():
    numbers = ArrayList([Float(1), Variable('x')])

    assert numbers.type == '[variable]'

    result = numbers.run({'x': Float(2)})

    assert result.items == [1, 2]
    assert result.type == '[float]'


def test_list_comparisons():
    # empty lists evaluate to False, but are not the same als the literal False
    assert not ArrayList.zero()
    assert ArrayList.zero() != False

    # nonempty lists evaluate to True
    assert ArrayList([Integer(1)], Integer) and True

    # lists of different types are not equal
    assert ArrayList([Integer(1)], Integer) != ArrayList([Float(1)], Float)

    # comparisons with zero are lenient
    assert ArrayList.zero() == ArrayList([], Float)
    assert ArrayList.zero() == ArrayList([], Integer)
    assert ArrayList.zero() == ArrayList([], Word)

    # comparisons with Python types are illegal
    with raises(ShellTypeError):
        ArrayList.zero() == []


def test_list_words():
    words = ArrayList([Word('ab'), Word('cd')], Word)

    assert words.items == ['ab', 'cd']
    assert str(words) == '[ab, cd]'
    assert len(words) == 2


def test_mixed_list():
    with raises(ShellTypeError):
        ArrayList([Integer(1), Word('a')], Integer)


def test_nested_list():
    inner = ArrayList([Integer(1), Float(0.1), Integer(2)], Float)
    outer = ArrayList([inner, inner], ArrayList)

    assert len(outer) == 2
    assert str(outer) == '[[1.0, 0.1, 2.0], [1.0, 0.1, 2.0]]'
    assert outer.type == '[[float]]'

    for i in outer.items:
        assert isinstance(i, ArrayList)

    inner = ArrayList([[]])

    inner = ArrayList([Integer(1), Float(0.1), Integer(2)], Float)
