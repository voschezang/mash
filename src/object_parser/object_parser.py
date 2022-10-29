"""Parse json-like data and init objects such as dataclasses.

# Classes

- `Factory` is a generic interface. 
- `JSONFactory` is a concrete implementation.
- `ErrorMessages` exposes a few custom strings.
- `Spec` is a legacy alternative to dataclasses that provides a simplified constructor.
"""
from typing import _GenericAlias, Dict
from enum import Enum
from abc import ABC, abstractmethod

from util import has_annotations, has_method, infer_inner_cls, is_alpha, is_alphanumerical, is_enum


class ErrorMessages:
    """A static class with can be subclassed
    """
    @staticmethod
    def invalid_key_format(cls, key: str):
        return f'Format of key: `{key}` was invalid  in {cls}'

    @staticmethod
    def missing_mandatory_key(cls, key: str) -> str:
        return f'Missing mandatory key: `{key}` in {cls}'

    @staticmethod
    def no_type_annotations(cls) -> str:
        return f'No fields specified to initialize (no type annotations in {cls})'

    @staticmethod
    def unexpected_key(cls, key):
        return f'Unexpected key `{key}` in {cls}'


class Factory(ABC):
    """An interface for instantiating objects from json-like data.
    """

    def __init__(self, cls: type, errors=ErrorMessages):
        """The `__annotations__` of `cls` are first used to verify input data.

        Arguments
        ---------
        cls: a class
            The `__annotations__` of `cls` are first used to verify input data.

        errors: ErrorMessages
            Can be replaced by a custom error message class.
            Note that errors messages can be specific for a given field in `cls`.

        Examples
        --------
        E.g. cls can be a dataclass:
        ```py
        class User:
            email: str
            age: int = 0
        ```
        """
        self.cls = cls
        self.errors = errors

    def build(self, data={}):
        """Initialize `self.cls` with fields from `data`.
        All child objects are recursively instantiated as well, based on type annotations.

        See object_parser_example.py for a larger usecase example.

        Raises
        ------
        - SpecError (for a single field) 
        - SpecErrors (for multiple invalid fields).

        User-defineable methods
        -----------------------
        See the class `Spec` below for an example.

        Process values
        - `cls.parse_value()` can be used to pre-process input values before instantiating objects
        - `cls.__post_init__()` can be used to check an object after initialization

        Processing of keys
        - `cls.parse_key()` can be used to pre-process input keys.
        - `cls.verify_key_format()` defaults to verify_key_format
        - `cls._key_synonyms: dict` can be used to define alternative keys
        """

        parsed_data = self.parse_value(data)
        instance = self.build_instance(parsed_data)

        if has_method(self.cls, '__post_init__'):
            instance.__post_init__()

        return instance

    def parse_value(self, value) -> object:
        """Use the optional method "parse_value" in `cls` to parse a value.
        """
        if has_method(self.cls, 'parse_value'):
            return self.cls.parse_value(value)

        return value

    @abstractmethod
    def build_instance(self, data) -> object:
        """Build an instance of `self.cls`, after parsing input data but before finializing.
        """
        pass

    ############################################################################
    # Helpers
    #
    # These methods restrict how this class can be used.
    ############################################################################

    def verify_key_format(self, key: str):
        """Verify key format.
        Either using the optional method "parse_value" in `cls`, or otherwise
        using a default verification.
        """
        if has_method(self.cls, 'verify_key_format'):
            self.cls.verify_key_format(key)

    def find_synonym(self, key: str) -> str:
        """Use the optional field "_key_synonyms" in `self.cls` to translate a key.
        """
        find_synonym(self.cls, key)


class JSONFactory(Factory):
    def build_instance(self, data) -> object:
        """Init either a `dataclass, list, Enum` or custom class.
        """
        # if has_method(data, 'items'):
        #     return {}

        if has_method(data, 'items'):
            fields = self.build_fields(data)
            return self.build_from_dict(fields)

        elif isinstance(self.cls, _GenericAlias):
            return self.build_list(data)

        if is_enum(self.cls):
            return self.build_enum(data)

        return self.build_object(data)

    ############################################################################
    # Internals
    ############################################################################

    def build_fields(self, data={}) -> dict:
        """Instantiate all fields in `cls`, based its type annotations and the values in `data`.
        """
        data = parse_field_keys(self.cls, data)

        result = {}
        if not data:
            return result

        elif getattr(self.cls, '_name', '') in ['Dict', 'List']:
            keys = data.keys()
            # TODO handle data: list

        elif not has_annotations(self.cls):
            raise SpecError(self.errors.no_type_annotations(self.cls))

        else:
            keys = self.cls.__annotations__.keys()

        errors = []
        for key in keys:
            # (before finalization) fields are independent, hence multiple errors can be collected
            try:
                result[key] = self.build_field(key, data)
            except SpecError as e:
                errors.append(e)

        if errors:
            raise SpecErrors(errors)

        return result

    def build_field(self, key, data):
        if key in data:
            self.verify_key_format(key)

            if has_annotations(self.cls):
                inner_cls = self.cls.__annotations__[key]
            else:
                inner_cls = infer_inner_cls(self.cls)

            factory = JSONFactory(inner_cls)
            return factory.build(data[key])

        elif hasattr(self.cls, key):
            return getattr(self.cls, key)

        raise SpecError(self.errors.missing_mandatory_key(self.cls, key))

    def build_from_dict(self, fields: dict):
        if hasattr(self.cls, '__dataclass_fields__'):
            return self.cls(**fields)

        if getattr(self.cls, '_name', '') in ['Dict', 'List']:
            return list(fields.values())

        if issubclass(self.cls, Spec):
            instance = super(Spec, self.cls).__new__(self.cls)
        else:
            instance = self.cls()

        if has_annotations(self.cls):
            # assume instance of Spec
            for k in self.cls.__annotations__:
                if k not in fields:
                    raise SpecError()
                setattr(instance, k, fields[k])

        return instance

    def build_list(self, items: list) -> list:
        if len(self.cls.__args__) != 1:
            raise NotImplementedError()

        list_item = self.cls.__args__[0]
        factory = JSONFactory(list_item)
        return [factory.build(v) for v in items]

    def build_enum(self, value) -> Enum:
        if has_method(self.cls, 'parse_value'):
            value = self.cls.parse_value(value)

        try:
            return self.cls[value]
        except KeyError:
            raise SpecError(f'Invalid value for {self.cls}(Enum)')

    def build_object(self, data) -> object:
        if has_method(self.cls, 'parse_value'):
            data = self.cls.parse_value(data)

        return self.cls(data)


################################################################################
# Helpers
################################################################################


def parse_field_keys(cls, data) -> dict:
    # note that dict comprehensions ignore duplicates
    return {parse_field_key(cls, k): v for k, v in data.items()}


def parse_field_key(cls, key: str) -> str:
    if getattr(cls, '_name', '') in ['Dict', 'List']:
        if cls._name == 'Dict':
            inner_cls = cls.__args__[1]
        elif cls._name == 'List':
            inner_cls = cls.__args__[0]

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

###############################################################################
# Exceptions
###############################################################################


class SpecError(Exception):
    pass


class SpecErrors(SpecError):
    pass


class BuildError(SpecError):
    pass


class BuildErrors(SpecError):
    pass

###############################################################################
# Legacy
###############################################################################


def init_recursively(cls, data={}):
    fields: dict = init_values(cls, data)

    if hasattr(cls, '__dataclass_fields__'):
        instance = cls(**fields)

    else:
        if issubclass(cls, Spec):
            instance = super(Spec, cls).__new__(cls)
        else:
            instance = cls()

        if has_annotations(cls):
            # assume instance of Spec
            for k in cls.__annotations__:
                if k not in fields:
                    raise SpecError()
                setattr(instance, k, fields[k])

    if has_method(cls, '__post_init__'):
        instance.__post_init__()

    return instance


def init_values(cls, data: dict) -> dict:
    """Instantiate all values in `data`, based on the type annotations in `cls`.
    """
    data = parse_field_keys(cls, data)

    result = {}
    if not data:
        return result
    elif not has_annotations(cls):
        raise SpecError(ErrorMessages.no_type_annotations())

    for key in cls.__annotations__:
        result[key] = _init_field(cls, key, data)

    return result


def _init_field(cls, key, data):
    if key in data:
        return init(cls.__annotations__[key], data[key])
    elif hasattr(cls, key):
        return getattr(cls, key)

    raise SpecError(ErrorMessages.missing_mandatory_key(cls, key))


def init(cls, args):
    if isinstance(cls, _GenericAlias):
        # assume this is a typing.List
        if len(cls.__args__) != 1:
            raise NotImplementedError

        list_item = cls.__args__[0]
        return [list_item(v) for v in args]

    if has_method(cls, 'parse_value'):
        args = cls.parse_value(args)

    if is_enum(cls):
        try:
            return cls[args]
        except KeyError:
            raise SpecError(f'Invalid value for {cls}(Enum)')

    try:
        obj = cls(args)

    except ValueError as e:
        raise SpecError(e)

    if has_method(cls, '__post_init__'):
        obj.__post_init__()

    return obj


def verify_key_format(cls, key: str):
    if not is_alpha(key[0]) or not is_alphanumerical(key, ignore='_'):
        raise SpecError(ErrorMessages.invalid_key_format(cls, key))


class Spec():
    """Example class

    Initialize with either:
    ```py
    Spec( {'a': 1, 'b': 2} )
    Spec(a=1, b=2)
    ```

    See object_parser_example.py for a larger usecase as an example.
    """

    _key_synonyms = {}

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
    def parse_value(value):
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
        return verify_key_format(cls, key)

    def items(self):
        return {k: getattr(self, k) for k in self.__annotations__}

    ############################################################################
    # Internals
    ############################################################################

    def __new__(cls, data={}, **kwds):
        """ Generic constructor that validates the keys before initializing the object.
        """
        if data:
            # merge all arguments
            kwds.update(data)
        return init_recursively(cls, kwds)

    def __repr__(self) -> str:
        cls = str(self.__class__)[1:-1]
        repr = f'<{cls} object at {hex(id(self))}>'
        data = vars(self)
        return f'{repr} {data}'
