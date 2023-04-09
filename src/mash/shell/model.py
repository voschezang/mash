from collections import UserString
from dataclasses import dataclass
import logging
import re
import shlex
import subprocess
from typing import Iterable, List
from mash.shell import delimiters
from mash.io_util import log
from mash.shell.delimiters import DEFINE_FUNCTION, FALSE, IF, INLINE_ELSE, INLINE_THEN, THEN, TRUE
from mash.shell.errors import ShellError, ShellSyntaxError
from mash.shell.function import InlineFunction
from mash.shell.if_statement import LINE_INDENT, Abort, State, close_prev_if_statement, close_prev_if_statements, handle_else_statement, handle_prev_then_else_statements, handle_then_statement
from mash.shell.parsing import expand_variables, indent_width, to_bool, to_string
from mash.util import has_method, quote_all, translate_items

LAST_RESULTS = '_last_results'
LAST_RESULTS_INDEX = '_last_results_index'

################################################################################
# Units
################################################################################


@dataclass
class ReturnValue:
    data: str


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
        width = self.indent
        inner = self.data
        if inner is None:
            return

        if shell.locals[IF]:
            if lazy:
                raise NotImplementedError()

            closed = shell._last_if['branch'] in (INLINE_THEN, INLINE_ELSE)

            if width < shell._last_if['line_indent'] or (
                    width == shell._last_if['line_indent'] and
                    not isinstance(inner, Then) and
                    not isinstance(inner, Else)):

                close_prev_if_statements(shell, width)

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
    def run(self, prev_result='', shell=None, lazy=False):
        args = shell.run_commands(self.data, prev_result)

        if lazy:
            return ['math'] + args

        line = ' '.join(quote_all(args,
                                  ignore=list('*$<>') + ['>=', '<=']))
        # return shell.eval_math(line)
        return self.eval(line, shell.env)

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
    def run(self, prev_result='', shell=None, lazy=False):
        result = shell.run_commands(self.data, run=not lazy)
        return ReturnValue(result)


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
            return run_shell_command(line, prev_result, delimiter=None)
        return ' '.join(line)


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
# Infix Operator Expressions
################################################################################


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
        return f'`{self.op}`'


class Assign(Infix):
    @property
    def key(self):
        return self.lhs

    @property
    def value(self):
        return self.rhs

    def run(self, prev_result='', shell=None, lazy=False):
        k = shell.run_commands(self.key)

        if self.op == '=':
            v = shell.run_commands(self.value)
            if not lazy:
                shell.set_env_variables(k, v)
                return
            return k, self.op, v

        values = shell.run_commands(self.value, run=not lazy)

        if values is None:
            values = ''

        if str(values).strip() == '' and shell._last_results:
            values = shell._last_results
            shell.env[LAST_RESULTS] = []

        if not lazy:
            shell.set_env_variables(k, values)
            return
        return k, self.op, values


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

        next = run_shell_command(line, prev, delimiter=self.op)
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
        agg = delimiter.join(str(r) for r in results)
        if agg.strip() == '':
            return ''

        return delimiter.join(quote_all(results))


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
        value = to_bool(value)
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
    def run(self, prev_result='', shell=None, lazy=False):
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
        items = self.values
        if len(items) >= 2 and not lazy:
            k, *args = items
            if k == 'map':
                args = Terms(list(args))
                return Map.map(args, prev_result, shell)
            elif k == 'foreach':
                args = Terms(list(args))
                return shell._do_foreach(args, prev_result)
            elif k in ['reduce', 'foldr']:
                return shell.foldr(args, prev_result)

        # TODO expand vars in other branches as well
        wildcard_value = ''
        if '$' in items:
            wildcard_value = prev_result
            prev_result = ''

        items = list(expand_variables(items, shell.env,
                                      shell.completenames_options,
                                      shell.ignore_invalid_syntax,
                                      wildcard_value))

        k = items[0]

        if not lazy:
            if k == 'echo':
                args = items[1:]
                if prev_result:
                    args += [prev_result]
                line = ' '.join(str(arg) for arg in args)
                return line

            if shell.is_function(k):
                # TODO if self.is_inline_function(k): ...
                # TODO standardize quote_all args
                line = ' '.join(quote_all(items, ignore='*$?'))
                return shell.pipe_cmd_py(line, prev_result)

        if prev_result:
            items += [prev_result]
        if not lazy:
            return ' '.join(str(v) for v in items)
        return items


class Lines(Nodes):
    def run(self, prev_result='', shell=None, lazy=False):
        shell.locals.set(LINE_INDENT, indent_width(''))

        for item in self.values:

            width = indent_width('')
            if shell.locals[IF] and not isinstance(item, Indent) and width > shell._last_if['line_indent']:
                close_prev_if_statements(shell, width)

            if shell.locals[IF] and not isinstance(item, Indent):
                if not isinstance(item, Then) and \
                        not isinstance(item, ElseCondition):
                    close_prev_if_statement(shell)

            result = shell.run_commands(item, run=not lazy)

            if isinstance(result, ReturnValue):
                return result.data

            if isinstance(result, list):
                # result = ' '.join(quote_all(result))
                # result = ' '.join(str(s) for s in result)
                result = str(result)

            if result is not None:
                if result or not shell.locals[IF]:
                    print(to_string(result))

    @property
    def data(self):
        return ', '.join(str(v) for v in self.values)

################################################################################
# Function Definitions
################################################################################


class FunctionDefinition(Node):
    def __init__(self, f, args=None, body=None):
        self.f = f
        self.args = [] if args is None else args
        self.body = body

    def run(self, prev_result='', shell=None, lazy=False):
        args = self.define_function(shell, lazy)

        # TODO use line_indent=self.locals[RAW_LINE_INDENT]
        shell.locals.set(DEFINE_FUNCTION,
                         InlineFunction('', args, func_name=self.f))
        shell.prompt = '>>>    '

    def define_function(self, shell, lazy: bool):
        if lazy:
            raise NotImplementedError()

        args = self.args
        if args:
            args = shell.run_commands(args)

        if has_method(shell, f'do_{self.f}'):
            raise ShellError()
        elif shell.is_function(self.f):
            logging.debug(f'Re-define existing function: {self.f}')

        if shell.auto_save:
            logging.warning(
                'Instances of InlineFunction are incompatible with serialization')
            shell.auto_save = False

        return args

    @property
    def data(self):
        return f'{self.f}( {self.args} )'


class InlineFunctionDefinition(FunctionDefinition):
    def run(self, prev_result='', shell=None, lazy=False):
        args = self.define_function(shell, lazy)

        # TODO use parsing.expand_variables_inline
        shell.env[self.f] = InlineFunction(self.body, args, func_name=self.f)

################################################################################
# Functions
################################################################################


def run_shell_command(line: str, prev_result: str, delimiter='|') -> str:
    """
    May raise subprocess.CalledProcessError
    """
    assert delimiter in delimiters.bash or delimiter is None

    if delimiter == '>-':
        delimiter = '>'

    if delimiter is not None:
        # pass last result to stdin
        line = f'echo {shlex.quote(prev_result)} {delimiter} {line}'

    logging.info(f'Cmd = {line}')

    result = subprocess.run(line,
                            capture_output=True,
                            check=True,
                            shell=True)

    stdout = result.stdout.decode().rstrip('\n')
    stderr = result.stderr.decode().rstrip('\n')

    log(stderr)
    return stdout
