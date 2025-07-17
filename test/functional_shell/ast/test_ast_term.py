
from mash.functional_shell.ast.term import Term, Word
from mash.functional_shell.ast.terms import Terms


def test_ast_term():
    a = Term('1')
    b = Term('1')
    c = Term('2')

    assert a.data == '1'
    assert b.data == '1'
    assert c.data == '2'

    assert a == b
    assert a != c


def test_ast_terms():
    terms = Terms(Word('ab'), Word('cd'))
    assert terms.values[0] == 'ab'
    assert terms.values[1] == 'cd'

    assert terms == Terms(Word('ab'), Word('cd'))
    assert terms != Terms(Word('cd'), Word('ab'))


def test_ast_run_terms():
    terms = Terms(Word('ab'), Word('cd'))
    assert terms.run(None) == 'ab cd'
    assert terms.values[0].run(None) == 'ab'
    assert terms.values[1].run(None) == 'cd'
