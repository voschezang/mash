from pytest import raises

from mash.shell.errors import ShellSyntaxError
from mash.shell.lex_parser import parse
from mash.shell.model import BashPipe, BinaryExpression, ElseIf, ElseIfThen, If, IfThen, IfThenElse, Indent, InlineFunctionDefinition, Lines, Map, Math, Method, Pipe, Term, Terms, Word


def parse_line(text: str):
    return parse(text).values[0]


def test_parse_cmd():
    text = 'echo a 10'
    result = parse(text)
    assert isinstance(result, Lines)
    assert isinstance(result.values[0], Terms)
    values = result.values[0].values
    assert values == ['echo', 'a', '10']
    assert parse_line(text).values == ['echo', 'a', '10']


def test_parse_cmds():
    text = 'echo a 10 ; echo b \n echo c'
    result = parse(text)
    assert isinstance(result, Lines)
    results = result.values
    assert isinstance(results[0], Terms)
    assert results[0].values == ['echo', 'a', '10']
    assert isinstance(results[1], Terms)
    assert results[1].values == ['echo', 'b']
    assert isinstance(results[2], Terms)
    assert results[2].values == ['echo', 'c']


def test_parse_comment():
    text = '# a comment'
    result = parse(text)
    assert isinstance(result, Lines)
    assert result.values == []


def test_parse_term():
    line = 'abc d-?e* [a-z]10'
    terms = parse_line(line)

    assert isinstance(terms, Terms)
    values = terms.values

    assert values[0] == 'abc'
    assert isinstance(values[0], Method)
    assert values[1] == 'd-?e*'
    assert values[1].type == 'wildcard'
    assert values[2] == '[a-z]10'
    assert values[2].type == 'wildcard'


def test_parse_word():
    line = '238u3r'
    result = parse(line)
    assert isinstance(result, Lines)
    assert isinstance(result.values[0], Word)
    assert result.values[0] == '238u3r'

    line = '+'
    result = parse(line)
    assert isinstance(result.values[0], Word)
    assert result.values[0].type == 'symbol'
    assert result.values[0] == '+'

    line = '?'
    result = parse(line)
    assert result.values[0].type == 'wildcard'
    assert result.values[0] == '?'


def test_parse_equations():
    text = '1+a'
    result = parse_line(text)

    assert isinstance(result, Terms)
    values = result.values

    assert values[0] == '1'
    assert values[0].type == 'term'
    assert values[1] == '+'
    assert values[1].type == 'symbol'
    assert values[2] == 'a'
    assert isinstance(values[2], Method)


def test_parse_range():
    line = 'pre{1..3}post'
    result = parse_line(line)
    assert result == line


def test_parse_assign():
    key, op, left, right = parse_line('a <- 10')
    assert key == 'assign'
    assert op == '<-'
    assert left == 'a'
    assert right == '10'


def test_parse_infix():
    key, op, left, right = parse_line('x = 2')
    assert key == 'assign'
    assert op == '='
    assert left == 'x'
    assert right == '2'

    key, op, left, right = parse_line('a b = 2')
    assert key == 'assign'
    assert op == '='

    assert isinstance(left, Terms)
    assert left.values == ['a', 'b']
    assert right == '2'


def test_parse_numbers():
    numbers = ['-1', '-0.1', '.2', '-100.']
    text = 'x = ' + ' '.join(numbers)
    # text = '-1.'
    result = parse_line(text)
    assert result[0] == 'assign'
    assert result[2] == 'x'
    assert result[3].values == numbers


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
    results = parse('(a)').values
    assert results[0][0] == 'scope'
    assert results[0][1] == 'a'

    result = parse('(a b c)')
    assert isinstance(result, Lines)
    results = result.values
    assert results[0][0] == 'scope'
    assert isinstance(results[0][1], Terms)
    assert results[0][1].values == ['a', 'b', 'c']

    results = parse('(a (b c) (d))').values
    assert results[0][0] == 'scope'
    assert isinstance(results[0][1], Terms)

    inner = results[0][1].values
    assert inner[0] == 'a'
    assert inner[1][0] == 'scope'
    assert inner[1][1].values == ['b', 'c']
    assert isinstance(inner[1][1], Terms)
    assert inner[2] == ('scope', 'd')


def test_parse_parentheses_quoted():
    results = parse('( "(" )').values
    assert results[0][0] == 'scope'
    assert results[0][1] == '('


def test_parse_multiline():
    text = """

x = 2

"""
    results = parse(text)
    assert isinstance(results, Lines)
    assert results.values[0][0] == 'assign'


def test_parse_multiline_quoted():
    text = """'
x = 2'"""
    results = parse(text)
    assert isinstance(results, Lines)
    assert results.values[0] == '\nx = 2'


def test_parse_indent():
    # TODO handle double spaces
    # line = '    echo   c'
    line = '    echo b c'
    result = parse_line(line)
    assert isinstance(result, Indent)

    inner = result.data
    assert isinstance(inner, Terms)
    assert inner.values == ['echo', 'b', 'c']


def test_parse_indent_multiline():
    text = '\n\n    \n\t\t\n    echo'
    result = parse(text).values
    assert isinstance(result[0], Indent)
    assert isinstance(result[1], Indent)
    assert isinstance(result[2], Indent)
    assert result[0].data is None
    assert result[1].data is None
    assert result[2].data == 'echo'


def test_parse_indent_semicolon():
    text = ';    \n;    echo'
    result = parse(text).values
    assert result[0] == 'echo'


def test_parse_if_else():
    line = 'if 1 == 3 then 2 else 3'
    result = parse_line(line)
    assert isinstance(result, IfThenElse)
    cond, true, false = result.condition, result.then, result.otherwise
    assert true == '2'
    assert false == '3'

    assert isinstance(cond, BinaryExpression)
    assert cond.op == '=='
    assert cond.lhs == '1'
    assert cond.rhs == '3'


def test_parse_if_then():
    line = 'if 1 == 3 then 2'
    result = parse_line(line)
    assert isinstance(result, IfThen)
    assert result.condition.op == '=='
    assert result.then == '2'

    line = 'if true print 2'
    result = parse_line(line)
    assert isinstance(result, If)
    assert isinstance(result.condition, Terms)
    assert result.condition.values == ['true', 'print', '2']

    # double then
    text = 'if 1 then print 1 then print 2'
    with raises(ShellSyntaxError):
        parse_line(text)

    text = 'if 1 then print 1 ; then print 2'
    result = parse_line(text)


def test_parse_if_with_colons():
    line = 'if 1 then print a; print b'
    result = parse(line)
    assert isinstance(result, Lines)
    results = result.values
    assert isinstance(results[0], IfThen)
    assert results[0].condition == '1'
    assert isinstance(results[0].then, Terms)
    assert results[0].then.data == 'print a'
    assert results[1].data == 'print b'


def test_parse_else():
    text = 'else if 2 == 2'
    result = parse_line(text)
    assert isinstance(result, ElseIf)

    assert result.condition.op == '=='
    assert result.condition.lhs == '2'
    assert result.condition.rhs == '2'


def test_parse_if_then_multiline():
    text = """

if x == y then
    inner = a

    if z then
        inner2 = b


outer = c

    """
    results = parse(text).values
    assert isinstance(results[0], IfThen)

    assert isinstance(results[0].condition, BinaryExpression)

    assert results[0].condition == BinaryExpression('x', 'y', '==')

    assert isinstance(results[1], Indent)
    assert isinstance(results[2], Indent)
    assert isinstance(results[3], Indent)

    assert results[1].indent == (4, 0)
    assert results[2].indent == (4, 0)
    assert results[3].indent == (8, 0)
    assert results[3].data[0] == 'assign'
    assert results[3].data[1:] == ('=', 'inner2', 'b')

    assert results[4][0] == 'assign'
    assert results[4][1:] == ('=', 'outer', 'c')


def test_parse_else_if():
    text = 'else if 1 then echo 2'
    result = parse_line(text)
    assert isinstance(result, ElseIfThen)
    assert result.condition == '1'
    assert isinstance(result.then, Terms)


def test_parse_if_with_assign():
    text = 'a <- if 20 then echo 10'
    key, *result = parse_line(text)
    assert key == 'assign'
    assert result[0] == '<-'
    assert result[1] == 'a'
    assert isinstance(result[2], IfThen)


def test_parse_if_none():
    with raises(ShellSyntaxError):
        parse('if    then')

    with raises(ShellSyntaxError):
        parse('if then')

    with raises(ShellSyntaxError):
        parse('else then')

    with raises(ShellSyntaxError):
        parse('if else')


def test_parse_map():
    result = parse_line('range 4 >>= echo')
    assert isinstance(result, Map)
    assert result.lhs.values == ['range', '4']
    assert result.rhs == 'echo'


def test_parse_bash_pipe():
    result = parse_line('print a | echo')
    assert isinstance(result, BashPipe)
    assert result.op == '|'
    assert result.lhs.values == ['print', 'a']
    assert result.rhs == 'echo'


def test_parse_pipe():
    result = parse_line('print a |> echo')
    assert isinstance(result, Pipe)
    assert isinstance(result.lhs, Terms)
    assert result.rhs == 'echo'


def test_parse_pipe_multiple():
    result = parse_line('print a |> echo 1 >>= echo 2 | echo')
    assert isinstance(result, Pipe)
    assert result.lhs.values == ['print', 'a']
    m = result.rhs
    assert isinstance(m, Map)
    assert m.lhs.values == ['echo', '1']

    assert isinstance(m.rhs, BashPipe)
    assert m.rhs.op == '|'
    assert m.rhs.lhs.values == ['echo', '2']
    assert m.rhs.rhs == 'echo'


def test_parse_pipe_assign():
    result = parse_line('a <- echo a |> echo b')
    key, symbol, var, line = result
    assert key == 'assign'
    assert symbol == '<-'
    assert var == 'a'

    assert isinstance(line, Pipe)
    assert line.lhs.values == ['echo', 'a']
    assert line.rhs.values == ['echo', 'b']


def test_parse_pipes_long():
    result = parse_line('echo a |> echo b == c |> echo c')
    assert isinstance(result, Pipe)

    assert result.lhs.values == ['echo', 'a']
    inner = result.rhs.lhs

    assert inner.op == '=='
    assert inner.lhs.values == ['echo', 'b']
    assert inner.rhs == 'c'
    assert result.rhs.rhs.values == ['echo', 'c']

    line = 'echo a |> echo b =='
    with raises(ShellSyntaxError):
        parse_line(line)


def test_parse_pipes_if_then():
    text = 'echo 1 |> if true then echo true else echo false'
    result = parse_line(text)
    assert isinstance(result, Pipe)
    assert result.lhs.values == ['echo', '1']
    assert isinstance(result.rhs, IfThenElse)

    with raises(ShellSyntaxError):
        text = 'echo 1 |> if true'
        parse_line(text)

    text = 'if f 1 |> g then echo true else echo false'
    result = parse_line(text)
    assert isinstance(result, IfThenElse)


def test_parse_inline_function():
    text = """
f (x y): x + y
    """
    result = parse_line(text)
    assert isinstance(result, InlineFunctionDefinition)
    assert result.f == 'f'
    assert isinstance(result.args, Terms)
    assert result.args.values == ['x', 'y']
    assert isinstance(result.body, Terms)
    assert result.body.values == ['x', '+', 'y']


def test_parse_inline_function_with_pipe():
    text = 'f (x y): echo x |> echo'
    result = parse_line(text)
    assert isinstance(result, InlineFunctionDefinition)
    assert result.f == 'f'
    assert result.args.values == ['x', 'y']
    assert isinstance(result.body, Pipe)
    assert result.body.lhs.values == ['echo', 'x']
    assert result.body.rhs == 'echo'


def test_parse_function():
    text = """
f (x): 
    if $x == 1 then return 2
    return $x + 1

print outer 
    """
    results = parse(text).values
    assert results[0][0] == 'define-function'
    assert results[0][1] == 'f'
    assert results[0][2] == 'x'
    assert isinstance(results[1], Indent)
    assert isinstance(results[2], Indent)
    assert results[1].indent == (4, 0)
    assert results[2].indent == (4, 0)

    assert isinstance(results[1].data, IfThen)
    assert isinstance(results[1].data.condition, BinaryExpression)
    assert results[1].data.then[0] == 'return'
    assert results[1].data.then[1].data == '2'
    assert results[2][0] == 'return'
    # non-indented code
    assert isinstance(results[3], Terms)
    assert results[3].values == ['print', 'outer']


def test_parse_math():
    result = parse_line('math 1 + 1')
    assert isinstance(result, Math)
    assert isinstance(result.data, Terms)
    assert result.data.values == ['1', '+', '1']

    result = parse_line('math 1 == 1')
    assert isinstance(result, Math)
    assert isinstance(result.data, BinaryExpression)
    assert result.data.op == '=='
    assert result.data.lhs == '1'
    assert result.data.rhs == '1'
