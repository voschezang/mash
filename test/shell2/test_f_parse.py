from logging import getLogger

from pytest import raises

from mash import io_util
from mash.shell.errors import ShellSyntaxError, ShellTypeError
from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.term import Cast, Float, Integer, Word
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
    out = io_util.run_subprocess(r'grep "WARNING:\s\w" ' + fn)
    out = out.stdout.decode()

    for line in out.splitlines():
        if line == 'WARNING: Conflicts:':
            continue
        assert 'resolved' in line


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


def test_parse_empty():
    assert parse('') is None

    result = parse('  ')
    assert result is None

    result = parse('\t  \t ')
    assert result is None


def test_parse_indented():
    result = parse('  ab cd  ef')

    assert isinstance(result, Lines)
    terms = result.items[0]

    assert isinstance(terms, Command)
    assert terms.f == 'ab'
    assert terms.args == ('cd', 'ef')


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
