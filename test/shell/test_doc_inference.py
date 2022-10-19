from doc_inference import infer_signature, infer_synopsis, generate_docs


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
