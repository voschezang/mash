from mash.shell2.pre_parser import PreParser, tokenize
from mash.shell2.tokenizer import inner


def test_pre_parser_init():
    parser = PreParser()
    parser.input('foo')


def test_pre_parser_noop():
    tokens = list(tokenize('foo bar'))

    assert tokens
    assert len(tokens) == 2
    assert tokens[0].value == 'foo'
    assert tokens[1].value == 'bar'


def test_pre_parser_indented():
    parser = PreParser()
    text = '    foo bar'

    # ensure line numbers are reset after each run
    for _ in range(2):
        tokens = list(inner(text, tokenizer=parser))

        assert len(tokens) == 3
        assert tokens[0].type == 'INDENT'
        assert tokens[0].lineno == 1
        assert tokens[1].value == 'foo'
        assert tokens[2].value == 'bar'


def test_pre_parser_multiline():
    text = """  foo bar
    foo bar
"""
    tokens = list(tokenize(text))

    assert tokens[0].type == 'INDENT'
    assert tokens[0].lineno == 1
    assert tokens[1].value == 'foo'
    assert tokens[2].value == 'bar'
    assert tokens[3].type == 'NEWLINE'

    assert tokens[4].type == 'INDENT'
    assert tokens[4].lineno == 2
    assert tokens[5].value == 'foo'
    assert tokens[6].value == 'bar'
    assert tokens[7].type == 'NEWLINE'

    assert len(tokens) == 8
