from copy import deepcopy
from types import TracebackType
from typing import Dict
import logging
import sys
from shell.doc_inference import generate_docs

from io_util import log
import util

# this data is impacts by both the classes Function and Shell, hence it should be global
exception_hint = '(run `E` for details)'

# global cache: sys.last_value and sys.last_traceback don't store exceptions raised in cmd.Cmd
last_exception: Exception = None
last_traceback: TracebackType = None


class ShellFunction:
    def __init__(self, func, func_name=None, synopsis: str = None, args: Dict[str, str] = None, doc: str = None) -> None:
        try:
            self.help = generate_docs(func, synopsis, args, doc)
        except NotImplementedError:
            self.help = ''

        try:
            func = deepcopy(func)
        except TypeError as e:
            logging.debug('Cannot deepcopy `func`:' + e.args[0])

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
