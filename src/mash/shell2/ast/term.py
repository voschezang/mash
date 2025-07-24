
from collections import UserString
from mash.shell.errors import ShellTypeError
from mash.shell2.ast.node import Node
from mash.shell2.env import Environment
from mash.util import quote


class Term(Node):
    def __init__(self, value: str):
        self.value = value

    def run(self, env: Environment):
        return self

    def __eq__(self, other):
        return self.value == other


class Word(Term, UserString):
    """Wrapper for strings that represent a single word.
    This is a subclass from UserString, so it can be compared to other strings.
    """

    def __repr__(self):
        return quote(self.value)

    @property
    def data(self):
        return self.value

    @property
    def type(self):
        return 'text'


class Float(Term):
    def __init__(self, value: str):
        try:
            self.value = float(value)
        except ValueError:
            raise ShellTypeError(f"Invalid value: {value}")

    def run(self, env: Environment):
        return self

    def __repr__(self):
        return repr(self.value)

    @property
    def type(self):
        return 'float'


class Integer(Float):
    """Integers.
    This is a subclass of Float; it can be used everywhere where a float was needed.
    """

    def __init__(self, value: str):
        try:
            self.value = int(value)
        except ValueError:
            raise ShellTypeError(f"Invalid value: {value}")

        if int(value) != float(value):
            raise ShellTypeError(f"Got float instead of int: {value}")

    @property
    def type(self):
        return 'int'
