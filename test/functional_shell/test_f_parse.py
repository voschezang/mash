
from pytest import raises
from mash.functional_shell.ast.lines import Lines
from mash.functional_shell.ast.node import Node
from mash.functional_shell.parser import parse


def parse_line(text: str):
    return parse(text).values[0]


def test_parse_compile():
    parse('abc')


def test_parse_cmd():
    text = 'ab'
    result = parse(text)
    assert isinstance(result, Lines)
    assert result.values == ('ab',)
    assert isinstance(result.values[0], Node)


def test_parse_empty():
    assert parse('') is None

    result = parse('  ')
    assert result is None

    result = parse('\t  \t ')
    assert result is None


def test_parse_indented():
    text = '  ab'
    result = parse(text)
    assert isinstance(result, Lines)
    assert result.values == ('ab',)
