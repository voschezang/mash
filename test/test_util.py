from operator import contains, eq
from pytest import raises

from mash.util import concat, constant, equals, find_prefix_matches, find_fuzzy_matches, for_all, for_any, glob, identity, is_alpha, is_digit, list_prefix_matches, match_words, not_equals, split, split_sequence, split_tips


def test_concat_empty_container():
    assert concat('') == ''
    assert concat([]) == []
    assert concat({}) == {}
    assert concat(set()) == set()
    assert concat(tuple()) == tuple()


def test_concat():
    assert concat('abc') == 'abc'

    assert concat([[1], [2]]) == [1, 2]
    assert concat([['a'], [1], []]) == ['a', 1]

    assert concat([{1, 2}, {2, 3}]) == {1, 2, 3}
    assert concat(({1, 2}, {2, 3})) == {1, 2, 3}

    assert concat([(1, 2), (2, 3)]) == (1, 2, 2, 3)

    assert concat([{'a': 1, 'z': 2}]) == {'a': 1, 'z': 2}


def test_split():
    assert split('1,2,3', ',') == ['1', '2', '3']
    assert split('1,2,3', '-+=') == ['1,2,3']
    assert split('1,2;3', ',;') == ['1', '2', '3']
    assert split('1,2;3', ',;') == ['1', '2', '3']


def test_split_tips():
    d = ';'
    assert list(split_tips([], d)) == [[]]
    assert list(split_tips(';', d)) == [';']
    assert list(split_tips(';;', d)) == [';', ';']
    assert list(split_tips('az', d)) == ['az']
    assert list(split_tips(['a', 'z'], d)) == [['a', 'z']]
    assert list(split_tips(';az', d)) == [';', 'az']
    assert list(split_tips('a;', d)) == ['a', ';']
    assert list(split_tips('az;', d)) == ['az', ';']
    assert list(split_tips(';az;', d)) == [';', 'az', ';']
    assert list(split_tips('..az.;.', '.;')) == ['.', '.', 'az', '.', ';', '.']
    assert list(split_tips(';a;;z;', d)) == [';', 'a;;z', ';']
    assert list(split_tips(';a ; z;', d)) == [';', 'a ; z', ';']


def test_split_sequence():
    d = ';,'
    assert list(split_sequence([], d)) == []
    assert list(split_sequence(',', d)) == []
    assert list(split_sequence(',;;', d)) == []
    assert list(split_sequence([1], ',')) == [[1]]
    assert list(split_sequence([1], d)) == [[1]]
    assert list(split_sequence([1, 2], ',')) == [[1, 2]]
    assert list(split_sequence([1, 2], d)) == [[1, 2]]
    assert list(split_sequence(['a'], d)) == [['a']]
    assert list(split_sequence('ab', d)) == [['a', 'b']]
    assert list(split_sequence('a,b', ',')) == [['a'], ['b']]
    assert list(split_sequence('a,;b', d)) == [['a'], ['b']]
    assert list(split_sequence(';a,b;', d)) == [['a'], ['b']]


def test_split_sequence_no_delim():
    assert list(split_sequence([], '')) == [[]]
    assert list(split_sequence('ab', '')) == [['a', 'b']]


def test_split_sequence_with_return_single_items():
    d = ';,'
    a = 'always'

    # cardinality 1
    assert list(split_sequence(',', d, True)) == []
    assert list(split_sequence('a', d, True)) == [['a']]

    # delimiters as suffix
    assert list(split_sequence('a,', d, True)) == [['a']]
    assert list(split_sequence('a,', d, a)) == [[',', 'a']]
    assert list(split_sequence('a,;;;,,', d, a)) == [[';', ',', 'a']]
    assert list(split_sequence('a;,,,', d, a)) == [[';', 'a']]

    # delimiters as prefix
    assert list(split_sequence(';a', d, a)) == [[';', 'a']]
    assert list(split_sequence(';a', d, True)) == [[';', 'a']]
    assert list(split_sequence(',a', d, a)) == [[',', 'a']]
    assert list(split_sequence(',a', d, True)) == [[',', 'a']]

    # delimiters as both prefix and suffix
    assert list(split_sequence(',,a,,', d, True)) == [[',', 'a']]
    assert list(split_sequence(';,a', d, True)) == [[';', ',', 'a']]
    assert list(split_sequence(',;a', d, True)) == [[';', 'a']]
    assert list(split_sequence(',;a', d, a)) == [[';', 'a']]


def test_split_sequence_with_return_multiple_items():
    d = ';,'
    a = 'always'
    assert list(split_sequence('a,b', d, a)) == [[',', 'a'], [',', 'b']]
    assert list(split_sequence(',a,b,', d, a)) == [[',', 'a'], [',', 'b']]
    assert list(split_sequence('a,b;c', d, a)) == [[';', ',', 'a'],
                                                   [';', ',', 'b'],
                                                   [';', 'c']]
    assert list(split_sequence('a;b,c', d, a)) == [[';', 'a'],
                                                   [';', ',', 'b'],
                                                   [';', ',', 'c']]


def test_split_sequence_with_return_LHS():
    assert list(split_sequence('a|b', '|', True)) == [['a'], ['|', 'b']]
    assert list(split_sequence('a|b', '|', 'always')) == \
        [['|', 'a'], ['|', 'b']]


def test_find_fuzzy_matches():
    # empty inputs
    assert list(find_fuzzy_matches('', [])) == []
    assert list(find_fuzzy_matches('', [''])) == ['']

    # approximations
    assert list(find_fuzzy_matches('b', ['a', 'b'])) == ['b', 'a']
    assert list(find_fuzzy_matches('aa', ['bb'])) == ['bb']
    assert list(find_fuzzy_matches('abcd', ['abbb', 'abcc', 'dcba'])) == [
        'abcc', 'abbb', 'dcba']

    # casing
    assert list(find_fuzzy_matches('a', ['A', 'a'])) == ['a', 'A']


def test_list_prefix_matches_no_input():
    assert list(list_prefix_matches('', ['c', 'b'])) == ['c', 'b']
    assert list(list_prefix_matches('', [])) == []


def test_list_prefix_matches_eager():
    assert list(list_prefix_matches('a', ['b', 'c'])) == []

    assert next(list_prefix_matches('a', ['a'])) == 'a'
    assert next(list_prefix_matches('a', ['c', 'b', 'a'])) == 'a'
    assert next(list_prefix_matches('ab', ['a', 'ab', 'abc'])) == 'ab'


def test_list_prefix_matches_fuzzy():
    assert list(list_prefix_matches('ab', ['abc'])) == ['abc']
    assert list(list_prefix_matches('ba', ['abc'])) == []


def test_find_prefix_matches_all():
    assert list(find_prefix_matches('a', ['c', 'b', 'a'])) == ['a']
    assert list(find_prefix_matches('a', ['aa', 'ai'])) == ['aa', 'ai']
    assert list(find_prefix_matches('ab', ['aa', 'ab'])) == ['ab', 'aa']


def test_match_word():
    assert match_words('i abc') == ['i', 'abc']
    assert match_words('<abc>') == ['abc']
    assert match_words('-abc-[def] x_1') == ['abc', 'def', 'x_1']
    assert match_words('a$x...$y', prefix=r'\$') == ['$x', '$y']
    assert match_words('{$from..$to_here}', prefix=r'\$') == \
        ['$from', '$to_here']


def test_glob_with_options():
    v = 'abc?{a'
    assert list(glob(v)) == [v]

    v = '?[a-z]*'
    assert list(glob(v)) == [v]

    options = ['ab', 'de']
    assert list(glob('*', options)) == options
    assert list(glob('a?', options)) == ['ab']
    assert list(glob('[a-z]?', options)) == options
    assert list(glob('[a-z][a-c]', options)) == ['ab']
    assert list(glob('[a-z]', options)) == ['[a-z]']

    with raises(ValueError):
        list(glob('{a]', options, strict=True))

    with raises(ValueError):
        list(glob('[a-z]', options, strict=True))


def test_glob_ranges():
    assert list(glob('{4..2}')) == ['4', '3', '2']
    assert list(glob('{aa,bb}')) == ['aa', 'bb']
    assert set(glob('{1..2}-{aa,bb}')) == {'1-aa', '2-aa', '1-bb', '2-bb'}


def test_identity():
    assert identity(1) == 1
    assert identity(1, 2) == (1, 2)


def test_constant():
    K = constant(1)
    assert K(10) == 1


def test_find_prefix_matches():
    assert next(find_prefix_matches('a', ['a'])) == 'a'

    with raises(ValueError):
        assert next(find_prefix_matches('a', ['A', 'b', 'c', ])) == 'ab'


def test_is_alpha():
    assert is_alpha('abc')
    assert not is_alpha('-')
    assert is_alpha('-', ignore='-')


def test_is_digit():
    assert is_digit(1)
    assert is_digit(-1)
    assert is_digit('+10')
    assert is_digit('-10')

    assert not is_digit(1.2)
    assert not is_digit([])
    assert not is_digit('1.2')
    assert not is_digit('1 2')


def test_for_any():
    items = [1, 2]
    assert for_any(items, eq, 2)
    assert not for_any(items, eq, 3)


def test_for_all():
    # a single collection
    assert for_any([1, 2], eq, 2)

    # two collections
    assert for_all([1], contains, [1, 2])
    assert not for_all([1, 2], contains, [1])


def test_equals():
    assert equals(1, 1, 1)
    assert not equals(1, 2, 3)


def test_not_equals():
    assert not_equals(1, 2, 3)
    assert not not_equals(1, 1, 1)
