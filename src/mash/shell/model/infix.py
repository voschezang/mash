from typing import Iterable
from mash.shell.model import delimiters
from mash.shell.model.functions import set_env_variables
from mash.shell.model.term import Term
from mash.shell.model.node import Math, Node, run_shell_command
from mash.shell.model.nodes import Terms
from mash.shell.base import BaseShell
from mash.shell.model.delimiters import FALSE, TRUE
from mash.shell.function import LAST_RESULTS, LAST_RESULTS_INDEX
from mash.shell.parsing import quote_items, to_bool
from mash.util import quote_all


################################################################################
# Infix Operator Expressions
################################################################################


class Infix(Node):
    def __init__(self, lhs: Node, rhs: Node, op=None):
        """An infix operator expression.

        Parameters
        ----------
        lsh : left-hand side
        rsh : right-hand side
        op : operator
        """
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def __eq__(self, other):
        return all((self.lhs == other.lhs,
                   self.rhs == other.rhs,
                   self.op == other.op))

    def __repr__(self):
        f = f'{type(self).__name__}'
        args = f'( {repr(self.lhs)}, {repr(self.rhs)} )'
        if self.op:
            return f'{f}[{self.op}]{args}'
        return f'{f}{args}'

    @property
    def data(self) -> str:
        return f'`{self.op}`'


class Assign(Infix):
    @property
    def key(self) -> Node:
        return self.lhs

    @property
    def value(self) -> Node:
        return self.rhs

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        k = shell.run_commands(self.key)

        if self.op == '=':
            v = shell.run_commands(self.value)
            if not lazy:
                set_env_variables(shell, k, v)
                return
            return k, self.op, v

        values = shell.run_commands(self.value, run=not lazy)

        if values is None:
            values = ''

        if str(values).strip() == '' and shell._last_results:
            values = shell._last_results
            shell.env[LAST_RESULTS] = []

        if not lazy:
            set_env_variables(shell, k, values)
            return
        return k, self.op, values


class BinaryExpression(Infix):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if prev_result not in (TRUE, FALSE):
            raise NotImplementedError('prev_result was not empty')

        op = self.op
        a = shell.run_commands(self.lhs, run=not lazy)
        b = shell.run_commands(self.rhs, run=not lazy)

        line = ' '.join(quote_items([a, op, b]))

        if op in delimiters.comparators:
            if not lazy:
                return Math.eval(line, shell.env)
            return a, op, b

        if op in '+-*/':
            # math
            if not lazy:
                return Math.eval(line, shell.env)
            return a, op, b

        raise NotImplementedError()

    def __repr__(self):
        return f'{type(self).__name__}[{self.op}]( {repr(self.lhs)}, {repr(self.rhs)} )'


class Pipe(Infix):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        prev = shell.run_commands(self.lhs, prev_result, run=not lazy)
        next = shell.run_commands(self.rhs, prev, run=not lazy)
        return next


class BashPipe(Infix):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        prev = shell.run_commands(self.lhs, prev_result, run=not lazy)
        line = shell.run_commands(self.rhs, run=False)

        # TODO also quote prev result
        if not isinstance(line, str) and not isinstance(line, Term):
            line = ' '.join(quote_all(line, ignore=['*']))

        next = run_shell_command(line, prev, delimiter=self.op)
        return next


class Map(Infix):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        prev = shell.run_commands(self.lhs, prev_result, run=not lazy)

        rhs = self.rhs
        if isinstance(rhs, str) or isinstance(rhs, Term):
            rhs = Terms([rhs])

        return self.map(rhs, str(prev), shell)

    @staticmethod
    def map(command, values: str, shell, delimiter='\n') -> Iterable:
        """Apply a function to every line.
        If `$` is present, then each line from stdin is inserted there.
        Otherwise each line is appended.

        Usage
        -----
        ```sh
        println a b |> map echo
        println a b |> map echo prefix $ suffix
        ```
        """
        # monadic bind
        # https://en.wikipedia.org/wiki/Monad_(functional_programming)

        items = shell.parse(values).values

        results = []
        for i, item in enumerate(items):
            shell.env[LAST_RESULTS_INDEX] = i

            results.append(shell.run_commands(command, item, run=True))

        shell.env[LAST_RESULTS_INDEX] = 0
        agg = delimiter.join(str(r) for r in results)
        if agg.strip() == '':
            return ''

        return delimiter.join(quote_all(results))


class LogicExpression(Infix):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        a = shell.run_commands(self.lhs, run=not lazy)
        b = shell.run_commands(self.rhs, run=not lazy)
        if not lazy:
            a = to_bool(a)
            b = to_bool(b)
            if self.op == 'or':
                return a or b
            elif self.op == 'and':
                return a and b

        return ' '.join(quote_all((a, self.op, b), ignore=list('*<>')))
