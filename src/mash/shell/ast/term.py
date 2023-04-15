from mash.shell.internals.if_statement import Abort
from mash.shell.internals.helpers import run_function
from mash.shell.ast.node import Node
from mash.shell.base import BaseShell
from mash.shell.grammer.parsing import expand_variables
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
