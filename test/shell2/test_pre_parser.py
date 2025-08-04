from pytest import raises
from mash.shell2 import tokenizer
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

    # there should be a single newline token
    assert tokens[3].type == 'NEWLINE'

    assert tokens[4].type == 'BEGIN'
    assert tokens[4].lineno == 5
    assert tokens[5].value == 'large'
    assert tokens[6].value == 'indent'
    assert tokens[7].type == 'NEWLINE'
    assert tokens[8].type == 'END'
    assert tokens[9].type == 'END'
    assert tokens[10].value == 'none'
    # assert tokens[7].type == 'NEWLINE'

    # the last NEWLINE should be absent
    assert len(tokens) == 11


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
    # tokens = list(tokenizer.tokenize(text))
    tokens = list(tokenize(text))

    assert tokens[0].type == 'IF'
    assert tokens[1].value == 'true'
    assert tokens[2].type == 'COLON'
    assert tokens[3].type == 'NEWLINE'
    assert tokens[4].type == 'BEGIN'
    assert tokens[5].type == 'IF'
    assert tokens[6].value == 'false'
    assert tokens[7].type == 'COLON'
    assert tokens[8].type == 'NEWLINE'
    assert tokens[9].type == 'BEGIN'
    assert tokens[10].value == 'foo'
    assert tokens[11].type == 'NEWLINE'
    assert tokens[12].value == 'bar'
    assert tokens[13].type == 'NEWLINE'
    assert tokens[14].type == 'END'
    assert tokens[15].type == 'END'
    assert tokens[16].type == 'ELSE'
    assert tokens[17].type == 'COLON'
    assert tokens[18].type == 'NEWLINE'
    assert tokens[19].type == 'BEGIN'
    assert tokens[20].value == 'bar'
    assert tokens[21].type == 'END'


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
    begin = tokens[2]
    bar = tokens[3]
    end = tokens[5]
    foobar = tokens[6]

    assert foo.value == 'foo'
    assert begin.type == 'BEGIN'
    assert bar.value == 'bar'
    assert end.type == 'END'
    assert foobar.value == 'foobar'

    assert infer_indent(foo) == 0
    assert infer_indent(begin) == 4
    assert infer_indent(bar) == 4
    assert infer_indent(foobar) == 0
