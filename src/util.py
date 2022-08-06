from collections.abc import Sequence
from dataclasses import dataclass
from typing import Dict, List


# backwards compatibility
from io_util import parse_args, parser, debug, interactive


AdjacencyList = Dict[str, List[str]]


def decorate(decoratee: dataclass, cls: object):
    # Adapt an instance of `ContextWrapper` to have hasA & isA relationships with `context`.
    # See https://en.wikipedia.org/wiki/Decorator_pattern

    setattr(decoratee, 'decorated_' + type(cls).__name__, cls)

    # add aliassed methods of decoratee to context
    for key in dir(cls):
        if key.startswith('_'):
            continue

        if hasattr(decoratee, key):
            a, b = type(decoratee).__name__, type(cls).__name__
            raise NotImplementedError(
                f'Name conflict for key {key} in classes {a}, and {b}')

        attr = getattr(cls, key)
        setattr(decoratee, key, attr)

    return decoratee


def infer_dependencies(known_deps: AdjacencyList, key: str):
    if key not in known_deps:
        return

    # yield direct dependencies
    if key in known_deps:
        yield from known_deps[key]

    # yield indirect dependencies
        for other_key in known_deps[key]:
            direct_dependencies = infer_dependencies(known_deps, other_key)
            yield from direct_dependencies


def concat(items: Sequence = []):
    """Concatenate items

    `items` must must be a container or iterable
    """
    try:
        return concat_empty_container(items)
    except TypeError:
        pass

    # in case of list-like container
    for e in (list(), tuple()):
        try:
            return sum(items, e)
        except TypeError:
            continue

    # in case of string-like container
    if isinstance(items, str):
        return ''.join(items)

    iter = items.__iter__()
    acc = next(iter)
    for item in iter:
        try:
            acc |= item
        except TypeError:
            try:
                acc.update(item)
            except TypeError:
                pass

    return acc


def concat_empty_container(items):
    emtpy_containers = (str(), list(), dict(), set(), tuple())
    for e in emtpy_containers:
        if items == e:
            return e

    raise TypeError()


def split(line: str, delimiters=',.'):
    lines = [line]
    for delimiter in delimiters:
        lines = concat([line.split(delimiter) for line in lines if line])
    return [line for line in lines if line]


def identity(value):
    return value


def constant(value):
    """Returns a constant function
    """
    def K(*args):
        return value
    return K


def group(items, n):
    """Group items by chunks of size n.
    I.e. a lazy version of itertools.pairwise with variable groupsize.
    """
    buffer = []
    for item in items:
        buffer.append(item)
        if len(buffer) == n:
            yield buffer
            buffer = []

    yield buffer


def extend(q, items):
    """Fill queue with items, similar to list.extend

    Parameters
    ----------
        w : queue.Queue or asyncio.Queue
    """
    for item in items:
        # Note that put_nowait is compatible with threading.Queue and asyncio.Queue
        q.put_nowait(item)


def rename(func, new_name: str):
    func.__name__ = new_name
    func.__qualname__ = new_name


def has_method(cls, method) -> bool:
    return hasattr(cls, method) and is_callable(getattr(cls, method))


def is_callable(method) -> bool:
    return hasattr(method, '__call__')
