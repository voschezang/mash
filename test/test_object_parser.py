from enum import auto, Enum
from typing import List
import pytest
import string

from object_parser import *
from object_parser import parse_field_key, verify_key_format
from object_parser import Factory, JSONFactory


def test_abstract_factory():
    with pytest.raises(TypeError):
        Factory()


def test_factory():
    cls = int
    errors = 'dummy'
    f = JSONFactory(cls, errors)
    assert f.cls == cls
    assert f.errors == errors
    assert hasattr(f.build, '__call__')


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
        parse_field_key(Spec, key)


def test_verify_key_formats():
    invalid_keys = ['a b c', '-ab', '_']
    for k in invalid_keys:
        with pytest.raises(SpecError):
            Spec.verify_key_format(k)

        with pytest.raises(SpecError):
            verify_key_format(Spec, k)


def test_constructor():
    value = 2
    cls = int
    for cls in (bool, int, float, str):
        assert init(cls, value) == cls(value)
        assert JSONFactory(cls).build(value) == cls(value)

    list_of_ints = List[int]
    values: list_of_ints = [2, 3, 4]
    assert init(list_of_ints, values) == values

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
