"""Utils
- printing
- parsing cli args
"""
import argparse
from dataclasses import dataclass
from termcolor import colored
import argparse
import functools
import logging
import os
import sys
import select
from argparse import ArgumentParser, RawTextHelpFormatter
from io import TextIOBase


shell_ready_signal = '-->'

interactive = False

parse_args: argparse.Namespace = None
parser: argparse.ArgumentParser = None


def bold(text: str):
    return colored(text, attrs=['bold'])


def confirm(msg='Continue [Y/n]? '):
    """Ask user for confirmation
    Default to yes
    """
    if not interactive:
        return True

    res = input(msg).lower()
    return 'n' not in res


def print_shell_ready_signal():
    print(shell_ready_signal)
    sys.stdout.flush()


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

        # Note that verbosity will also be set at the end of this file
        set_verbosity()


# @dataclass
class ArgparseWrapper:
    # parser: ArgumentParser = None
    # parse_args: argparse.Namespace = None

    def __init__(self, *args, formatter_class=RawTextHelpFormatter, **kwds):
        global parser
        if parser is None:
            parser = ArgumentParser(
                *args, formatter_class=formatter_class, **kwds)

        self.parser = parser

    def __enter__(self):
        return self.parser

    def __exit__(self, *_):
        add_and_parse_args()

        global parse_args
        self.parse_args = parse_args


def has_output(stream: TextIOBase = sys.stdin, timeout=0):
    rlist, _, _ = select.select([stream], [], [], timeout)
    return rlist != []


def read_line(stream: TextIOBase, timeout=0, default_value=''):
    if has_output(stream, timeout):
        return stream.readline().decode()

    return default_value


def terminal_size(default=os.terminal_size((80, 100))):
    try:
        return os.get_terminal_size()
    except OSError:
        return default


set_verbosity()
