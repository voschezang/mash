from pytest import raises
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.node import Node


def test_ast_lines():
    lines = Lines(Command('print', 'hello'),
                  Command('print', 'world'))

    assert lines.values[0] == Command('print', 'hello')
    assert lines.values[1] == Command('print', 'world')
    assert str(lines) == 'print hello \n print world'


def test_run_lines():
    lines = Lines(Command('print', 'hello'))

    with raises(NotImplementedError):
        lines.run(None)
