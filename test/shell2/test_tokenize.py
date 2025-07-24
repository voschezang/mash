from mash.shell2.tokenizer import main, tokenize


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
    assert token.type == 'INT'


def test_tokenize_indentation():
    tokens = list(tokenize('  abc'))
    assert len(tokens) == 1
    assert tokens[0].type == 'METHOD'
    assert tokens[0].value == 'abc'


def test_tokenize_list():
    tokens = list(tokenize('[1, 2, ab c ]'))
    assert tokens[0].type == 'LBRACE'
    assert tokens[1].type == 'INT'
    assert tokens[2].type == 'COMMA'
    assert tokens[3].type == 'INT'
    assert tokens[4].type == 'COMMA'
    assert tokens[5].type == 'METHOD'
    assert tokens[6].type == 'METHOD'
    assert tokens[7].type == 'RBRACE'
