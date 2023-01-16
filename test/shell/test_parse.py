from pytest import raises

from mash.shell import ShellError
from mash.shell.lex_parser import parse


def test_parse_cmd():
    text = 'echo a 10'
    result = list(parse(text))[0]
    assert result == 'echo, a, 10'


def test_parse_infix():
    text = 'x = 2'
    key, op, left, right = list(parse(text))[0]
    assert 'binary' in key
    assert op == '='
    assert left == 'x'
    assert right == '2'

    text = 'a b = 2'
    key, op, left, right = list(parse(text))[0]
    assert left == 'a, b'


def test_parse_quotes():
    text = 'x = "a b c"'
    key, op, left, right = list(parse(text))[0]
    assert 'binary' in key
    assert op == '='
    assert left == 'x'
    assert right == '"a b c"'

    text = 'x = "y = 1"'
    key, op, left, right = list(parse(text))[0]
    assert right == '"y = 1"'

    # TODO support multiline strings
    text = """x = "y
z" 
    """
    key, op, left, right = list(parse(text))[0]
    assert right == 'y'


def test_parse_if_else():
    text = 'if 1 == 3 then 2 else 3'
    result = list(parse(text))[0]
    key, cond, true, false = result
    assert 'if-then-else' in key
    assert true == '2'
    assert false == '3'

    key, op, left, right = cond
    assert 'binary' in key
    assert op == '=='
    assert left == '1'
    assert right == '3'


def test_parse_inline_function():
    text = """
    f (x): x + 1
    """
    result = list(parse(text))[0]
    assert result[0] == 'define-inline-function'
    assert result[1] == 'f'
    assert result[2] == 'x'
    key, op, _, _ = result[3]
    assert 'binary' in key
    assert op == '+'


def test_parse_function():
    text = """
    f (x): 
        if x == 1 then return 2
        return x + 1
    """
    result = list(parse(text))
    assert result[0][0] == 'define-function'
    assert result[1][0] == 'if-then'
    assert result[1][1][0] == 'binary-expression'
    assert result[1][2][0] == 'return'
    assert result[2][0] == 'return'
