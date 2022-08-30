from collections.abc import Sequence
from dataclasses import dataclass
import nltk
from nltk.metrics.distance import edit_distance
from typing import Dict, List, Tuple

# backwards compatibility
from io_util import parse_args, parser, debug, interactive


AdjacencyList = Dict[str, List[str]]


class DataClassHelper:
    """Methods that mutate dataclass fields.
    """

    def __init__(self, data: dataclass):
        self._context = data

    def ensure_field(self, key: str):
        self.verify_context_key(key)

        # first infer dependencies
        if self._context.direct_dependencies:
            deps = infer_dependencies(self._context.direct_dependencies, key)
            for dependency in set(deps):
                self.ensure_field(dependency)

        if getattr(self._context, key) is None:
            self.set_field(key)

    def set_field(self, key: str):
        self.verify_context_key(key)
        msg = f'Missing context: {key}'

        if not interactive:
            raise ValueError(msg)

        print(msg)
        value = input(f'--> set {key} ')
        setattr(self._context, key, value)

    def verify_context_key(self, key):
        assert key in self._context.__dataclass_fields__


def decorate(decoratee: dataclass, cls: object):
    """Adapt a class instance to have an hasA and isA relationships with `cls`.
    See https://en.wikipedia.org/wiki/Decorator_pattern
    """

    setattr(decoratee, 'decorated_' + type(cls).__name__, cls)

    # add aliassed methods of decoratee to context
    for key in dir(cls):
        if key.startswith('_'):
            continue

        if hasattr(decoratee, key):
            a = decoratee.__name__ if hasattr(decoratee, '__name__') else \
                type(decoratee).__name__
            b = type(cls).__name__
            raise NotImplementedError(
                f'Name conflict for key `{key}` in classes: {a}, {b}')

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


################################################################################
# Operations for lists and sequences
################################################################################


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
    """Fill queue `q` with items, similar to list.extend

    Parameters
    ----------
        w : queue.Queue or asyncio.Queue
    """
    for item in items:
        # Note that put_nowait is compatible with threading.Queue and asyncio.Queue
        q.put_nowait(item)


def find_fuzzy_matches(element: str, elements: List[str]):
    """Yield elements that are most similar.
    Similarity is based on the Levenshtein edit-distance.
    """
    if element in elements:
        # yield eagerly
        yield element
        elements.remove(element)

    scores: List[Tuple[str]] = []

    for i, other in enumerate(elements):
        score = edit_distance(element, other)
        scores.append((score, other))

    ordered = [value for _, value in sorted(scores)]
    yield from ordered


def list_prefix_matches(element: str, elements: List[str]):
    """Yields all elements that are equal to a prefix of `element`.
    Elements with better matches are chosen first.
    """
    prev_matches = set()
    for i in range(max(1, len(element)), 0, -1):
        prefix = element[:i]
        for other in elements:
            if other in prev_matches:
                continue

            if other.startswith(prefix):
                prev_matches |= {other}
                yield other


def find_prefix_matches(element: str, elements: List[str]):
    """Yields all elements that are equal to a prefix of `element`.
    Elements with better matches are chosen first.

    Raise a ValueError when no matches are found.
    """
    # TODO rm this cache and the corresponding ValueError
    iter = list_prefix_matches(element, elements)
    i = -1
    for i, match in enumerate(iter):
        yield match

    if i == -1:
        preview = ', '.join(elements[:3])
        raise ValueError(
            f'{element} is not a prefix of any of the given items [{preview}, ..]')


################################################################################
# Inspection helpers
################################################################################


def rename(func, new_name: str):
    func.__name__ = new_name
    func.__qualname__ = new_name


def has_method(cls, method) -> bool:
    return hasattr(cls, method) and is_callable(getattr(cls, method))


def is_callable(method) -> bool:
    return hasattr(method, '__call__')

################################################################################
# Pure functions
################################################################################


def identity(value):
    return value


def constant(value):
    """Returns a constant function
    """
    def K(*args):
        return value
    return K


def none():
    """Do nothing
    """
    pass
