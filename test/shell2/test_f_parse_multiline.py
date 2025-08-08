from pytest import raises

from mash.shell.errors import ShellSyntaxError
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.multiline import Function, IfElse
from mash.shell2.ast.variable import Variable
from mash.shell2.parser import parse
from mash.shell2.pre_parser import tokenize


def test_parse_multiline():
    text = """foo
bar
"""
    lines = parse(text)
    assert isinstance(lines, Lines)

    assert len(lines.items) == 2


def test_parse_indented():
    with raises(ShellSyntaxError):
        parse('  ab cd  ef')


def test_parse_multiline_if_else():
    text = """
if a:
    run
    run more
else:
    walk
"""
    lines = parse(text)
    assert isinstance(lines, Lines)

    condition = lines.items[0]
    assert isinstance(condition, IfElse)
    assert isinstance(condition.condition, Command)
    assert condition.condition.f == 'a'

    assert isinstance(condition.then, Lines)
    assert condition.then.items[0].f == 'run'
    assert condition.then.items[1].args == ('more',)

    assert isinstance(condition.otherwise, Lines)
    assert condition.otherwise.items[0].f == 'walk'


def test_parse_function_definition():
    text = """
f ($x $y $z):
    return $x
"""
    lines = parse(text)
    assert isinstance(lines, Lines)

    fun = lines.items[0]
    assert isinstance(fun, Function)
    assert fun.name == 'f'
    assert isinstance(fun.args[0], Variable)
    assert fun.args[0].value == 'x'
    assert fun.args[1].value == 'y'
    assert fun.args[2].value == 'z'

    assert isinstance(fun.body, Lines)
