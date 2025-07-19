
from logging import getLogger
from mash import io_util
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.term import Term, Word
from mash.shell2.ast.terms import Terms
from mash.shell2.parser import parse


def parse_line(text: str):
    return parse(text).values[0]


def test_parse_compile():
    parse('abc')


def test_parse_warnings():
    # ensure there are no warnings
    log = getLogger()
    log.setLevel(1)
    result = io_util.catch_all_output('abc', parse)
    assert result == ('', '')

# def test_parse_warnings():


def test_parse_command():
    text = 'print'
    result = parse(text)
    assert isinstance(result, Lines)

    terms = result.values[0]
    assert isinstance(terms, Command)
    assert terms.f == 'print'


def test_parse_terms():
    text = 'print ok'
    result = parse(text)

    assert isinstance(result, Lines)

    command = result.values[0]
    assert isinstance(command, Command)
    assert command.f == 'print'
    assert command.args == [Word('ok')]


def test_parse_empty():
    assert parse('') is None

    result = parse('  ')
    assert result is None

    result = parse('\t  \t ')
    assert result is None


def test_parse_indented():
    text = '  ab cd  '
    result = parse(text)
    assert isinstance(result, Lines)
    terms = result.values[0]

    assert isinstance(terms, Command)
    assert terms.f == 'ab'
    assert terms.args == ['cd']
