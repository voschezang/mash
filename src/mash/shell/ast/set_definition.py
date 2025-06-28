from collections import defaultdict
from itertools import product

from mash.shell.ast.node import Node
from mash.shell.ast.nodes import Terms
from mash.shell.ast.term import Term
from mash.shell.base import BaseShell
from mash.shell.cmd2 import Mode
from mash.shell.internals.helpers import enter_new_scope
from mash.shell.function import InlineFunction


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
        super().__init__(str(items))

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        data = {}
        for item in self.items.values:
            key = shell.run_commands(item, '', lazy)[0]
            key = str(item)

            with shell.use_mode(Mode.COMPILE):
                if key in shell.env:
                    results = shell.env[key]
                else:
                    results = shell.run_commands(item, '', not lazy)

            if results is None:
                continue

            if isinstance(results, dict):
                inner = []
                for k in results:
                    with shell.use_mode(Mode.COMPILE):
                        terms = Terms([Term(key), Term(k)])
                        item = shell.run_commands(terms, '', not lazy)
                    inner.append(item)

            elif isinstance(results, str):
                inner = results.splitlines()
            else:
                inner = list(results)

            data[key] = inner

        # TODO evaluate this condition earlier
        if lazy:
            return f'{{ {self.items} | {self.condition} }}'

        result = list(self.apply(data, shell))
        shell._save_result(result)
        return ''

    def parse_result(self, result):
        keys = ['users', 'documents']
        results = defaultdict(dict)
        for i, row in enumerate(result):
            for k, item in zip(keys, row):
                results[i][k] = item

        return results

    def apply(self, data: dict, shell: BaseShell = None):
        """Returns the outer product of a nested list.
        """
        columns = []
        for k, values in data.items():
            columns.append([{k: v} for v in values])

        if self.condition is None:
            yield from (merge(row) for row in product(*columns))
            return

        for element in product(*columns):
            with enter_new_scope(shell):
                for item in element:
                    for k, v in item.items():
                        f = InlineFunction(v, [], f'do_{k}' )
                        shell.env[k] = f
                        # shell.env[k] = v

                result = shell.run_commands(self.condition, '', run=True)

            if result:
                yield merge(element)

    def __repr__(self):
        if self.condition:
            condition = f'{self.condition.lhs} {self.condition.op} {self.condition.rhs}'
            return f'{type(self).__name__}( {str(self.data)} | {condition} )'
        return f'{type(self).__name__}( {str(self.data)} )'


def merge(dicts: list) -> dict:
    """Merge all items in `dicts` into a single dictionary.
    """
    result = {}
    for entry in dicts:
        for k, v in entry.items():
            result[k] = v
    return result
