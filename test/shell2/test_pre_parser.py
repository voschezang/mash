from mash.shell2.pre_parser import PreParser, infer_indent, tokenize
from mash.shell2.tokenizer import inner


def test_pre_parser():
    parser = PreParser()
    parser.input('foo')

    token = parser.token()
    assert token
    assert token.value == 'foo'

    token = parser.token()
    assert not token


def test_pre_parser_peek():
    parser = PreParser()
    parser.input('foo')

    for _ in range(2):
        token = parser.peek()
        assert token
        assert token.value == 'foo'

    token = parser.token()
    assert token

    token = parser.peek()
    assert not token

    token = parser.token()
    assert not token


def test_pre_parser_noop():
    tokens = list(tokenize('foo bar'))

    assert tokens
    assert len(tokens) == 2
    assert tokens[0].value == 'foo'
    assert tokens[0].type == 'METHOD'
    assert tokens[1].value == 'bar'
    assert tokens[1].type == 'METHOD'


def test_pre_parser_indented():
    parser = PreParser()
    text = '    foo bar'

    # ensure line numbers are reset after each run
    for _ in range(2):
        tokens = list(inner(text, tokenizer=parser))

        assert len(tokens) == 4
        assert tokens[0].type == 'BEGIN'
        assert tokens[0].lineno == 1
        assert tokens[1].value == 'foo'
        assert tokens[2].value == 'bar'
        assert tokens[3].type == 'END'


def test_pre_parser_multiline():
    # note the odd indentation and trailing newlines
    text = """
  small indent


    large indent

none
"""
    tokens = list(tokenize(text))

    # the first NEWLINE should be absent
    assert tokens[0].type == 'BEGIN'

    assert tokens[0].lineno == 2
    assert tokens[1].value == 'small'
    assert tokens[2].value == 'indent'

    # the newline should be replaced with BEGIN
    assert tokens[3].type == 'BEGIN'
    assert tokens[3].lineno == 5
    assert tokens[4].value == 'large'
    assert tokens[5].value == 'indent'
    # the newline should be replaced with END
    assert tokens[6].type == 'END'
    assert tokens[7].type == 'END'
    assert tokens[8].value == 'none'

    # the last NEWLINE should be absent
    assert len(tokens) == 9


def test_pre_parser_multiline_if_else():
    # support odd indentation levels
    text = """
if true:
        if false:
        \t foo
        \t bar
else:
  bar

"""
    tokens = list(tokenize(text))

    assert tokens[0].type == 'IF'
    assert tokens[1].value == 'true'
    assert tokens[2].type == 'COLON'
    assert tokens[3].type == 'BEGIN'
    assert tokens[4].type == 'IF'
    assert tokens[5].value == 'false'
    assert tokens[6].type == 'COLON'
    assert tokens[7].type == 'BEGIN'
    assert tokens[8].value == 'foo'
    assert tokens[9].type == 'NEWLINE'
    assert tokens[10].value == 'bar'
    assert tokens[11].type == 'END'
    assert tokens[12].type == 'END'
    assert tokens[13].type == 'ELSE'
    assert tokens[14].type == 'COLON'
    assert tokens[15].type == 'BEGIN'
    assert tokens[16].value == 'bar'
    assert tokens[17].type == 'END'

    assert len(tokens) == 18


def test_infer_indent():
    # parser.input('  foo')
    # token = parser.token()
    # assert infer_indent(token) == 3
    text = """
foo
    bar
foobar
"""
    tokens = list(tokenize(text))

    foo = tokens[0]
    begin = tokens[1]
    bar = tokens[2]
    end = tokens[3]
    foobar = tokens[4]

    assert foo.value == 'foo'
    assert begin.type == 'BEGIN'
    assert bar.value == 'bar'
    assert end.type == 'END'
    assert foobar.value == 'foobar'

    assert infer_indent(foo) == 0
    assert infer_indent(begin) == 4
    assert infer_indent(bar) == 4
    assert infer_indent(foobar) == 0
