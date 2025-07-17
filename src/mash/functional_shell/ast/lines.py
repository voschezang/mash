from typing import List
from mash.functional_shell.env import Environment


class Line:
    """

    E.g.

    .. code-block:: sh

        print 1; print 2
    """

    def __init__(self, values: list):
        self.values = values

    def run(self, env: Environment):
        for line in self.values:
            line.run(env)


class Lines:
    """
    E.g.

    .. code-block:: sh

        print 1; print 2
        print outer:
            print inner

    """

    def __init__(self, values: List[Line]):
        self.values = values

    def insert(self, values: List[Line]):
        self.values = [values] + self.values

    def run(self, env: Environment):
        for line in self.values:
            line.run(env)
