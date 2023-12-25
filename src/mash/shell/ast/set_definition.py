from itertools import product

from mash.shell.ast.node import Node
from mash.shell.base import BaseShell
from mash.shell.cmd2 import Mode


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
        self.data = str(items)

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        items = []
        for item in self.items.values:
            with shell.use_mode(Mode.COMPILE):
                results = shell.run_commands(item, '', not lazy)

            if results is None:
                return

            if isinstance(results, dict):
                for k, v in results.items():
                    # TODO use values 
                    items.append((str(k),))
            else:
                for row in results:
                    items.append(row.splitlines())

        if lazy:
            return f'{{ {self.items} | {self.condition} }}'

        result = list(self.apply(items, shell))
        return ['\n'.join(c) for c in result]

    def apply(self, items, shell: BaseShell = None):
        """Returns the outer product of a nested list.
        """
        if self.condition is None:
            yield from product(*items)
            return

        if 1:
            # TODO remove
            yield from product(*items)
            return
        for element in product(*items):
            result = shell.run_commands(self.condition, element)
            if result:
                yield element
