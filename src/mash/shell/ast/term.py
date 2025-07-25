"""
Term 
----

.. code-block:: bash

    # Classes
    Term
    ├── Method # f()
    ├── Quoted # "abc"
    ├── Variable # $x
    └── Word # anything else
"""

from logging import debug
from typing import List
from mash.shell.errors import ShellError
from mash.shell.internals.if_statement import Abort
from mash.shell.internals.helpers import run_function
from mash.shell.ast.node import Node
from mash.shell.base import POSITIONALS, BaseShell
from mash.shell.grammer.parse_functions import expand_variables, to_string
from mash.util import quote_all


class Term(Node):
    def __eq__(self, other):
        """Literal comparison
        """
        return self.data == other

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        return Term.run_terms([self.data], prev_result, shell, lazy)

    @staticmethod
    def run_terms(items, prev_result='', shell=None, lazy=False):
        # TODO expand vars in other branches as well
        wildcard_value = ''
        if '$' in items:
            wildcard_value = prev_result
            prev_result = ''

        if items[0] == '?':
            if len(items) == 1:
                line = '?'
            else:
                result = Term.run_terms(items[1:], '', shell, True)
                line = ' '.join(['?'] + result)

            return shell.onecmd_raw(line, prev_result)

        items = items.copy()
        for i, item in enumerate(items):
            try:
                items[i] = item.expand_variable(shell.env)
            except AttributeError:
                pass

        # TODO integrate expansion in the respective classes
        items = list(expand_variables(items, shell.env,
                                      shell.completenames_options,
                                      shell.ignore_invalid_syntax,
                                      wildcard_value))

        k, *args = items
        if prev_result:
            args += [prev_result]

        if not lazy:
            if k == 'echo':
                line = ' '.join(str(arg) for arg in args)
                return line

            try:
                return run_function(k, args, shell)
            except Abort:
                pass

            if shell.is_function(k):
                # TODO if self.is_inline_function(k): ...
                # TODO standardize quote_all args
                line = ' '.join(quote_all(items, ignore='*$?'))
                return shell.onecmd_raw(line, prev_result)

        if prev_result:
            items += [prev_result]
        if lazy:
            return items

        line = ' '.join(str(v) for v in items)
        return shell._default_method(line)

    def expand_variable(self, env: dict):
        return self


class NestedTerm(Term):
    def __init__(self, value: str):
        self.data = value

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        parent, *children = self.values
        if parent not in shell.env:
            raise ShellError(f'Undefined variable: {parent}')

        obj = shell.env[parent]
        for k in children:
            try:
                obj = obj[k]
            except KeyError as e:
                debug(e)
                raise ShellError(f'Invalid variable: {k}')

        return obj

    @property
    def values(self) -> List[str]:
        values = self.data.split('.')

        if self.data[0] == '.':
            values = [None] + values
            values.insert(0, None)

        if self.data[-1] == '.':
            values.append(0)

        return values


class Word(Term):
    def __init__(self, value, string_type=''):
        self.data = value
        # SMELL
        self.type = string_type


class Method(Term):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if not lazy:
            args = [prev_result] if prev_result else []

            try:
                return run_function(self.data, args, shell)
            except Abort:
                pass

            if shell.is_function(self.data):
                return shell.onecmd_raw(self.data, prev_result)

            return shell._default_method(str(self.data))

        return super().run(prev_result, shell, lazy)


class Quoted(Term):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        delimiter = ' '
        items = self.data.split(delimiter)
        items = list(expand_variables(items, shell.env,
                                      shell.completenames_options,
                                      shell.ignore_invalid_syntax,
                                      escape=True))
        return delimiter.join(items)


class Variable(Term):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if not lazy:
            k = self.data[1:]
            return shell.env[k]

        return super().run(prev_result, shell, lazy)


class NestedVariable(Term):
    def __init__(self, keys: list):
        # first key is either a wildcard ($) or a variable
        if keys[0] != '$':
            keys[0] = keys[0][1:]

        self.keys = keys

        data = '.'.join(keys)
        super().__init__(data)

    def expand_variable(self, env: dict):
        trace = []
        for k in self.keys:
            trace.append(k)
            try:
                env = env[k]
            except (KeyError, TypeError) as e:
                debug(e)
                raise ShellError(f'Variable not found: {" ".join(trace)}')

        return PythonData(self, env)


class PositionalVariable(Term):
    # TODO remove unused class
    def __init__(self, i: int, keys: list):
        self.i = int(i)
        self.keys = keys

        data = '$' + '.'.join([str(i)] + keys)
        super().__init__(data)

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if not lazy:
            try:
                if self.i > len(shell.env[POSITIONALS]):
                    raise ShellError(f'Invalid index: {self.data}')

                obj = shell.env[POSITIONALS][self.i]
                for k in self.keys:
                    obj = obj[k]
            except KeyError as e:
                raise ShellError(e)

            return obj

        return super().run(prev_result, shell, lazy)


class PythonData(Term):
    """Wrapper to represent data from environment variables.
    """

    def __init__(self, original: Term, value):
        self.data = value

    def __eq__(self, other):
        """Literal comparison
        """
        return self.original == other

    def __str__(self):
        return to_string(self.data)
