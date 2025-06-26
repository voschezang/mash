from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from types import TracebackType
from typing import Dict, List
import sys

from mash.doc_inference import generate_docs
from mash.io_util import log, log_once
from mash import util

# this data is impacts by both the classes Function and Shell, hence it should be global
exception_hint = '(run `E` for details)'

# global cache: sys.last_value and sys.last_traceback don't store exceptions raised in cmd.Cmd
last_exception: Exception = None
last_traceback: TracebackType = None

LAST_RESULTS = '_last_results'
LAST_RESULTS_INDEX = '_last_results_index'


class ShellFunction:
    def __init__(self, func, func_name=None, synopsis: str = None, args: Dict[str, str] = None, doc: str = None) -> None:
        try:
            self.help = generate_docs(func, synopsis, args, doc)
        except NotImplementedError:
            self.help = func.__doc__

        try:
            # copy to prevent side-effects
            func = deepcopy(func)
        except TypeError as e:
            name = getattr(func, '__name__', 'func')
            log_once(f'Cannot deepcopy `{name}`: {e.args[0]}')

        self.func = func

        if func_name is not None:
            util.rename(self.func, func_name)

    def __call__(self, args: str = ''):
        args = args.split(' ')
        args = [arg for arg in args if arg != '']

        try:
            return self.func(*args)
        except Exception:
            self.handle_exception()
            return

    def handle_exception(self):
        global last_exception, last_traceback

        etype, last_exception, last_traceback = sys.exc_info()

        log(etype.__name__, exception_hint)
        if str(last_exception):
            log('\t', last_exception)


# TODO rename ShellFunction to ShellMethod, and rename InlineFunction to Function
@dataclass
class InlineFunction:
    command: str
    args: List[str]
    func_name: str
    multiline: bool = False
    line_indent: str = None
    inner: List[str] = field(default_factory=list)

    def __str__(self):
        args = ', '.join(self.args)
        return f'InlineFunction: {self.func_name} ({args})'


def scope() -> dict:
    return defaultdict(dict)
