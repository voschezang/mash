from __future__ import annotations

from mash.shell.errors import ShellError
from mash.shell2.ast.term import Term, Word
from mash.shell2.env import Environment


class Variable(Word):
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
    def type(self) -> str:
        return 'variable'
