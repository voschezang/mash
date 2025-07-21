
from pytest import raises
from mash.shell.errors import ShellTypeError
from mash.shell2.ast.term import Float, Integer, Term, Word


def test_ast_term():
    # Disable abstract method guards because Term is still an abstract class
    Term.__abstractmethods__ = {}

    a = Term('1')
    b = Term('1')
    c = Term('2')

    assert a.value == '1'
    assert b.value == '1'
    assert c.value == '2'

    assert a == b
    assert a != c


def test_ast_word():
    word = Word('abc')
    assert word.value == 'abc'
    assert str(word) == 'abc'
    assert repr(word) == 'abc'
    assert len(word) == 3

    assert word.run(None) == 'abc'


def test_ast_float():
    number = Float('10')
    assert number == 10

    number = Float('1.0')
    assert number == 1.0

    with raises(ShellTypeError):
        Integer(0.1)


def test_ast_int():
    number = Integer('2')
    assert number == 2
    assert number == Float(2)

    with raises(ShellTypeError):
        Integer(0.1)
