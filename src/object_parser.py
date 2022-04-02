from typing import _GenericAlias
from enum import Enum


class Spec():
    """Spec

    Initialize with either:
    ```py
    Spec( {'a': 1, 'b': 2} )
    Spec(a=1, b=2)
    ```

    A specification for an object can be defined using type annotations:
    ```py
    class User:
        email: str
        default_age: int = 0
    ```

    User-defined methods
    --------------------
    - `.parse()` can be used to pre-process input values before instantiating objects
    - `.verify()` can be used to check an object after instantiation

    See object_parser_example.py for a larger usecase as an example.
    """

    key_synonyms = {}

    def __init__(self, data=None, **kwds):
        """"Init
        This stub is included to show which args are used.
        """
        pass

    def verify(self):
        """Verify this object.
        Note that this method can do verifications that are based on multiple fields.
        Raise `SpecError` in case of a failed verification.
        """
        pass

    @staticmethod
    def parse(value):
        """Transform the raw input value of this object, before calling `.__init__()`
        This is mainly useful for Enums, but it is applied to all datatypes for consistency.

        E.g. use this to change the casing of an input string.
        """
        return value

    @staticmethod
    def parse_key(key):
        """Transform a raw input key (attribute) of this object
        This can be used to for example convert an input to lowercase.
        Note that this method is applied to all keys (attributes).
        """
        return key

    @classmethod
    def verify_key_format(cls, key: str):
        if not is_alpha(key, ignore='_') or key.startswith('_'):
            raise SpecError(cls.invalid_key_format(key))

    def items(self):
        return {k: getattr(self, k) for k in self.__annotations__}

    ############################################################################
    # Error Messages
    ############################################################################

    @classmethod
    def invalid_key_format(cls, key: str):
        return f'Format of key: `{key}` was invalid  in {cls}'

    @classmethod
    def missing_mandatory_key(cls, key: str):
        return f'Missing mandatory key: `{key}` in {cls}'

    @classmethod
    def unexpected_key(cls, key):
        return f'Unexpected key `{key}` in {cls}'

    @classmethod
    def no_type_annotations(cls):
        return f'No fields specified to initialize (no type annotations in {cls})'

    ############################################################################
    # Internals
    ############################################################################

    def __new__(cls, data={}, **kwds):
        """ Generic constructor that validates the keys before initializing the object.
        """
        if data:
            # merge all arguments
            kwds.update(data)

        fields = cls._init_fields(kwds)

        instance = super(Spec, cls).__new__(cls)
        if hasattr(cls, '__annotations__'):
            for k in cls.__annotations__:
                setattr(instance, k, fields[k])

        instance.verify()
        return instance

    @classmethod
    def _init_fields(cls, data: dict) -> dict:
        """Instantiate all entries of `data`
        """
        data = cls._parse_field_keys(data)

        result = {}
        if not data:
            return result
        elif not hasattr(cls, '__annotations__'):
            raise SpecError(cls.no_type_annotations())

        for key in cls.__annotations__:
            result[key] = cls._init_field(key, data)
            cls.verify(result[key])

        return result

    @classmethod
    def _init_field(cls, key, data):
        if key in data:
            return construct(cls.__annotations__[key], data[key])
        elif hasattr(cls, key):
            return getattr(cls, key)

        raise SpecError(cls.missing_mandatory_key(key))

    @classmethod
    def _parse_field_keys(cls, data) -> dict:
        # note that dict comprehensions ignore duplicates
        return {cls._parse_field_key(k): v for k, v in data.items()}

    @classmethod
    def _parse_field_key(cls, key: str):
        cls.verify_key_format(key)

        key = cls.parse_key(key)
        if hasattr(cls, '__annotations__') and key in cls.__annotations__:
            return key

        return cls._find_synonym(key)

    @classmethod
    def _find_synonym(cls, key: str):
        0
        for original_key, synonyms in cls.key_synonyms.items():
            if key in synonyms:
                return original_key

        raise SpecError(f'Unexpected key `{key}` in {cls}')


class SpecError(Exception):
    pass


def construct(cls, args):
    if is_enum(cls):
        try:
            parsed_value = cls.parse(args)
            return cls[parsed_value]
        except KeyError:
            raise SpecError(f'Invalid value for {cls}(Enum)')

    if isinstance(cls, _GenericAlias):
        # assume this is a typing.List
        if len(cls.__args__) != 1:
            raise NotImplementedError

        list_item = cls.__args__[0]
        return [list_item(v) for v in args]

    # try to apply `.parse`
    if hasattr(cls, 'parse') and hasattr(cls.parse, '__call__'):
        args = cls.parse(args)

    return cls(args)


# Error Messages


def key_error_msg(key, spec: Spec):
    return f'key: {key} in {spec}'


# Predicates


def is_alpha(key: str, ignore=[]) -> bool:
    return all(c.isalpha() or c in ignore for c in key)


def is_enum(cls):
    try:
        return issubclass(cls, Enum)
    except TypeError:
        pass
