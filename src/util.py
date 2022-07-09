
from argparse import RawTextHelpFormatter
from collections.abc import Sequence
from typing import Dict
import argparse
import functools
import logging
import os
import sys
from termcolor import colored

parse_args: argparse.Namespace = None
parser: argparse.ArgumentParser = None

interactive = False


def bold(text: str):
    return colored(text, attrs=['bold'])


@functools.lru_cache(maxsize=1)
def verbosity():
    global parse_args
    if parse_args is not None and 'verbose' in parse_args:
        return parse_args.verbose

    if '-vvv' in sys.argv:
        return 3
    elif '-vv' in sys.argv:
        return 2
    elif '-v' in sys.argv:
        return 1

    return 0


def set_verbosity():
    verbosity.cache_clear()
    v = verbosity()

    default_verbosity_level = 30
    verbosity_level = default_verbosity_level - v * 10

    logger = logging.getLogger()
    logger.setLevel(verbosity_level)


def log(*args, file=sys.stderr, **kwds):
    """Print to stderr
    """
    print(*args, file=file, **kwds)


def debug(*args, **kwds):
    """Similar to logging.debug, but without custom string formatting
    """
    if verbosity():
        log(*args, **kwds)


def set_parser(*args, formatter_class=RawTextHelpFormatter, **kwds):
    global parser
    parser = argparse.ArgumentParser(
        *args, formatter_class=formatter_class, **kwds)


def add_default_args():
    global parser
    if parser is None:
        set_parser()

    parser.add_argument('-v', '--verbose', default=0, action='count')

    if 'unittest' in sys.modules.keys() or 'pytest' in sys.modules.keys():
        parser.add_argument('*', nargs='*')


def add_and_parse_args():
    add_default_args()

    global parser, parse_args
    if parse_args is None:
        parse_args = parser.parse_args()

        # Note that verbosity will also set at the end of this file
        set_verbosity()


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


def confirm(msg='Continue [Y/n]? '):
    """Ask user for confirmation
    Default to yes
    """
    if not interactive:
        return True

    res = input(msg).lower()
    return 'n' not in res


def identity(value):
    return value


def constant(value):
    """Returns a constant function
    """
    def K(*args):
        return value
    return K


def infer_default_and_non_default_args(func):
    args = list(func.__code__.co_varnames)
    n_default_args = len(func.__defaults__) if func.__defaults__ else 0
    n_non_default_args = len(args) - n_default_args
    non_default_args = args[:n_non_default_args]
    default_args = args[n_non_default_args:]
    return non_default_args, default_args


def infer_args(func) -> list:
    non_default_args, default_args = infer_default_and_non_default_args(func)
    return non_default_args + [f'[{a}]' for a in default_args]


def infer_synopsis(func, variables=[]) -> str:
    if not variables:
        variables = infer_args(func)
    return ' '.join([func.__name__] + variables)


def infer_signature(func) -> dict:
    _, default_args = infer_default_and_non_default_args(func)

    def format(k):
        key = k
        if k in default_args:
            key = f'[{k}]'

        if k in func.__annotations__:
            v = func.__annotations__[k].__name__
            return key, f': {v}'

        return key, ''

    pairs = [format(var) for var in func.__code__.co_varnames]
    return {k: v for k, v in pairs}


def generate_parameter_docs(parameters) -> str:
    # explicitly define a tab to allow custom tab-widths
    tab = """
    """[1:]

    # transform dict to a multline string
    lines = (''.join(v) for v in parameters.items())
    parameters = f'\n{tab}{tab}'.join(lines)

    doc = f"""
    Parameters
    ----------
        {parameters}
    """

    # rm first newline
    return doc[1:]


def generate_docs(func, synopsis: str = None, args: Dict[str, str] = None, doc: str = None) -> str:
    if not hasattr(func, '__code__'):
        if synopsis is None and args is None:
            raise NotImplementedError('Cannot infer function signature')

    if args is None:
        args = infer_signature(func)
    if synopsis is None:
        synopsis = infer_synopsis(func, list(args.keys()))
    if doc is None:
        if func.__doc__:
            doc = func.__doc__
        elif args:
            doc = generate_parameter_docs(args)

    # only use doc when non-empty
    if doc:
        return synopsis + '\n\n' + doc
    return synopsis


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


def terminal_size(default=os.terminal_size((80, 100))):
    try:
        return os.get_terminal_size()
    except OSError:
        return default


def has_method(cls, method) -> bool:
    return hasattr(cls, method) and hasattr(getattr(cls, method), '__call__')


set_verbosity()
