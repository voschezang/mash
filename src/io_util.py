"""Utils
- printing
- parsing cli args
"""
from argparse import ArgumentParser, RawTextHelpFormatter
from contextlib import redirect_stdout
from io import StringIO
from termcolor import colored
from typing import Callable, List, TextIO, Union
import argparse
import functools
import logging
import os
import select
import subprocess
import sys


shell_ready_signal = '-->'
colored_output = True
interactive = False

parse_args: Union[argparse.Namespace, None] = None
parser: Union[argparse.ArgumentParser, None] = None


def bold(text: str):
    return colored(text, attrs=['bold'])


def warn(text: str):
    return colored(text, 'yellow')


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


def log(*args, file=sys.stderr, prefix=warn('···'), **kwds):
    """Print to stderr
    """
    print(prefix, *args, file=file, **kwds)


def debug(*args, **kwds):
    """Similar to logging.debug, but without custom string formatting
    """
    if verbosity():
        log(*args, **kwds)


def add_default_args(parser: ArgumentParser):
    if parser is None:
        raise NotImplementedError()

    parser.add_argument('-v', '--verbose', default=0, action='count')

    if python_is_run_in_test_mode():
        allow_all_args()


def allow_all_args():
    parser.add_argument('*', nargs='*')


def python_is_run_in_test_mode() -> bool:
    return 'pytest' in sys.modules.keys() or \
        ('unittest' in sys.modules.keys() and 'nltk' not in sys.modules.keys())


class ArgparseWrapper:
    def __init__(self, *args,
                 conflict_handler='resolve',
                 formatter_class=RawTextHelpFormatter, **kwds):
        global parser
        if parser is None:
            parser = ArgumentParser(*args,
                                    conflict_handler=conflict_handler,
                                    formatter_class=formatter_class, **kwds)

            add_default_args(parser)

        self.parser = parser

    def __enter__(self):
        return self.parser

    def __exit__(self, *_):
        # re-raise any exception thrown during setup
        _, exc, _ = sys.exc_info()
        if exc:
            raise

        logging.debug('sys.argv' + str(sys.argv))

        global parse_args
        parse_args = parser.parse_args()
        self.parse_args = parse_args

        # Note that verbosity will also be set at the end of this file
        set_verbosity()


def has_argument(parser: ArgumentParser, arg='arg_name') -> bool:
    return find_argument(parser, arg) is not None


def find_argument(parser: ArgumentParser, arg='arg_name'):
    for action in parser._actions:
        if action.dest == arg:
            return action

    return None


def has_output(stream: TextIO = sys.stdin, timeout=0):
    rlist, _, _ = select.select([stream], [], [], timeout)
    return rlist != []


def read_line(stream: TextIO, timeout=0, default_value=''):
    if has_output(stream, timeout):
        return stream.readline()

    return default_value


def read_file(filename: str):
    return next(read_files([filename]))


def read_files(filenames: List[str]):
    for fn in filenames:
        with open(fn) as f:
            result = f.read()
        yield result


def terminal_size(default=os.terminal_size((80, 100))):
    try:
        return os.get_terminal_size()
    except OSError:
        return default


def catch_output(arg: str, func: Callable, **func_kwds) -> str:
    """Run func while temporarily redirecting stdout.
    Then return the result from stdout.
    """
    out = StringIO()
    with redirect_stdout(out):
        func(arg, **func_kwds)
        result = out.getvalue()

    return result.rstrip('\n')


def run_subprocess(line: str) -> str:
    """Wrapper for subprocess.run
    Raise a RuntimeError on a non-zero exit status.
    """
    result = subprocess.run(line, capture_output=True, shell=True)
    if result.returncode != 0:
        raise RuntimeError(result)
    return result


def check_output(line: str) -> str:
    """Similar to subprocess.check_output, but with more detailed error messages
    """
    result = subprocess.run(line, capture_output=True, shell=True)

    msg = result.stdout.decode(), result.stderr.decode()
    assert result.returncode == 0, msg

    return result.stdout.decode().rstrip('\n')


set_verbosity()
