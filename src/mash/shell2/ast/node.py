from abc import ABC, abstractmethod
from mash.shell2.env import Environment


class Node(ABC):
    """A node (edge) of an abstract syntax tree (AST).
    """

    @abstractmethod
    def run(self, env: Environment):
        pass

    @abstractmethod
    def __repr__(self):
        return repr(super(Node, self))

    @abstractmethod
    def __eq__(self, other):
        pass

    @property
    @abstractmethod
    def type(self):
        pass
