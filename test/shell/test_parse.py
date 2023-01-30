from pytest import raises

from mash.shell import ShellError
from mash.shell.lex_parser import parse


def parse_line(text: str):
    return list(parse(text))[1][0]


def test_parse_cmd():
    text = 'echo a 10'
    result = list(parse(text))
    assert result[0] == 'lines'
    assert result[1][0][0] == 'list'
    assert result[1][0][1] == ['echo', 'a', '10']
    assert parse_line(text)[1] == ['echo', 'a', '10']


def test_parse_cmds():
    text = 'echo a 10 ; echo b \n echo c'
    result = list(parse(text))
    assert result[0] == 'lines'
    assert result[1][0][0] == 'list'
    assert result[1][0][1] == ['echo', 'a', '10']
    assert result[1][1][0] == 'list'
    assert result[1][1][1] == ['echo', 'b']
    assert result[1][2][0] == 'list'
    assert result[1][2][1] == ['echo', 'c']


def test_parse_infix():
    key, op, left, right = parse_line('x = 2')
    assert key == 'assign'
    assert op == '='
    assert left == 'x'
    assert right == '2'

    key, op, left, right = parse_line('a b = 2')
    assert key == 'assign'
    assert op == '='
    assert left == ('list', ['a', 'b'])
    assert right == '2'


def test_parse_quotes():
    result = parse_line('x = "a b c"')
    key, op, left, right = result
    assert key == 'assign'
    assert op == '='
    assert left == 'x'
    assert right == 'a b c'

    line = r'x = "y =\"\' 1"'
    key, op, left, right = parse_line(line)
    assert right == 'y =\\"\\\' 1'


def test_parse_quotes_multiline():
    # TODO support multiline strings
    text = """x = "y
z" 
    """
    if 0:
        key = parse(text)
        key, op, left, right = parse_line(text)
        assert right == '"y\nz"'


def test_parse_parentheses():
    _, results = parse('(a)')
    assert results[0][0] == 'scope'
    assert results[0][1][0] == 'lines'
    assert results[0][1][1] == ['a']

    _, results = parse('(a (b) c)')
    assert results[0][0] == 'scope'
    assert results[0][1][0] == 'lines'

    inner = results[0][1][1][0]
    assert inner[0] == 'list'
    assert inner[1][0] == 'a'
    assert inner[1][2] == 'c'
    assert inner[1][1][0] == 'scope'
    assert inner[1][1][1] == ('lines', ['b'])


def test_parse_parentheses_quoted():
    _, results = parse('( "(" )')
    results
    assert results[0][0] == 'scope'
    assert results[0][1][0] == 'lines'
    assert results[0][1][1] == ['(']


def test_parse_multiline():
    text = """

x = 2

"""
    key, results = parse(text)
    assert key == 'lines'
    assert results[0][0] == 'assign'


def test_parse_multiline_quoted():
    text = """'
x = 2'"""
    key, results = parse(text)
    assert key == 'lines'
    assert results[0] == '\nx = 2'


def test_parse_indent():
    line = '    echo'
    result = parse_line(line)
    assert result[0] == 'indent'
    assert result[2] == 'echo'


def test_parse_indent_multiline():
    text = '\n\n    \n\t\t\n    echo'
    result = parse(text)[1]
    assert result[0][0] == 'indent'
    assert result[1][0] == 'indent'
    assert result[2][0] == 'indent'
    assert result[2][2] == 'echo'


def test_parse_indent_semicolon():
    text = ';    \n;    echo'
    result = parse(text)[1]
    assert result[0] == 'echo'


def test_parse_if_else():
    line = 'if 1 == 3 then 2 else 3'
    result = parse_line(line)
    key, cond, true, false = result
    assert 'if-then-else' in key
    assert true == '2'
    assert false == '3'

    key, op, left, right = cond
    assert 'binary' in key
    assert op == '=='
    assert left == '1'
    assert right == '3'


def test_parse_if_then_multiline():
    text = """

if x == y then
    inner = a

    if z then
        inner2 = b


outer = c

    """
    results = parse(text)[1]
    assert results[0][0] == 'if'
    assert results[0][1][0] == 'binary-expression'
    assert results[0][1][1:] == ('==', 'x', 'y')
    assert results[1][0] == 'indent'
    assert results[1][1] == (4, 0)
    assert results[2][0] == 'indent'
    assert results[2][1] == (4, 0)
    assert results[3][0] == 'indent'
    assert results[3][1] == (8, 0)
    assert results[3][2][0] == 'assign'
    assert results[3][2][1:] == ('=', 'inner2', 'b')

    assert results[4][0] == 'assign'
    assert results[4][1:] == ('=', 'outer', 'c')


def test_parse_inline_function():
    text = """
f (x): x + 1
    """
    result = parse(text)[1]
    assert result[0][0] == 'define-inline-function'
    assert result[0][1] == 'f'
    assert result[0][2] == 'x'
    key, op, _, _ = result[0][3]
    assert 'binary' in key
    assert op == '+'


def test_parse_function():
    text = """
f (x): 
    if x == 1 then return 2
    return x + 1
    """
    results = parse(text)[1]
    assert results[0][0] == 'define-function'
    assert results[1][0] == 'indent'
    assert results[1][1] == (4, 0)
    assert results[2][0] == 'indent'
    assert results[2][1] == (4, 0)
    assert results[1][2][0] == 'if-then'
    assert results[1][2][1][0] == 'binary-expression'
    assert results[1][2][2] == ('return', '2')
    assert results[2][2][0] == 'return'


def test_parse_bash_pipe():
    result = parse_line('print a | echo')
    assert result[0] == 'bash'
    assert result[1] == '|'
    assert result[2][0] == 'list'
    assert result[3] == 'echo'


def test_parse_pipe():
    result = parse_line('print a |> echo')
    assert result[0] == 'pipe'
    assert result[1] == '|>'
    assert result[2][0] == 'list'
    assert result[3] == 'echo'


def test_parse_pipe_multiple():
    result = parse_line('print a |> echo 1 | echo 2')
    assert result[0] == 'pipe'
    assert result[1] == '|>'
    assert result[2][0] == 'list'
    assert result[2][1] == ['print', 'a']
    assert result[3][0] == 'bash'
    assert result[3][1] == '|'
