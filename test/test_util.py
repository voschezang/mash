from util import concat, split


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
