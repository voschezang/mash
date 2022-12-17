import re
from braceexpand import braceexpand, UnbalancedBracesError
from dataclasses import dataclass
from enum import Enum
from functools import partial
from itertools import accumulate, dropwhile, takewhile
from scipy.spatial import distance
from operator import contains
from queue import Queue
from typing import Any, Callable, Dict, Generator, Iterable, List, MappingView, Sequence, Tuple, TypeVar, Union
import fnmatch
import sys
import traceback

T = TypeVar('T')

AdjacencyList = Dict[str, List[str]]
GLOB_CHARS = '?*+!{}[]'


class DataClassHelper:
    """Methods that mutate dataclass fields.
    Keep track of dependent fields, and ask for user input to fill them in.
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

        # if not io_util.interactive:
        #     raise ValueError(msg)

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


def crop(s: str, n=100, suffix='..') -> str:
    margin = len(suffix)
    if len(s) <= n + margin:
        return s
    return s[:n] + suffix

################################################################################
# Operations for lists and sequences
################################################################################


def append_list(a: list, b) -> list:
    a = a.copy()
    a.append(b)
    return a


def accumulate_list(items: Iterable[T]) -> Iterable[List[T]]:
    items = accumulate(items, append_list, initial=[])

    # drop the first item
    next(items)

    return items


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


def split_tips(line: str, delimiters: str = ',.') -> Generator[str, None, None]:
    """Split `line` based on `delimiters`.
    """
    if not line:
        # e.g. an empty list or string
        yield line
        return

    i = 0
    for i, char in enumerate(line):
        if char in delimiters:
            yield char
        else:
            break
    else:
        # patch index iff iter is exhausted
        i += 1

    suffixes = []
    j = len(line)
    for j in range(len(line)-1, i, -1):
        char = line[j]
        if char in delimiters:
            suffixes.append(char)
        else:
            break
    else:
        # patch index iff iter is exhausted
        j -= 1

    middle = line[i:j+1]
    if middle:
        yield middle
    yield from suffixes


def split_sequence(items: Sequence[T], delimiters: Sequence[T] = ['\n', ';'],
                   return_delimiters: Union[bool, str] = False, prefixes=[]) -> Generator[List[T], None, None]:
    """An abstraction of list.split.
    Multiple delimiters are supported.

    Paramters
    ---------
    return_delimiters : bool | 'always'
        prefix yielded items with the delimiters that were encountered.
        See [polish notation](https://en.wikipedia.org/wiki/Polish_notation)
        If 'always', then include left-hand side delimiters.
    """
    if not delimiters:
        yield list(items)
        return

    there_are_other_delimiters = len(delimiters) > 1
    delim = delimiters[0]

    if return_delimiters:
        delim_is_present = delim in items
        delim_encountered = False

    prefix_added = False
    buffer = []
    for i, item in enumerate(items):

        if item != delim:
            buffer.append(item)

            if i < len(items) - 1:
                continue

        if buffer:
            # yield results recursively

            if return_delimiters and not prefix_added and delim_is_present:
                if return_delimiters == 'always' or delim_encountered:
                    # extend a copy of prefixes
                    prefixes = prefixes + [delim]
                    prefix_added = True

            if there_are_other_delimiters:
                yield from split_sequence(buffer, delimiters[1:], return_delimiters, prefixes)
            else:
                yield prefixes + buffer

            buffer = []

        if item == delim:
            # set this value after yielding any right-hand side results
            delim_encountered = True


def take(values: Iterable[T], n: int) -> List[T]:
    """Return the first n items
    https://hackage.haskell.org/package/base-4.17.0.0/docs/Prelude.html#v:take
    """
    return (v for i, v in enumerate(values) if i < n)


def group(items: Iterable[T], n: int) -> Iterable[List[T]]:
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


def split_prefixes(items: Sequence[T], prefixes: Sequence[T]) -> Iterable[T]:
    predicate = partial(contains, prefixes)
    return takewhile(predicate, items)


def omit_prefixes(items: Sequence[T], prefixes: Sequence[T]) -> Iterable[T]:
    predicate = partial(contains, prefixes)
    return dropwhile(predicate, items)


def match_words(s: str, prefix='') -> List[str]:
    """Match a words that:
    - starts with a letter
    - contains exclusively alphanumerical chars and underscores

    An optional prefix can be added, e.g. a delimiter.
    """
    return re.findall(prefix + r'[A-Za-z][\w]*', s)


def extend(q: Queue, items: Sequence):
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

    scores: List[Tuple[str, str]] = []

    for i, other in enumerate(elements):
        score = hamming(element, other)
        scores.append((score, other))

    ordered = [value for _, value in sorted(scores)]
    yield from ordered


def find_prefix_matches(element: str, elements: MappingView[str]):
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
        preview = ', '.join(take(elements, 3))
        raise ValueError(
            f'{element} is not a prefix of any of the given items [{preview}, ..]')


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


def glob(value: str, options: List[str] = [], strict=False) -> Iterable[str]:
    """Filter items based on Unix shell-style wildcards
    E.g.
    ```
    w?ldcard
    [a-e]*
    ranges_{1..3}
    options_{a,b,c}
    ```
    """
    try:
        values = braceexpand(value)
    except UnbalancedBracesError as e:
        if strict:
            raise ValueError(e)
        else:
            values = [value]

    if not options:
        yield from values
        return

    options = [str(o) for o in options]

    for value in values:
        matches = list(fnmatch.filter(options, value))
        if matches:
            yield from matches
        else:
            if strict and is_globbable(value):
                raise ValueError(f'No matches found: {value}')
            yield value


def hamming(a: str, b: str) -> float:
    """Approximate the Hamming distance of two strings.
    """
    # add padding
    n = max(len(a), len(b))
    a = f'{a:{n}}'
    b = f'{b:{n}}'

    # add a case-insentive component
    a = a + a.lower()
    b = b + b.lower()
    return distance.hamming(list(a), list(b))

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


def is_enum(cls: type) -> bool:
    try:
        return issubclass(cls, Enum)
    except TypeError:
        pass


def infer_inner_cls(cls=Dict[str, str]):
    if cls._name == 'Dict':
        return cls.__args__[1]
    elif cls._name == 'List':
        return cls.__args__[0]
    raise NotImplementedError()


def extract_exception():
    """
    except AssertionError:
        print(extract_exception())
    """
    _, _, last_traceback = sys.exc_info()
    info = traceback.extract_tb(last_traceback)
    filename, line, func, text = info[-1]
    return filename, line, func, text


################################################################################
# Pure functions
################################################################################


def identity(*values):
    if len(values) == 1:
        return values[0]
    return values


def constant(value):
    """Returns a constant function
    """
    def K(*args):
        return value
    return K


def first(*values):
    return values[0]


def partial_simple(f: Callable, *args, **kwds):
    """Similar to functools.partial.
    Can be can be used converts bound methods to functions.
    """
    def g(*other_args, **other_kwds):
        return f(*args, *other_args, **kwds, **other_kwds)

    doc = '' if f.__doc__ is None else f.__doc__

    g.__doc__ = 'Partial function of f: \n' + doc
    g.__name__ = f'{f.__name__}(..)()'
    return g


def partial_no_args(f, *args):
    """Similar to functools.partial
    """
    def K():
        return f(*args)
    return K


def none(*_):
    """Do nothing
    """
    pass


def flip(f):
    """Similar to functools.partial, but flip the arguments
    """
    def g(*args):
        args = args[::-1]
        return f(*args)
    return g


def lazy_map(func, func_args, generator: Callable[[Any], Iterable], post_func=identity):
    """Apply `func` to the result of `generator()`.
    Apply post_func afterwards.
    """
    def inner(*args, **kwds):
        g = partial(func, func_args)
        items = generator(*args, **kwds)
        return post_func(map(g, items))

    return inner


def call(f, *_):
    """Call f and ignore all other arguments
    """
    return f()

################################################################################
# Predicates
################################################################################


def is_alpha(key: str, ignore=[]) -> bool:
    return all(c.isalpha() or c in ignore for c in key)


def is_alphanumerical(key: str, ignore=[]) -> bool:
    return all(c.isalnum() or c in ignore for c in key)


def is_digit(s: str) -> bool:
    try:
        int(str(s))
        return True
    except ValueError:
        return False


def is_Dict(cls):
    return getattr(cls, '_name', '') == 'Dict'


def is_List(cls):
    return getattr(cls, '_name', '') == 'List'


def is_Dict_or_List(cls):
    return is_Dict(cls) or is_List(cls)


def is_globbable(value: str) -> bool:
    return for_any(GLOB_CHARS, contains, value)


def is_valid_method_name(value: str) -> bool:
    try:
        return (is_alpha(value[0]) or value[0] == '_') \
            and is_alphanumerical(value, ignore='_')
    except TypeError:
        return False


def has_annotations(cls: type) -> bool:
    # hasattr is necessary for < 3.10
    return hasattr(cls, '__annotations__') and cls.__annotations__


def for_any(foreach_items: Sequence, predicate: Callable, *args, **kwds) -> bool:
    """Evaluate whether any item satisfies predicate(*args, item)
    """
    return any(for_each(foreach_items, predicate, *args, **kwds))


def for_all(foreach_items: Sequence, predicate: Callable, *args, **kwds) -> bool:
    """Evaluate whether all item satisfy predicate(*args, item)
    """
    return all(for_each(foreach_items, predicate, *args, **kwds))


def for_each(foreach_items: Sequence, predicate: Callable, *args, **kwds) -> Iterable:
    return (predicate(*args, i, **kwds) for i in foreach_items)


def equals(*args):
    """Return True if args are equal to each other.
    """
    if len(args) <= 1:
        return True

    return all(args[0] == arg for arg in args)


def not_equals(*args):
    """Return True if not all args are equal to each other.
    """
    return not equals(*args)
