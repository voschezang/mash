from abc import ABC, abstractmethod
from mash.shell.errors import ShellError, ShellTypeError
from mash.shell2.env import Environment


class Node(ABC):
    """A node (edge) of an abstract syntax tree (AST).
    """

    @abstractmethod
    def run(self, env: Environment):
        """Returns an instance of Node.
        """
        pass

    @abstractmethod
    def __repr__(self) -> str:
        return repr(super(Node, self))

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @classmethod
    def cast(cls, node):
        raise ShellTypeError(
            f'Cannot cast {node.type} to {cls.instance_type()}')

    @classmethod
    def instance_type(cls) -> str:
        """Returns the .type property of an instance of `cls`.
        """
        return cls.zero().type

    @classmethod
    def zero(cls):
        """Create an instance representing zero or nothingness.
        """
        return cls()
