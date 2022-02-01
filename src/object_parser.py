from typing import _GenericAlias

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

    See object_parser_example.py for a larger use case example.
    """
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

        instance._validate()
        return instance


    @classmethod
    def _init_fields(cls, data: dict) -> dict:
        filtered_kwds = cls._translate_all_keys(data)

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


    def _validate(self):
        """Validate this Spec
        Note that this method can do validations that are based on multiple fields.
        """
        pass


    def __init__(self, data=None, **kwds):
        """"Init
        This stub is included to show which args are used.
        """
        pass


    @classmethod
    def _translate_all_keys(cls, data) -> dict:
        # note that dict comprehensions ignore duplicates
        return {cls._translate_field_key(k): v for k, v in data.items()}


    @classmethod
    def _translate_field_key(cls, key: str):
        if not is_alpha(key, ignore='_') or key.startswith('_'):
            raise SpecError(cls._invalid_key_format(key))
        return key


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


class SpecError(Exception):
    pass



def construct(cls, args):
    if isinstance(cls, _GenericAlias):
        # assume this is a typing.List
        if len(cls.__args__) != 1:
            raise NotImplementedError
        list_item = cls.__args__[0]
        return [list_item(v) for v in args]

    return cls(args)


### Error Messages

def key_error_msg(key, spec: Spec):
    return f'key: {key} in {spec}'


### Predicates

def is_alpha(key: str, ignore=[]) -> bool:
    return all(c.isalpha() or c in ignore for c in key)

