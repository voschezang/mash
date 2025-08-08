from __future__ import annotations
from abc import ABC, abstractmethod

from mash.shell.errors import ShellError, ShellTypeError
from mash.shell2.env import Environment


class Node(ABC):
    """A node (edge) of an abstract syntax tree (AST).
    """

    @abstractmethod
    def run(self, env: Environment) -> Node:
        """Returns an instance of Node.
        """
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class Data(Node):
    """A node representing a Mash datastructure. 
    E.g. a Variable, Word or ArrayList.
    """

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @classmethod
    def zero(cls) -> Data:
        """Create an instance representing zero or nothingness.
        E.g. an empty string or list.

        Adding zero should not change a value.
        Multiplying with zero results in zero.
        """
        raise ShellError('Data.zero() is not supported.')

    @classmethod
    def cast(cls, node) -> Node:
        raise ShellTypeError(
            f'Cannot cast {node.type} to {cls.instance_type()}')

    @classmethod
    def instance_type(cls) -> str:
        """Returns the .type property of an instance of `cls`.
        """
        return cls.zero().type

    def __bool__(self):
        raise NotImplementedError()
