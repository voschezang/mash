
from pytest import raises
from mash.shell.errors import ShellTypeError
from mash.shell2.ast.term import Cast, Float, Integer, Term, Word


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
    assert Word.zero() == ''

    assert word.run(None) == 'abc'


def test_ast_wildcards():
    value = r'ab%c*'
    word = Word(value)
    assert word.value == value
    assert str(word) == value


# def test_ast_quotes():
#     value = ','
#     word = Word(value)
#     assert word.value == value
#     assert str(word) == '","'


def test_ast_float():
    number = Float('10')
    assert number == 10

    number = Float('1.0')
    assert number == 1.0


def test_ast_int():
    number = Integer('2')
    assert number == 2
    assert number == Float(2)

    number = Integer(0.1)
    assert number == 0


def test_ast_cast_int():
    # always round down
    result = Integer.cast(Float(0.99))
    assert result == 0

    with raises(ShellTypeError):
        Float.cast(Word('1'))


def test_ast_cast_float():
    result = Float.cast(Integer(10))
    assert result == 10.0

    with raises(ShellTypeError):
        Float.cast(Word('1'))


def test_ast_cast():
    result = Cast([Float, Integer], Float(0.5))
    assert result.casts == [Float, Integer]
    assert result.term == 0.5

    assert result.type == '(float) (int)'
    assert str(result) == '(float) (int) 0.5'
    assert Cast.zero().casts == []

    assert result.run({}) == 0

    with raises(ShellTypeError):
        Cast([Word], Float(1)).run({})
