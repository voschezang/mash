"""Parse json-like data and init objects such as dataclasses.

# Classes

- `factory.Factory` is a generic interface. 
- `factory.JSONFactory` is a concrete implementation.
- `errors.ErrorMessages` exposes a few custom strings.
- `spec.Spec` is a legacy alternative to dataclasses that provides a simplified constructor.
"""

from mash.object_parser.errors import BuildError, ErrorMessages, SpecError
from mash.util import has_annotations, has_method, is_Dict, is_Dict_or_List, is_List, is_valid_method_name


def parse_field_keys(cls, data) -> dict:
    # note that dict comprehensions ignore duplicates
    return {parse_field_key(cls, k): v for k, v in data.items()}


def parse_field_key(cls, key: str) -> str:
    if is_Dict_or_List(cls):
        if is_Dict(cls):
            inner_cls = cls.__args__[1]
        elif is_List(cls):
            inner_cls = cls.__args__[0]

        if is_Dict_or_List(cls):
            return key

        return f'{{{inner_cls.__name__}}}'

    if has_method(cls, 'verify_key_format'):
        cls.verify_key_format(key)
    else:
        verify_key_format(cls, key)

    if has_method(cls, 'parse_key'):
        key = cls.parse_key(key)

    if has_annotations(cls) and key in cls.__annotations__:
        return key

    return find_synonym(cls, key)


def find_synonym(cls, key: str):
    if hasattr(cls, '_key_synonyms'):
        for original_key, synonyms in cls._key_synonyms.items():
            if key in synonyms:
                return original_key

    raise BuildError(ErrorMessages.unexpected_key(cls, key))


def verify_key_format(cls, key: str):
    if key.startswith('_') or not is_valid_method_name(key):
        raise SpecError(ErrorMessages.invalid_key_format(cls, key))
