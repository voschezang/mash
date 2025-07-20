
from logging import getLogger
from mash import io_util
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.term import Word
from mash.shell2.ast.variable import Variable
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


def test_parse_command():
    text = 'print'
    result = parse(text)
    assert isinstance(result, Lines)

    terms = result.values[0]
    assert isinstance(terms, Command)
    assert terms.f == 'print'


def test_parse_command_with_args():
    text = 'print ok or not ok'
    result = parse(text)

    assert isinstance(result, Lines)

    command = result.values[0]
    assert isinstance(command, Command)
    assert command.f == 'print'
    assert command.f == Word('print')

    assert command.args == ('ok', 'or', 'not', 'ok')


def test_parse_empty():
    assert parse('') is None

    result = parse('  ')
    assert result is None

    result = parse('\t  \t ')
    assert result is None


def test_parse_indented():
    text = '  ab cd  ef'
    result = parse(text)
    assert isinstance(result, Lines)
    terms = result.values[0]

    assert isinstance(terms, Command)
    assert terms.f == 'ab'
    assert terms.args == ('cd', 'ef')


def test_parse_command_variable():
    text = 'print $abc xyz'
    result = parse(text)
    assert isinstance(result, Lines)
    terms = result.values[0]

    assert isinstance(terms, Command)
    assert terms.args[0] == Variable('abc')
    assert terms.args[1] == Word('xyz')
