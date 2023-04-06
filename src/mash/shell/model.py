from collections import UserString
from typing import Iterable, List
from mash.shell import delimiters
from mash.shell.delimiters import FALSE, IF, INLINE_ELSE, INLINE_THEN, THEN, TRUE, to_bool
from mash.shell.if_statement import LINE_INDENT, Abort, State, handle_else_statement, handle_then_statement
from mash.shell.parsing import expand_variables, indent_width
from mash.util import quote_all

LAST_RESULTS = '_last_results'
LAST_RESULTS_INDEX = '_last_results_index'

################################################################################
# Units
################################################################################


class Node(UserString):
    def __init__(self, data=''):
        # store value transparently
        self.data = data

    def run(self, prev_result='', shell=None, lazy=False):
        if lazy:
            return self.data

        if shell.is_function(self.data):
            return shell.pipe_cmd_py(self.data, prev_result)

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


class Indent(Node):
    def __init__(self, value, indent):
        self.data = value
        self.indent = indent

    def run(self, prev_result='', shell=None, lazy=False):
        return shell.run_handle_indent((self.indent, self.data),
                                       prev_result, run=not lazy)

    def __repr__(self):
        return f'{type(self).__name__}( {repr(self.data)} )'


class Shell(Node):
    def run(self, prev_result='', shell=None, lazy=False):
        terms = shell.run_commands(self.data)
        if isinstance(terms, str) or isinstance(terms, Term):
            line = str(terms)
        else:
            line = ' '.join(terms)

        if line == '' and prev_result == '':
            print('No arguments received for `!`')
            return FALSE

        if not lazy:
            return shell.pipe_cmd_sh(line, prev_result, delimiter=None)
        return ' '.join(line)


class Infix(Node):
    def __init__(self, lhs, rhs, op=None):
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
    def data(self):
        return TRUE


class Pipe(Infix):
    def run(self, prev_result='', shell=None, lazy=False):
        prev = shell.run_commands(self.lhs, prev_result, run=not lazy)
        next = shell.run_commands(self.rhs, prev, run=not lazy)
        return next


class BashPipe(Infix):
    def run(self, prev_result='', shell=None, lazy=False):
        prev = shell.run_commands(self.lhs, prev_result, run=not lazy)
        line = shell.run_commands(self.rhs, run=False)

        # TODO also quote prev result
        if not isinstance(line, str) and not isinstance(line, Term):
            line = ' '.join(quote_all(line, ignore=['*']))

        next = shell.pipe_cmd_sh(line, prev, delimiter=self.op)
        return next


class Map(Infix):
    def run(self, prev_result='', shell=None, lazy=False):
        lhs, rhs = self.lhs, self.rhs
        prev = shell.run_commands(lhs, prev_result, run=not lazy)

        if isinstance(rhs, str) or isinstance(rhs, Term):
            rhs = Terms([rhs])

        return self.map(rhs, prev, shell)

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
        agg = delimiter.join(results)
        if agg.strip() == '':
            return ''

        return delimiter.join(quote_all(results))


class BinaryExpression(Infix):
    def run(self, prev_result='', shell=None, lazy=False):
        if prev_result not in (TRUE, FALSE):
            raise NotImplementedError('prev_result was not empty')

        op = self.op
        a = shell.run_commands(self.lhs, run=not lazy)
        b = shell.run_commands(self.rhs, run=not lazy)

        if op in delimiters.comparators:
            # TODO join a, b
            if not lazy:
                return shell.eval(['math', a, op, b])
            return a, op, b

        if op in '+-*/':
            # math
            if not lazy:
                return shell.eval(['math', a, op, b])
            return a, op, b

        raise NotImplementedError()

    def __repr__(self):
        return f'{type(self).__name__}[{self.op}]( {repr(self.lhs)}, {repr(self.rhs)} )'


class LogicExpression(Infix):
    def run(self, prev_result='', shell=None, lazy=False):
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


################################################################################
# Terms
################################################################################


class Term(Node):
    def __eq__(self, other):
        """Literal comparison
        """
        return self.data == other


class Word(Term):
    def __init__(self, value, string_type=''):
        self.data = value
        self.type = string_type


class Method(Term):
    def run(self, prev_result='', shell=None, lazy=False):
        if not lazy:
            if shell.is_function(self.data):
                return shell.pipe_cmd_py(self.data, prev_result)

            return shell._default_method(str(self.data))

        return super().run(prev_result, shell, lazy)


class Variable(Term):
    def run(self, prev_result='', shell=None, lazy=False):
        if not lazy:
            k = self.data[1:]
            return shell.env[k]

        return super().run(prev_result, shell, lazy)


class Quoted(Term):
    def run(self, prev_result='', shell=None, lazy=False):
        delimiter = ' '
        items = self.data.split(delimiter)
        items = list(expand_variables(items, shell.env,
                                      shell.completenames_options,
                                      shell.ignore_invalid_syntax,
                                      escape=True))
        return delimiter.join(items)


################################################################################
# Conditions
################################################################################


class Condition(Node):
    def __init__(self, condition=None, then=None, otherwise=None):
        self.condition = condition
        self.then = then
        self.otherwise = otherwise
        self.data = '_'


class If(Condition):
    # A multiline if-statement

    def run(self, prev_result='', shell=None, lazy=False):
        if lazy:
            raise NotImplementedError()

        value = shell.run_commands(self.condition, run=not lazy)
        value = to_bool(value) == TRUE


class IfThen(Condition):
    def run(self, prev_result='', shell=None, lazy=False):
        if lazy:
            raise NotImplementedError()

        value = shell.run_commands(self.condition, run=not lazy)
        value = to_bool(value) == TRUE

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
    def run(self, prev_result='', shell=None, lazy=False):
        if lazy:
            raise NotImplementedError()

        result = None
        try:
            # verify & update state
            handle_then_statement(self)
            if self.then:
                result = shell.run_commands(self.then, run=not lazy)
        except Abort:
            pass

        if self.then:
            shell._last_if['branch'] = INLINE_THEN

        return result

    def __repr__(self):
        return f'{type(self).__name__}( {repr(self.then)} )'


class IfThenElse(Condition):
    def run(self, prev_result='', shell=None, lazy=False):
        value = shell.run_commands(self.condition, run=not lazy)
        value = to_bool(value) == TRUE
        line = self.then if value else self.otherwise

        # include prev_result for inline if-then-else statement
        return shell.run_commands(line, prev_result, run=not lazy)


class ElseCondition(Condition):
    pass


class ElseIfThen(ElseCondition):
    def run(self, prev_result='', shell=None, lazy=False):
        if lazy:
            raise NotImplementedError()

        try:
            # verify & update state
            handle_else_statement(shell)
            value = shell.run_commands(self.condition, run=not lazy)
            value = to_bool(value) == TRUE
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
    def run(self, prev_result='', shell=None, lazy=False):
        if lazy:
            raise NotImplementedError()

        try:
            # verify & update state
            handle_else_statement(shell)
            value = shell.run_commands(self.condition, run=not lazy)
            value = to_bool(value) == TRUE
        except Abort:
            value = False

        shell.locals[IF].append(State(shell, value, THEN))
        return

    def __repr__(self):
        return f'{type(self).__name__}( {repr(self.condition)} )'


class Else(ElseCondition):
    def run(self, prev_result='', shell=None, lazy=False):
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

################################################################################
# Containers
################################################################################


class Nodes(Node):
    def __init__(self, values: List[Node]):
        self.values = values

    def __add__(self, nodes: Node):
        # assume type is equal
        self.extend(nodes)
        return self

    def extend(self, nodes: Node):
        self.values += nodes.values

    def __eq__(self, other):
        return self.values == other.values and type(self) == type(other)

    @property
    def data(self):
        return ' '.join(str(v) for v in self.values)


class Terms(Nodes):
    def run(self, prev_result='', shell=None, lazy=False):
        return shell.run_handle_terms([self.values], prev_result, run=not lazy)


class Lines(Nodes):
    def run(self, prev_result='', shell=None, lazy=False):
        shell.locals.set(LINE_INDENT, indent_width(''))
        print_result = True
        return shell.run_handle_lines([self.values], prev_result,
                                      run=not lazy, print_result=print_result)
