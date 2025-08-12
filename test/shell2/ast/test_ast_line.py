from pytest import raises
from mash.shell.errors import ShellError
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.term import Word


def test_ast_lines():
    lines = Lines(Command(Word('print'), Word('hello')),
                  Command(Word('print'), Word('world')))

    assert lines.items[0] == Command(Word('print'), Word('hello'))
    assert lines.items[1] == Command(Word('print'), Word('world'))

    s = '(Command) print'
    assert str(lines) == f'(Lines) {s} hello\n{s} world'


def test_run_lines():
    lines = Lines(Command(Word('print'), Word('hello')))
    lines.run({})

    lines = Lines(Command(Word('abc'), Word('def')))
    with raises(ShellError):
        lines.run({})
