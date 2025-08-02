from logging import getLogger

from pytest import raises

from mash.shell.errors import ShellSyntaxError, ShellTypeError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.term import Boolean, Cast, Float, Integer, Word
from mash.shell2.ast.variable import Variable
from mash.shell2.parser import parse


def parse_line(text: str):
    lines = parse(text)
    assert isinstance(lines, Lines)

    return lines.items[0]


def test_parse_bool():
    lines = parse('true')
    assert isinstance(lines, Lines)
    result = lines.items[0]
    assert isinstance(result, Boolean)
    assert result.value

    lines = parse('false')
    assert isinstance(lines, Lines)
    result = lines.items[0]
    assert isinstance(result, Boolean)
    assert not result.value


def test_parse_number():
    term = parse_line('1')
    assert isinstance(term, Integer)
    assert term.value == 1

    term = parse_line('0.1')
    assert isinstance(term, Float)
    assert term.value == 0.1


def test_parse_variable():
    var = parse_line('$abc')
    assert isinstance(var, Variable)
    assert var.value == 'abc'


def test_parse_cast_int():
    lines = parse('(int) 1.1')
    assert isinstance(lines, Lines)
    cast = lines.items[0]
    assert isinstance(cast, Cast)
    assert cast.casts == [Integer]
    assert cast.term == 1.1

    with raises(ShellSyntaxError):
        parse('($x) 1')

    with raises(ShellTypeError):
        parse('(nothing) 1.1')


def test_parse_cast_word():
    lines = parse('(text) 1.1')
    cast = lines.items[0]

    assert isinstance(cast, Cast)
    assert cast.casts == [Word]
    assert cast.term == 1.1


def test_parse_cast_list():
    lines = parse('(int) [1.1]')
    cast = lines.items[0]

    assert isinstance(cast, Cast)
    assert cast.casts == [Integer]
    assert cast.term == ArrayList([Float(1.1)])


def test_parse_command_cast():
    lines = parse('print (text) 1.1')
    command = lines.items[0]
    cast = command.args[0]

    assert isinstance(cast, Cast)
    assert cast.casts == [Word]
    assert cast.term == 1.1


def test_parse_double_cast():
    lines = parse('(float) (int) 0.5')
    cast = lines.items[0]

    assert isinstance(cast, Cast)
    assert cast.casts == [Integer, Float]
    assert cast.term == 0.5


def test_parse_cast_nested():
    lines = parse('print (float) [1, (int) 2.1]')
    command = lines.items[0]
    outer_cast = command.args[0]

    assert isinstance(outer_cast, Cast)
    assert outer_cast.casts == [Float]

    array = outer_cast.term
    assert isinstance(array, ArrayList)
    assert array.items[0] == 1

    cast = array.items[1]
    assert isinstance(cast, Cast)
    assert cast.casts == [Integer]
    assert cast.term == 2.1


def test_error_hints():
    with raises(ShellSyntaxError):
        parse('$x $x')
