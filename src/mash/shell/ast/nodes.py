"""
Nodes 
-----

A container class for `Node`'s.
See `shell.grammer.parser <https://voschezang.github.io/mash-docs/modules/shell.grammer.html#module-shell.grammer.parser>`_

.. code-block:: bash

    # Tree
    Lines
    └── Nodes
        └── Node

Node
----

An "edge" of the AST.

Subclasses of `Node`:
        
.. code-block:: bash

    Node
    ├── Condition
    │   ├── ElseCondition
    │   │   ├── Else
    │   │   └── ElseIf
    │   ├── If
    │   ├── IfThen
    │   ├── IfThenElse
    │   └── Then
    ├── Infix
    │   ├── Assign
    │   ├── BashPipe
    │   ├── BinaryExpression
    │   ├── LogicExpression
    │   ├── Map
    │   └── Pipe
    └── Term
        ├── Method
        ├── Quoted
        ├── Variable
        └── Word        

"""

from typing import List

from mash.shell.ast.conditions import ElseCondition, Then
from mash.shell.grammer.literals import IF
from mash.shell.internals.helpers import ReturnValue
from mash.shell.ast.node import Indent, Node
from mash.shell.ast.term import Term
from mash.shell.base import BaseShell
from mash.shell.internals.if_statement import LINE_INDENT, close_prev_if_statements
from mash.shell.grammer.parse_functions import indent_width, to_string


class Nodes(Node):
    """A container class for `Node`'s.
    """

    def __init__(self, values: List[Node]):
        self._values = values

    @property
    def values(self) -> List[str]:
        return self._values

    def __add__(self, nodes: Node):
        # assume type is equal
        self.extend(nodes)
        return self

    def extend(self, nodes: Node):
        self._values += nodes.values

    def __eq__(self, other):
        try:
            return self.values == other.values and type(self) == type(other)
        except AttributeError:
            return False

    @property
    def data(self) -> str:
        return ' '.join(str(v) for v in self.values)


class Terms(Nodes):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        items = self.values

        if len(items) >= 2 and not lazy:
            k, *args = items
            # TODO add "prefix" class, instead of this hack for infix operators
            if k in ['reduce', 'foldr']:
                return shell.foldr(args, prev_result)

        return Term.run_terms(items, prev_result, shell, lazy)


class Lines(Nodes):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        for item in self.values:
            shell.locals.set(LINE_INDENT, indent_width(''))

            width = indent_width('')
            if shell.locals[IF] and not isinstance(item, Indent) and width < shell._last_if['line_indent']:
                close_prev_if_statements(shell, width)

            if shell.locals[IF] and not isinstance(item, Indent):
                if not isinstance(item, Then) and \
                        not isinstance(item, ElseCondition):
                    shell.locals.set(IF, [])

            result = shell.run_commands(item, run=not lazy)

            if isinstance(result, ReturnValue):
                return result.data

            if result is not None:
                if result or not shell.locals[IF]:
                    print(to_string(result))

    @property
    def data(self):
        return ', '.join(str(v) for v in self.values)
