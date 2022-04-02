import string
import pytest
from typing import List
from object_parser import *


def test_Spec__new__():
    obj = Spec.__new__(Spec)
    assert obj

    with pytest.raises(SpecError):
        obj = Spec.__new__(Spec, x=1, y=2)


def test_Spec__init__():
    obj = Spec()
    assert obj

    with pytest.raises(SpecError):
        obj = Spec(x=1, y=2)


def test_Spec_parse_field_key():
    key = 'non_existing_key'
    with pytest.raises(SpecError):
        Spec._parse_field_key(key)


def test_Spec_validate_key_formats():
    invalid_keys = ['a b c', '-ab', '_']
    for k in invalid_keys:
        with pytest.raises(SpecError):
            Spec.verify_key_format(k)


def test_constructor():
    value = 2
    assert construct(int, value) == value

    cls = str
    assert construct(cls, value) == cls(value)

    list_of_ints = List[int]
    values: list_of_ints = [2, 3, 4]
    assert construct(list_of_ints, values) == values


def test_key_error_msg():
    msg = key_error_msg('a', '<some class>')
    assert len(msg) > 10


def test_is_alpha():
    assert is_alpha(string.ascii_letters)

    num = '123'
    assert not is_alpha('abc' + num)
    assert is_alpha(num, ignore=num)
