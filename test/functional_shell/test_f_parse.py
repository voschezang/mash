
from mash.functional_shell import tokenizer
from mash.functional_shell.ast.lines import Lines
from mash.functional_shell.parser import parse


def parse_line(text: str):
    return parse(text).values[0]


def test_parse_compile():
    parse('abc')


def test_parse_cmd():
    text = 'ab'
    result = parse(text)
    assert isinstance(result, Lines)
    assert result.values == ['ab']


def test_parse_empty():
    result = parse('')
    assert isinstance(result, Lines)
    assert isinstance(result, Lines)
    assert result.values == []

    result = parse('  ')
    assert isinstance(result, Lines)
    assert isinstance(result, Lines)
    assert result.values == []

    result = parse('\t  \t ')
    assert isinstance(result, Lines)
    assert isinstance(result, Lines)
    assert result.values == []


def test_parse_indented():
    text = '  ab'
    result = parse(text)
    assert isinstance(result, Lines)
    assert result.values == ['ab']
