from mash.functional_shell.tokenizer import main, tokenize


def test_tokenizer():
    lexer = main()
    assert lexer is not None


def test_tokenize_single():
    token = list(tokenize('myfunction'))[0]
    # assert token.type == 'METHOD'
    assert token.value == 'myfunction'

    token = list(tokenize('abc/def'))[0]
    assert token.type == 'WORD'
    assert token.value == 'abc/def'

    token = list(tokenize('1'))[0]
    # assert token.type == 'INT'


def test_tokenize_multiple():
    token = list(tokenize('1 2 3'))[0]
    # assert token.type == 'INT'


def test_tokenize_indentation():
    tokens = list(tokenize('  abc'))
    tokens
