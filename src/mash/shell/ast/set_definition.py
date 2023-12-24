from itertools import product

from mash.shell.ast.node import Node
from mash.shell.base import BaseShell


class SetDefinition(Node):
    """A set.

    E.g.

    .. code-block:: sh

        # find older users
        { users | users.age > 25 }

        # inner join
        { users documents | users.id = documents.id }

    """

    def __init__(self, items, condition=None):
        self.items = items
        self.condition = condition

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        items = [shell.run_commands(item) for item in self.items]

        if lazy:
            return f'{{ {self.items} | {self.condition} }}'

        return list(self.apply(items, shell))

    def apply(self, items, shell: BaseShell = None):
        if self.condition is None:
            yield from product(*items)
            return

        for element in product(*items):
            result = shell.run_commands(self.condition, element)
            if result:
                yield element
