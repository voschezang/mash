from mash.shell.ast.node import Node
from mash.shell.base import BaseShell
from mash.shell.delimiters import FALSE, IF, INLINE_ELSE, INLINE_THEN, THEN, TRUE
from mash.shell.if_statement import Abort, State, handle_else_statement, handle_then_statement
from mash.shell.parsing import to_bool


class Condition(Node):
    def __init__(self, condition=None, then=None, otherwise=None):
        self.condition = condition
        self.then = then
        self.otherwise = otherwise
        self.data = '_'


class If(Condition):
    # A multiline if-statement

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if lazy:
            raise NotImplementedError()

        value = shell.run_commands(self.condition, run=not lazy)
        value = to_bool(value) == TRUE


class IfThen(Condition):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if lazy:
            raise NotImplementedError()

        value = shell.run_commands(self.condition, run=not lazy)
        value = to_bool(value)

        if value and self.then:
            # include prev_result for inline if-then statement
            result = shell.run_commands(self.then, prev_result, run=not lazy)
        else:
            # set default value
            result = FALSE

        branch = THEN if self.then is None else INLINE_THEN
        shell.locals[IF].append(State(shell, value, branch))
        return result


class Then(Condition):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if lazy:
            raise NotImplementedError()

        result = None
        try:
            # verify & update state
            handle_then_statement(shell)
            if self.then:
                result = shell.run_commands(self.then, run=not lazy)
        except Abort:
            pass

        if self.then:
            shell._last_if['branch'] = INLINE_THEN

        return result

    def __repr__(self):
        return f'{type(self).__name__}( {repr(self.then)} )'

    def _handle_close_prev_if_statements(self, shell: BaseShell, width: tuple):
        if width == shell._last_if['line_indent']:
            return
        super()._handle_close_prev_if_statements(shell, width)


class IfThenElse(Condition):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        value = shell.run_commands(self.condition, run=not lazy)
        value = to_bool(value)
        line = self.then if value else self.otherwise

        # include prev_result for inline if-then-else statement
        return shell.run_commands(line, prev_result, run=not lazy)


class ElseCondition(Condition):
    pass


class ElseIfThen(ElseCondition):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if lazy:
            raise NotImplementedError()

        try:
            # verify & update state
            handle_else_statement(shell)
            value = shell.run_commands(self.condition, run=not lazy)
            value = to_bool(value)
        except Abort:
            value = False

        if value and self.then:
            result = shell.run_commands(self.then, run=not lazy)
        else:
            result = None

        branch = THEN if self.then is None else INLINE_THEN
        shell.locals[IF].append(State(shell, value, branch))
        return result


class ElseIf(ElseCondition):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if lazy:
            raise NotImplementedError()

        try:
            # verify & update state
            handle_else_statement(shell)
            value = shell.run_commands(self.condition, run=not lazy)
            value = to_bool(value)
        except Abort:
            value = False

        shell.locals[IF].append(State(shell, value, THEN))
        return

    def __repr__(self):
        return f'{type(self).__name__}( {repr(self.condition)} )'


class Else(ElseCondition):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        if lazy:
            raise NotImplementedError()

        result = None
        try:
            # verify & update state
            handle_else_statement(shell)
            if self.otherwise:
                result = shell.run_commands(self.otherwise, run=not lazy)
        except Abort:
            pass

        if self.otherwise is not None:
            self._last_if['branch'] = INLINE_ELSE
        return result

    def _handle_close_prev_if_statements(self, shell: BaseShell, width: tuple):
        if width == shell._last_if['line_indent']:
            return
        super()._handle_close_prev_if_statements(shell, width)
