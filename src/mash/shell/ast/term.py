"""
Term 
----

.. code-block:: bash

    # Classes
    Term
    ├── Method # f()
    ├── Quoted # "abc"
    ├── Variable $x
    └── Word
"""

from mash.shell.errors import ShellError
from mash.shell.internals.if_statement import Abort
from mash.shell.internals.helpers import run_function
from mash.shell.ast.node import Node
from mash.shell.base import POSITIONALS, BaseShell
from mash.shell.grammer.parse_functions import expand_variables
from mash.util import has_method, quote_all


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
        
        for item in items:
            if isinstance(item, NestedVariable):
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
            if isinstance(item, NestedVariable):
                items[i] = item.expand(wildcard_value)

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


class Word(Term):
    def __init__(self, value, string_type=''):
        self.data = value
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
        self.keys = keys
        data = '$.' + '.'.join(keys)
        super().__init__(data)

    def expand(self, data):
        for k in self.keys:
            data = data[k]

        return data


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
