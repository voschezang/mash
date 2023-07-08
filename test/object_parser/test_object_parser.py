from enum import auto, Enum
from typing import List
import pytest
import string

from mash.object_parser.object_parser import parse_field_key, verify_key_format
from mash.object_parser.errors import SpecError
from mash.object_parser.factory import Factory, JSONFactory
from mash.util import is_alpha, is_enum


class Dummy:
    a: int
    b: float


def test_abstract_factory():
    with pytest.raises(TypeError):
        Factory()


def test_factory():
    cls = int
    errors = 'dummy'
    f = JSONFactory(cls, errors=errors)
    assert f.cls == cls
    assert f.errors == errors
    assert hasattr(f.build, '__call__')


def test_Spec_parse_field_key():
    key = 'non_existing_key'

    parse_field_key(Dummy, 'a')

    with pytest.raises(SpecError):
        parse_field_key(Dummy, key)


def test_verify_key_formats():
    invalid_keys = ['a b c', '-ab', '_']

    verify_key_format(Dummy, 'a')

    for k in invalid_keys:
        with pytest.raises(SpecError):
            verify_key_format(Dummy, k)


def test_constructor():
    value = 2
    cls = int
    for cls in (bool, int, float, str):
        assert JSONFactory(cls).build(value) == cls(value)

    list_of_ints = List[int]
    values: list_of_ints = [2, 3, 4]

    assert JSONFactory(list_of_ints).build(values) == values


def test_is_alpha():
    assert is_alpha(string.ascii_letters)

    num = '123'
    assert not is_alpha('abc' + num)
    assert is_alpha(num, ignore=num)


def test_is_enum():
    class A(Enum):
        a = auto()
        b = auto()

    assert is_enum(A)
    assert not is_enum(str)
