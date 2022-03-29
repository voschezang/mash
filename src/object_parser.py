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
    Because all attributes are parsable, all methods must start with an underscore.

    See object_parser_example.py for a larger use case example.
    """

    translations = {}

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

        instance._verify()
        return instance

    def __init__(self, **kwds):
        print(self.__name__)

    @classmethod
    def _init_fields(cls, data: dict) -> dict:
        filtered_kwds = cls._parse_field_keys(data)

        result = {}
        if not filtered_kwds:
            return result
        elif not hasattr(cls, '__annotations__'):
            #raise SpecError(cls._unexpected_key(''))
            raise SpecError(cls._no_type_annotations())

        for key in cls.__annotations__:
            result[key] = cls._init_field(key, filtered_kwds)

        return result

    @classmethod
    def _init_field(cls, key, data):

        if key in data:
            return construct(cls.__annotations__[key], data[key])
        elif hasattr(cls, key):
            return getattr(cls, key)

        raise SpecError(cls._missing_mandatory_key(key))

    def _verify(self):
        """Verify this object.
        Note that this method can do verifications that are based on multiple fields.
        """
        pass

    def __init__(self, data=None, **kwds):
        """"Init
        This stub is included to show which args are used.
        """
        pass

    @classmethod
    def _parse_field_keys(cls, data) -> dict:
        # note that dict comprehensions ignore duplicates
        return {cls._parse_field_key(k): v for k, v in data.items()}

    @classmethod
    def _parse_field_key(cls, key: str):
        cls._validate_key_format(key)

        key = key.lower()
        if hasattr(cls, '__annotations__') and key in cls.__annotations__:
            return key

        return cls._translate_key(key)

    @classmethod
    def _translate_key(cls, key: str):
        for original_key, key_translations in cls.translations.items():
            if key in key_translations:
                return original_key

        raise SpecError(f'Unexpected key `{key}` in {cls}')

    @classmethod
    def _validate_key_format(cls, key: str):
        if not is_alpha(key, ignore='_') or key.startswith('_'):
            raise SpecError(cls._invalid_key_format(key))

    @classmethod
    def _invalid_key_format(cls, key: str):
        return f'Format of key: `{key}` was invalid  in {cls}'

    @classmethod
    def _missing_mandatory_key(cls, key: str):
        return f'Missing mandatory key: `{key}` in {cls}'

    @classmethod
    def _unexpected_key(cls, key):
        return f'Unexpected key `{key}` in {cls}'

    @classmethod
    def _no_type_annotations(cls):
        return f'No fields specified to initialize (no type annotations in {cls})'

    def items(self):
        return {k: getattr(self, k) for k in self.__annotations__}

    def oas(self):
        pass

    def _extend_oas(self, components: dict):
        """Generate a OAS/Swagger component 
        See: [OAS](https://swagger.io/specification/)
        E.g.
        ```yml
        components:
            schemas:
                User:
                    properties:
                        id:
                            type: integer
                        name:
                            type: string
        ```
        """
        t = type(self).__name__
        if t not in components:
            components[t] = {}
            components[t]['properties'] = {}
            if self.__doc__:
                components[t]['description'] = self.__doc__

        for k in self.__annotations__:
            v = getattr(self, k)
            item_type = infer_oas_type(v)

            if isinstance(v, Spec):
                v._extend_oas(components)
                ref = f'$ref: #/components/schemas/{item_type}'
                components[t]['properties'][k] = ref
            if isinstance(v, _GenericAlias) or isinstance(v, list):
                ref = f'$ref: #/components/schemas/{item_type}'
                item_type = infer_oas_type(v[0])
                if isinstance(v[0], Spec):
                    v[0]._extend_oas(components)
                    item_type = f'$ref: #/components/schemas/{item_type}'

                components[t]['properties'][k] = {}
                components[t]['properties'][k]['type'] = 'array'
                components[t]['properties'][k]['items'] = item_type
            else:
                components[t]['properties'][k] = item_type


class SpecError(Exception):
    pass


def construct(cls, args):
    try:
        if issubclass(cls, Enum):
            try:
                return cls[args]
            except KeyError:
                raise SpecError(f'Invalid value for {cls}(Enum)')
    except TypeError:
        pass

    if isinstance(cls, _GenericAlias):
        # assume this is a typing.List
        if len(cls.__args__) != 1:
            raise NotImplementedError
        list_item = cls.__args__[0]
        return [list_item(v) for v in args]

    return cls(args)


# Error Messages


def key_error_msg(key, spec: Spec):
    return f'key: {key} in {spec}'


# Predicates

def is_alpha(key: str, ignore=[]) -> bool:
    return all(c.isalpha() or c in ignore for c in key)
