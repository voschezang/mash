from logging import getLogger

from pytest import raises

from mash import io_util
from mash.shell.errors import ShellSyntaxError, ShellTypeError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.term import Boolean, Cast, Float, Integer, Word
from mash.shell2.ast.variable import Variable
from mash.shell2.parser import parse


def parse_line(text: str):
    lines = parse(text)
    assert isinstance(lines, Lines)

    return lines.items[0]


def test_parse_compile():
    parse('abc')


def test_parse_warnings():
    # ensure there are no warnings
    log = getLogger()
    log.setLevel(1)
    result = io_util.catch_all_output('abc', parse)
    assert result == ('', '')


def test_parse_warnings_output():
    parse('abc')
    fn = 'src/mash/shell2/parser.out'
    out = io_util.run_subprocess(r'grep "WARNING:\s\w" ' + fn)

    for line in out.stdout.decode().splitlines():
        if line == 'WARNING: Conflicts:':
            continue
        assert 'resolved' in line


def test_parse_empty():
    assert parse('') is None

    result = parse('  ')
    assert result is None

    result = parse('\t  \t ')
    assert result is None


def test_parse_command():
    result = parse('print')
    assert isinstance(result, Lines)

    terms = result.items[0]
    assert isinstance(terms, Command)
    assert terms.f == 'print'


def test_parse_command_with_args():
    text = 'print ok or not ok'
    result = parse(text)

    assert isinstance(result, Lines)

    command = result.items[0]
    assert isinstance(command, Command)
    assert command.f == 'print'
    assert command.f == Word('print')

    assert command.args == ('ok', 'or', 'not', 'ok')


def test_parse_command_variable():
    result = parse('print $abc xyz')
    assert isinstance(result, Lines)
    terms = result.items[0]

    assert isinstance(terms, Command)
    assert terms.args[0] == Variable('abc')
    assert terms.args[1] == Word('xyz')


def test_parse_list_int():
    text = '[1, 2, 3]'
    lines = parse(text)
    assert isinstance(lines, Lines)
    result = lines.items[0]
    assert isinstance(result, ArrayList)
    assert result.items == [1, 2, 3]
    assert result.child_types == [Variable]


def test_parse_mixed_list():
    text = '[1.5, abc, 1]'
    lines = parse(text)
    assert isinstance(lines, Lines)
    result = lines.items[0]
    assert isinstance(result, ArrayList)
    assert result.items == [1.5, 'abc', 1]
    assert result.child_types == [Variable]


def test_parse_empty_list():
    result = parse('[]').items[0]
    assert isinstance(result, ArrayList)
    assert result.items == []


def test_parse_nested_list():
    text = '[ [[1], [2]], []]'

    lines = parse(text)
    assert isinstance(lines, Lines)

    result = lines.items[0]
    assert isinstance(result, ArrayList)
    assert result.items[0] == ArrayList([[Integer(1)], [Integer(2)]])
    assert result.items[1] == ArrayList([])
    assert result.child_types == [ArrayList, ArrayList, Variable]
    assert result.type == '[[[variable]]]'
