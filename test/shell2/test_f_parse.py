from logging import getLogger

from pytest import raises

from mash import io_util
from mash.shell.errors import ShellSyntaxError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.term import Cast, Word
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


def test_parse_warnings_output():
    parse('')
    fn = 'src/mash/shell2/parser.out'
    out = io_util.run_subprocess(f'grep "WARNING:\s\w" {fn}')
    out = out.stdout.decode()

    for line in out.splitlines():
        if line == 'WARNING: Conflicts:':
            continue
        assert 'resolved' in line


def test_parse_command():
    text = 'print'
    result = parse(text)
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
    terms = result.items[0]

    assert isinstance(terms, Command)
    assert terms.f == 'ab'
    assert terms.args == ('cd', 'ef')


def test_parse_command_variable():
    text = 'print $abc xyz'
    result = parse(text)
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


def test_parse_cast_int():
    text = '(int) 1.1'
    text = 'print (int) 1.1'
    lines = parse(text)
    assert isinstance(lines, Lines)
    result = lines.items[0]
    assert isinstance(result, Command)
    cast = result.args[0]
    assert isinstance(cast, Cast)
    assert cast.casts == ('int',)
    assert cast.term == 1.1


def test_parse_faulty_cast():
    text = '(int) 1.1'
    with raises(ShellSyntaxError):
        parse(text)


def test_parse_cast_word():
    text = 'print (word) 1.1'
    lines = parse(text)
    command = lines.items[0]
    cast = command.args[0]

    assert isinstance(cast, Cast)
    assert cast.casts == ('word',)
    assert cast.term == 1.1


def test_parse_double_cast():
    text = '(float) (int) 0.5'


def test_parse_cast_nested():
    text = '[1, (int) 2.1]'
