
from mash.functional_shell.ast.lines import Lines
from mash.functional_shell.ast.term import Term, Word
from mash.functional_shell.ast.terms import Terms
from mash.functional_shell.parser import parse


def parse_line(text: str):
    return parse(text).values[0]


def test_parse_compile():
    parse('abc')


def test_parse_term():
    text = 'ab'
    result = parse(text)
    assert isinstance(result, Lines)

    terms = result.values[0]
    assert isinstance(terms, Terms)
    assert terms.values == ('ab',)
    assert isinstance(terms.values[0], Term)
    assert isinstance(terms.values[0], Word)


def test_parse_terms():
    text = 'ab cd'
    result = parse(text)
    assert isinstance(result, Lines)
    terms = result.values[0]
    assert isinstance(terms, Terms)
    assert terms.values == ('ab', 'cd')
    term = terms.values[0]
    assert isinstance(term, Term)
    assert isinstance(term, Word)


def test_parse_empty():
    assert parse('') is None

    result = parse('  ')
    assert result is None

    result = parse('\t  \t ')
    assert result is None


def test_parse_indented():
    text = '  ab cd  '
    result = parse(text)
    assert isinstance(result, Lines)
    terms = result.values[0]

    assert isinstance(terms, Terms)
    assert terms.values == ('ab', 'cd')
