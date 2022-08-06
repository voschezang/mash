from pytest import raises

from util import concat, find_prefix_matches, split


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


def test_find_prefix_matches_eager():
    def f(*args):
        return next(find_prefix_matches(*args))

    assert next(find_prefix_matches('a', ['a'])) == 'a'
    assert next(find_prefix_matches('a', ['c', 'b', 'a'])) == 'a'
    assert next(find_prefix_matches('ab', ['a', 'ab', 'abc'])) == 'ab'

    with raises(ValueError):
        assert next(find_prefix_matches('a', ['A', 'b', 'c', ])) == 'ab'


def text_find_prefix_matches_all():
    assert list(find_prefix_matches('a', ['c', 'b', 'a'])) == ['a']
    assert list(find_prefix_matches('a', ['aa', 'ai'])) == ['aa', 'ai']
    assert list(find_prefix_matches('ab', ['aa', 'ab'])) == ['ab', 'aa']
