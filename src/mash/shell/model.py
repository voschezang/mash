from collections import UserString
from typing import List
from mash.shell.delimiters import FALSE, IF, INLINE_THEN, THEN, TRUE, to_bool
from mash.shell.if_statement import LINE_INDENT, State
from mash.shell.parsing import expand_variables, indent_width

################################################################################
# Units
################################################################################


class Node(UserString):
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


class Term(Node):
    pass


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


class Indent(Node):
    def __init__(self, value, indent):
        self.data = value
        self.indent = indent

    def run(self, prev_result='', shell=None, lazy=False):
        return shell.run_handle_indent((self.indent, self.data),
                                       prev_result, run=not lazy)

    def __repr__(self):
        return f'{type(self).__name__}( {repr(self.data)} )'


class Condition(Node):
    def __init__(self, condition, then=None, otherwise=None):
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


class IfThenElse(Condition):
    def run(self, prev_result='', shell=None, lazy=False):
        value = shell.run_commands(self.condition, run=not lazy)
        value = to_bool(value) == TRUE
        line = self.then if value else self.otherwise

        # include prev_result for inline if-then-else statement
        return shell.run_commands(line, prev_result, run=not lazy)

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
