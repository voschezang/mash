from __future__ import annotations
from collections import UserString
from functools import singledispatchmethod
from typing import Callable, Iterable, Tuple, Type

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

    @singledispatchmethod
    def __eq__(self, other) -> bool:
        return self.value == other

    @__eq__.register
    def _(self, other: Data) -> bool:
        return isinstance(other, Term) and self.value == other.value

    @__eq__.register
    def _(self, other: Node) -> bool:
        return False


class Boolean(Term):
    def __init__(self, value: bool | str):
        if isinstance(value, bool):
            self.value = value
        elif value.lower() == 'true':
            self.value = True
        else:
            self.value = False

    def run(self, env: Environment) -> Boolean:
        return self

    @property
    def type(self) -> str:
        return 'bool'

    def __bool__(self) -> bool:
        return self.value

    def __repr__(self) -> str:
        return repr(self.value).lower()


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

    @classmethod
    def cast(cls, node: Node) -> Word:
        if isinstance(node, Word):
            return Word(node.value)

        if isinstance(node, Number):
            return Word(str(node.value))

        return super().cast(node)


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
    def cast(cls, node: Node) -> Float:
        if isinstance(node, Number):
            return Float(node)

        if isinstance(node, Word):
            return Float(node.value)

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

        if isinstance(node, Word):
            return Integer(node.value)

        return super(cls).cast(node)

    @classmethod
    def zero(cls) -> Integer:
        return Integer(0)


class Cast(Node):
    CASTS = {'int': Integer,
             'float': Float,
             'text': Word}

    def __init__(self, casts: Iterable[Type[Data] | str], term: Node):
        self.casts = list(Cast.convert_casts(casts))
        self.term = term

    def run(self, env: Environment) -> Node:
        term = self.term.run(env)

        for cast in self.casts:
            term = cast.cast(term)

        return term

    def copy(self) -> Cast:
        casts = (cast.instance_type() for cast in self.casts)
        return Cast(casts, self.term.copy())

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

    @staticmethod
    def convert_casts(casts: Tuple[str]) -> Iterable[Type[Data] | str]:
        for c in casts:
            if c in Cast.CASTS:
                yield Cast.CASTS[c]
            elif c in ('str', 'word'):
                raise ShellTypeError(
                    f'Cast "{c}" is not supported. Did you mean "text"?')
            else:
                raise ShellTypeError(f'Cast "{c}" is not supported.')
