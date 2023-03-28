from collections import UserString
from typing import List
from mash.shell.parsing import expand_variables


class Node(UserString):
    def run(self, prev_result='', shell=None, lazy=False):
        if lazy:
            return self.data

        if shell.is_function(self.data):
            return shell.pipe_cmd_py(self.data, prev_result)

        return str(self.data)


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


class Terms(Node):
    def __init__(self, values: List[Term]):
        self.values = values

    @property
    def data(self):
        return ' '.join(str(v) for v in self.values)

    def run(self, prev_result='', shell=None, lazy=False):
        return shell.run_handle_terms([self.values], prev_result, run=not lazy)
