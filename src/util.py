import os
import logging
import argparse
import functools
import sys

parse_args: argparse.Namespace = None
parser: argparse.ArgumentParser = None


@functools.lru_cache(maxsize=1)
def verbosity():
    global parse_args
    if parse_args is not None and 'verbose' in parse_args:
        return parse_args.verbose

    if '-vvv' in sys.argv:
        return 3
    elif '-vv' in sys.argv:
        return 3
    elif '-v' in sys.argv:
        return 3

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
    # TODO uncomment
    # print(*args, file=file, **kwds)
    print(*args, **kwds)


def debug(*args, **kwds):
    """Similar to logging.debug, but without custom string formatting
    """
    if verbosity():
        log(*args, **kwds)


def add_default_args():
    global parser
    if parser is None:
        parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose', default=0, action='count')

    if 'unittest' in sys.modules.keys() or 'pytest' in sys.modules.keys():
        parser.add_argument('*', nargs='*')


def add_and_parse_args():
    add_default_args()

    global parser, parse_args
    if parse_args is None:
        parse_args = parser.parse_args()

        set_verbosity()


def concat(items=[]):
    """Concatenate items
    """
    return sum(items, [])


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


def terminal_size(default=os.terminal_size((80, 100))):
    try:
        return os.get_terminal_size()
    except OSError:
        return default


set_verbosity()