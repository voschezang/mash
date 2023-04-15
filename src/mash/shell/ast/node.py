from collections import UserString
import re
from typing import List
from mash.io_util import log
from mash.shell.base import BaseShell
from mash.shell.grammer.delimiters import FALSE, IF, INLINE_ELSE, INLINE_THEN
from mash.shell.errors import ShellSyntaxError
from mash.shell.if_statement import LINE_INDENT, Abort, close_prev_if_statements, handle_prev_then_else_statements
from mash.shell.helpers import ReturnValue, run_function, run_shell_command
from mash.util import quote_all, translate_items


class Node(UserString):
    """A node of an abstract syntax tree (AST).

    Properties
    ----------
    data : Node or str
        The core data
    values : list
        An iterable version of the core data
    """

    def __init__(self, data=''):
        # store value transparently
        self.data = data

    @property
    def values(self) -> List[str]:
        return [self.data]

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if lazy:
            return self.data

        args = [prev_result] if prev_result else []
        try:
            return run_function(self.data, args, shell)
        except Abort:
            pass

        if shell.is_function(self.data):
            return shell.onecmd_raw(self.data, prev_result)

        return str(self.data)

    def __iter__(self):
        if self.data is None:
            return iter([])
        return iter(self.data)

    def __getitem__(self, i):
        return self.data[i]

    def __repr__(self):
        return f'{type(self).__name__}( {str(self.data)} )'

    def __eq__(self, other):
        return hasattr(other, 'data') and self.data == other.data and type(self) == type(other)

    def _handle_close_prev_if_statements(self, shell: BaseShell, width: tuple):
        if width <= shell._last_if['line_indent']:
            close_prev_if_statements(shell, width)


class Indent(Node):
    def __init__(self, value, indent):
        self.data = value
        self.indent = indent

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        width = self.indent
        inner = self.data
        if inner is None:
            return

        if shell.locals[IF]:
            if lazy:
                raise NotImplementedError()

            closed = shell._last_if['branch'] in (INLINE_THEN, INLINE_ELSE)

            inner._handle_close_prev_if_statements(shell, width)

            if shell.locals[IF] and width > shell._last_if['line_indent']:
                if closed:
                    raise ShellSyntaxError(
                        'Unexpected indent after if-else clause')
                try:
                    handle_prev_then_else_statements(shell)
                except Abort:
                    return prev_result

        shell.locals.set(LINE_INDENT, width)
        return shell.run_commands(inner, prev_result, run=not lazy)

    def __repr__(self):
        return f'{type(self).__name__}( {repr(self.data)} )'


class Math(Node):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        args = shell.run_commands(self.data, prev_result)

        if lazy:
            return ['math'] + args

        line = ' '.join(quote_all(args,
                                  ignore=list('*$<>') + ['>=', '<=']))
        return Math.eval(line, shell.env)

    @staticmethod
    def eval(args: str, env: dict):
        operators = ['-', '\\+', '\\*', '%', '==', '!=', '<', '>']
        delimiters = ['\\(', '\\)']
        regex = '(' + '|'.join(operators + delimiters) + ')'
        terms = re.split(regex, args)
        return Math.eval_terms(terms, env)

    @staticmethod
    def eval_terms(terms: List[str], env) -> str:
        line = ''.join(translate_items(terms, env.asdict()))
        log(line)

        try:
            result = eval(line)
        except (NameError, SyntaxError, TypeError) as e:
            raise ShellSyntaxError(f'eval failed: {line}') from e

        return result


class Return(Node):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        result = shell.run_commands(self.data, run=not lazy)
        return ReturnValue(result)


class Shell(Node):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        terms = shell.run_commands(self.data)
        if isinstance(terms, Node):
            line = terms.data
        if isinstance(terms, list):
            line = ' '.join(terms)
        else:
            line = self.data

        if line == '' and prev_result == '':
            print('No arguments received for `!`')
            return FALSE

        if not lazy:
            return run_shell_command(line, prev_result, delimiter=None)
        return ' '.join(line)
