from operator import contains
from typing import Tuple
from mash.shell.delimiters import ELSE, IF, THEN
from mash.shell.errors import ShellError
from mash.util import for_any

LINE_INDENT = 'line_indent'


class Abort(RuntimeError):
    pass


class Done(RuntimeError):
    pass


def State(self, value) -> dict:
    return {'value': value,
            'branch': None,
            LINE_INDENT: self.locals[LINE_INDENT]}


def handle_if_statement(self, line: str, prev_result: str) -> str:
    # fix missing THEN in double if
    if self.locals[IF] and self._last_if['branch'] is None:
        self._last_if['branch'] = THEN

    if self.locals[IF] and self._last_if['branch'] == ELSE and self._last_if['value']:
        # case of: if .. else if .. :
        # force value to be false when previous IF was true
        self.locals[IF].append(State(self, None))
        return prev_result
    elif self.locals[IF] and self._last_if['branch'] == THEN and not self._last_if['value']:
        # case of: if .. then if .. then:
        # force value to be false when previous IF was false
        value = False
    else:
        value = self.eval_compare(line)

    self.locals[IF].append(State(self, value))
    return ''


def handle_prev_then_else_statements(self):
    if not self.locals[IF]:
        return

    if self._last_if['branch'] == THEN or self._last_if['branch'] is None:
        handle_then_statement(self, transparent=True)
    elif self._last_if['branch'] == ELSE:
        handle_else_statement(self, transparent=True)


def handle_then_else_statements(self, prefixes: str, prev_result: str) -> Tuple[str, str]:
    if not self.locals[IF]:
        if self.ignore_invalid_syntax:
            raise Done('')
        raise ShellError(
            f'If-then clause requires an {IF} statement (1)')

    try:
        if ELSE in prefixes:
            if prefixes[-1] != ELSE:
                raise ShellError('Nested else is not implemented')
            handle_else_statement(self)
        elif THEN in prefixes:
            handle_then_statement(self)

    except Abort:
        raise Done(prev_result)


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


def close_prev_if_statements(self, prefixes):
    # TODO handle case of both THEN and ELSE in prefixes

    if not self.locals[IF]:
        return

    elif IF in prefixes:
        if self.locals[LINE_INDENT] <= self._last_if[LINE_INDENT]:
            # case of: new, independent if-then
            self.locals[IF].pop()
            close_prev_if_statements(self, prefixes)

    elif THEN not in prefixes:
        if ELSE in prefixes:
            if self.locals[LINE_INDENT][:2] < self._last_if[LINE_INDENT][:2]:
                # case of: unclosed if-then-else
                self.locals[IF].pop()
                close_prev_if_statements(self, prefixes)

        elif self.locals[LINE_INDENT] <= self._last_if[LINE_INDENT]:
            # case of: if-then fully terminated
            self.locals[IF].pop()
