

from mash.util import is_callable


class Meta(type):
    """Treat a class as a dict.
    Expose:

    This allows a listing over the classes methods without needing an instance.

    .. code-block:: python

        # membership
        if key in Builtins:
            # key access
            Builtins[key]()

        # iteration
        for method in Builtins:
            print(method)
    """
    def __iter__(cls):
        for key in dir(cls):
            if key.startswith('_'):
                continue

            yield getattr(cls, key)

    def __contains__(cls, key):
        return not key.startswith('_') and key in dir(cls) and is_callable(getattr(cls, key))

    def __getitem__(cls, key):
        if key in cls:
            return getattr(cls, key)

        if key.startswith('__'):
            raise KeyError('Iteration does not support magic methods')

        if key.startswith('_'):
            raise KeyError('Iteration does not support private methods')

        if key in dir(cls):
            raise KeyError(f'{cls}.{key} is not callable for')

        raise KeyError(f'{key} is not a method for {cls}')


class Builtins(metaclass=Meta):
    """Wrapper for all built-in Mash functions.
    """

    @staticmethod
    def print(*args: str):
        print(*args)

    @staticmethod
    def exit(status):
        exit(status)


def is_builtin(method) -> bool:
    return method in dir(Builtins) and not method.startswith('__')
