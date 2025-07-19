
from mash.shell2.ast.term import Term, Word


def test_ast_term():
    a = Term('1')
    b = Term('1')
    c = Term('2')

    assert a.value == '1'
    assert b.value == '1'
    assert c.value == '2'

    assert a == b
    assert a != c


def test_ast_word():
    word = Word('abc')
    assert word.value == 'abc'
    assert str(word) == 'abc'
    assert repr(word) == 'abc'
    assert len(word) == 3

    assert word.run(None) == 'abc'
