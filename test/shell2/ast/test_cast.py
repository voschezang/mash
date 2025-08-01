from pytest import raises

from mash.shell.errors import ShellTypeError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.term import Cast, Float, Integer


def test_cast_int():
    cast = Cast(['int'], Float(1.1))

    assert isinstance(cast.copy(), Cast)
    assert cast.copy().casts == cast.casts

    assert cast.run({}) != '1'
    assert cast.run({}) == 1


def test_cast_word():
    cast = Cast(['text'], Float(1.1))
    assert cast.run({}) != 1.1
    assert cast.run({}) == '1.1'


def test_faulty_cast():
    cast = Cast(['text'], ArrayList([Float(1), Float(1)]))

    with raises(ShellTypeError):
        cast.run({})


def test_ast_double_cast():
    result = Cast(['float', 'int'], Float(0.5))
    assert result.casts == [Float, Integer]
    assert result.term == 0.5

    assert result.type == '(float) (int)'
    assert str(result) == '(float) (int) 0.5'
    assert Cast.zero().casts == []

    c = result.copy()
    assert c.casts == result.casts
    assert c.term == result.term
    assert c is not result

    assert result.run({}) == 0
