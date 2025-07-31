from __future__ import annotations
from collections import UserString

from mash.shell.errors import ShellError
from mash.shell2.ast.term import Term
from mash.shell2.env import Environment


class Variable(Term, UserString):
    def run(self, env: Environment) -> Term:
        k = self.value
        try:
            if k in env:
                return env[k]
        except TypeError:
            pass

        raise ShellError(
            f"Cannot resolve variable {k} in current environment.")

    def __repr__(self) -> str:
        return '$' + self.value

    @property
    def data(self):
        return repr(self)

    @property
    def type(self) -> str:
        return 'variable'

    @classmethod
    def zero(cls) -> Variable:
        return cls('')
