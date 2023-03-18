from operator import contains
from typing import Tuple
from mash.shell.delimiters import ELSE, IF, INLINE_THEN, THEN
from mash.shell.errors import ShellError

LINE_INDENT = 'line_indent'


class Abort(RuntimeError):
    pass


def State(self, value, branch=None) -> dict:
    return {'value': value,
            'branch': branch,
            LINE_INDENT: self.locals[LINE_INDENT]}


def handle_prev_then_else_statements(self):
    if not self.locals[IF]:
        return

    if self._last_if['branch'] == THEN or self._last_if['branch'] is None:
        handle_then_statement(self, transparent=True)
    elif self._last_if['branch'] == ELSE:
        handle_else_statement(self, transparent=True)


def handle_then_statement(self, transparent=False):
    if self._last_if['value'] is None:
        raise Abort()

    if not transparent:
        self._last_if['branch'] = THEN

    if not self._last_if['value']:
        raise Abort()

    for state in self.locals[IF][:-1]:
        if (state['value'] and state['branch'] == ELSE) or \
                (not state['value'] and state['branch'] == THEN):
            raise Abort()


def handle_else_statement(self, transparent=False):
    if self._last_if['value'] is None:
        raise Abort()
    elif self._last_if['branch'] is None:
        raise ShellError(
            f'If-then-else clause requires a {THEN} statement (3)')

    if not transparent:
        if not self.locals[IF]:
            raise ShellError(
                f'If-then-else clause requires an {IF} statement (4)')

        self._last_if['branch'] = ELSE

    if self._last_if['value']:
        raise Abort()

    for state in self.locals[IF][:-1]:
        if (state['value'] and state['branch'] == ELSE) or \
                (not state['value'] and state['branch'] == THEN):
            raise Abort()


def close_prev_if_statements(self, width):
    while True:
        close_prev_if_statement(self)
        if not self.locals[IF]:
            break
        if width <= self._last_if['line_indent']:
            # compare width to next if-clause
            break


def close_prev_if_statement(self):
    if self._last_if['branch'] is None:
        raise ShellError(
            'Unexpected indent. If-clause was not closed')

    self.locals[IF].pop()
