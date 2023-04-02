from collections import UserString
from typing import List
from mash.shell.base import to_bool
from mash.shell.delimiters import TRUE
from mash.shell.if_statement import LINE_INDENT
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


class Term(Node):
    def __init__(self, value):
        self.data = value

    def run(self, *args, **kwds):
        return self.data


class Word(Node):
    def __init__(self, value, string_type=''):
        self.data = value
        self.type = string_type


class Method(Node):
    def run(self, prev_result='', shell=None, lazy=False):
        if not lazy:
            if shell.is_function(self.data):
                return shell.pipe_cmd_py(self.data, prev_result)

            return shell._default_method(str(self.data))

        return super().run(prev_result, shell, lazy)


class Variable(Node):
    def run(self, prev_result='', shell=None, lazy=False):
        if not lazy:
            k = self.data[1:]
            return shell.env[k]

        return super().run(prev_result, shell, lazy)


class Quoted(Node):
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


class IfThenElse(Node):
    def __init__(self, condition, then, otherwise):
        self.condition = condition
        self.then = then
        self.otherwise = otherwise
        self.data = TRUE

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
