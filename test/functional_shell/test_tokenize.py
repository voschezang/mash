from mash.functional_shell.tokenizer import main, tokenize


def test_tokenizer():
    lexer = main()
    assert lexer is not None


def test_tokenizer_empty():
    assert list(tokenize('')) == []
    assert list(tokenize('  ')) == []


def test_tokenize_single():
    token = list(tokenize('myfunction'))[0]
    assert token.type == 'METHOD'
    assert token.value == 'myfunction'

    token = list(tokenize('1'))[0]
    assert token.type == 'INT'


def test_tokenize_path():
    tokens = list(tokenize('abc/123'))
    assert tokens[0].value == 'abc'
    assert tokens[0].type == 'METHOD'
    assert tokens[1].value == '/'
    assert tokens[1].type == 'SLASH'
    assert tokens[2].value == '123'
    assert tokens[2].type == 'INT'


def test_tokenize_multiple():
    token = list(tokenize('1 2 3'))[0]
    # assert token.type == 'INT'


def test_tokenize_indentation():
    tokens = list(tokenize('  abc'))
    tokens
