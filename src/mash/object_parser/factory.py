from typing import _GenericAlias
from enum import Enum
from abc import ABC, abstractmethod
import logging

from mash.object_parser.object_parser import find_synonym, parse_field_keys, verify_key_format
from mash.object_parser.errors import BuildError, BuildErrors, ErrorMessages, SpecError
from mash.object_parser.spec import Spec
from mash.util import has_annotations, has_method, infer_inner_cls, is_Dict_or_List, is_Dict, is_List, is_enum


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
        - BuildError (for a single field) 
        - BuildErrors (for multiple invalid fields).

        User-defineable methods
        -----------------------
        See the class `Spec` for an example.

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
        elif not is_Dict_or_List(self.cls):
            # ignore key for containers such as Dict
            verify_key_format(self.cls, key)

    def find_synonym(self, key: str) -> str:
        """Use the optional field "_key_synonyms" in `self.cls` to translate a key.
        """
        find_synonym(self.cls, key)


class JSONFactory(Factory):
    def build_instance(self, data) -> object:
        """Init either a `dataclass, list, Enum` or custom class.
        """
        if isinstance(data, _GenericAlias):
            raise BuildError(
                f'Cannot instantiate class {self.cls} with data {data}')

        if has_method(data, 'items'):
            fields = self.build_fields(data)
            return self.build_from_dict(fields)

        elif isinstance(self.cls, _GenericAlias):
            return list(self.build_list(data))

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

        elif is_Dict_or_List(self.cls):
            # TODO handle type: list
            keys = data.keys()

        elif not has_annotations(self.cls):
            raise BuildError(self.errors.no_type_annotations(self.cls))

        else:
            keys = self.cls.__annotations__.keys()

        errors = []
        for key in keys:
            # (before finalization) fields are independent, hence multiple errors can be collected
            try:
                result[key] = self.build_field(key, data)
            # except BuildError as e:
            except SpecError as e:
                errors.append(e)

        if errors:
            if not is_Dict_or_List(self.cls) or len(errors) == len(keys):
                raise BuildErrors(errors)

        return result

    def build_field(self, key, data):
        if key in data:
            self.verify_key_format(key)

            if has_annotations(self.cls):
                inner_cls = self.cls.__annotations__[key]
            else:
                inner_cls = infer_inner_cls(self.cls)

            factory = JSONFactory(inner_cls)
            if isinstance(data[key], type):
                raise BuildError(
                    f'Data must be instantiated. Types are not supported. Got {data[key]}')

            return factory.build(data[key])

        elif hasattr(self.cls, key):
            return getattr(self.cls, key)

        raise BuildError(self.errors.missing_mandatory_key(self.cls, key))

    def build_from_dict(self, fields: dict):
        if hasattr(self.cls, '__dataclass_fields__'):
            return self.cls(**fields)

        if is_Dict(self.cls):
            return self.build_generic_Dict(fields)

        if is_List(self.cls):
            return list(fields.values())

        if issubclass(self.cls, Spec):
            instance = super(Spec, self.cls).__new__(self.cls)
        else:
            instance = self.cls()

        if has_annotations(self.cls):
            # assume instance of Spec
            for k in self.cls.__annotations__:
                if k not in fields:
                    raise BuildError()

                setattr(instance, k, fields[k])

        return instance

    def build_generic_Dict(self, fields):
        inner_cls = self.cls.__args__[1]
        factory = JSONFactory(inner_cls)
        result = {}
        for k, v in fields.items():
            try:
                result[k] = factory.build(v)
            except BuildErrors as e:
                logging.debug(
                    f'build_list: factory({inner_cls}).build({v}) failed: {e}')

        return result

    def build_list(self, items: list) -> list:
        assert len(self.cls.__args__) == 1

        list_item = self.cls.__args__[0]
        factory = JSONFactory(list_item)
        for v in items:
            try:
                yield factory.build(v)
            except BuildErrors as e:
                logging.debug(
                    f'build_list: factory({list_item}).build({v}) failed: {e}')

    def build_enum(self, value) -> Enum:
        if has_method(self.cls, 'parse_value'):
            value = self.cls.parse_value(value)

        try:
            return self.cls[value]
        except KeyError:
            raise BuildError(f'Invalid value for {self.cls}(Enum)')

    def build_object(self, data) -> object:
        if has_method(self.cls, 'parse_value'):
            data = self.cls.parse_value(data)

        try:
            return self.cls(data)
        except TypeError as e:
            raise BuildError(e)
