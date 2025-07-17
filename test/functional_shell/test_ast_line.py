from mash.functional_shell.ast.lines import Lines
from mash.functional_shell.ast.node import Node


def test_ast_lines():
    lines = Lines(Node('abc'), Node('def'))

    assert lines.values == ('abc', 'def')
    assert str(lines) == 'abc\ndef'
    assert repr(lines) == "Lines( 'abc\\ndef' )"


def test_run_lines():
    lines = Lines(Node('print hello'))
    # TODO
    # result = lines.run(None)
    # assert result == 'hello
