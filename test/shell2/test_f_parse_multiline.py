from pytest import raises

from mash.shell2.ast.lines import Lines
from mash.shell2.parser import parse


def test_parse_multiline():
    text = """foo
bar
"""
    lines = parse(text)
    assert isinstance(lines, Lines)

    assert len(lines.items) == 2
