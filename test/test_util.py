from util import concat, infer_signature, infer_synopsis, generate_docs


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


def func(a, b: int, c: str = None) -> tuple:
    return a, b


def test_infer_synopsis():
    expected = 'func a b [c]'
    result = infer_synopsis(func)
    assert result == expected


def test_infer_signature():
    expected = ['a', 'b: int', '[c]: str']
    expected = {'a': '', 'b': ': int', '[c]': ': str'}
    result = infer_signature(func)
    assert result == expected


def test_generate_docs():
    expected = """func a b [c]

    Parameters
    ----------
        a
        b: int
        [c]: str
    """
    result = generate_docs(func)
    print(result)
    print(expected)
    assert result == expected
