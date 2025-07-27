from __future__ import annotations
from abc import abstractmethod
from collections import UserString
from typing import Callable, List

from mash.shell.errors import ShellError, ShellTypeError
from mash.shell2.ast.node import Data, Node
from mash.shell2.env import Environment
from mash.util import quote


class Term(Data):
    """Base class for classes containing variable data.
    Subclasses include Variable, Word, Number.
    """

    def __init__(self, value: str):
        self.value = value

    def run(self, env: Environment) -> Term:
        return self

    def copy(self) -> Term:
        return self.__class__(self.value)

    def __eq__(self, other) -> bool:
        return self.value == other


class Word(Term, UserString):
    """Wrapper for strings that represent a single word.
    This is a subclass from UserString, so it can be compared to other strings.
    """

    def __repr__(self) -> str:
        return quote(self.value)

    @property
    def data(self):
        return self.value

    @property
    def type(self):
        return 'text'

    @classmethod
    def zero(cls) -> Term:
        return Word('')


class Number(Term):
    def __init__(self, value: str, convert: Callable):
        try:
            self.value = convert(value)
        except ValueError:
            raise ShellTypeError(f"Invalid value: {value}")

    def __repr__(self) -> str:
        return repr(self.value)

    @classmethod
    def zero(cls) -> Node:
        """Create an instance representing zero or nothingness.
        """
        return cls()

    @classmethod
    def zero(cls) -> Term:
        return cls(0)


class Float(Number):
    def __init__(self, value: str):
        if isinstance(value, Number):
            # automatically cast to correct value
            value = value.value

        super().__init__(value, float)

    @property
    def type(self):
        return 'float'

    @classmethod
    def cast(self, node: Node) -> Number:
        if isinstance(node, Number):
            return Float(node)

        return super().cast(node)

    @classmethod
    def zero(cls) -> Node:
        return Float(0)


class Integer(Number):
    def __init__(self, value: str):
        if isinstance(value, Number):
            # automatically cast to correct value
            value = value.value

        super().__init__(value, int)

    @property
    def type(self):
        return 'int'

    @classmethod
    def cast(cls, node: Node) -> Integer:
        if isinstance(node, Number):
            return Integer(node)

        return super(cls).cast(node)

    @classmethod
    def zero(cls) -> Integer:
        return Integer(0)


class Cast(Node):
    def __init__(self, casts: List[type], term: Node):
        self.casts = casts
        self.term = term

    def run(self, env: Environment) -> Node:
        term = self.term.run(env)

        for c in self.casts:
            term = c.cast(term)

        return term

    def copy(self) -> Cast:
        return Cast(self.casts, self.term.copy())

    def __repr__(self) -> str:
        return f'{self.type} {repr(self.term)}'

    def __eq__(self, other) -> bool:
        raise ShellError('Cannot compare casts.')

    @property
    def type(self) -> str:
        return ' '.join(f'({cast.instance_type()})' for cast in self.casts)

    @classmethod
    def zero(self) -> Node:
        return Cast([], Integer(0))
