from mash.shell.ast.conditions import Else, ElseCondition, ElseIf, ElseIfThen, \
    If, IfThen, IfThenElse, Then
from mash.shell.ast.function_definition import FunctionDefinition, InlineFunctionDefinition
from mash.shell.ast.set_definition import SetDefinition
from mash.shell.ast.infix import Assign, BashPipe, BinaryExpression, LogicExpression, Map, Pipe
from mash.shell.ast.node import Indent, Math, Node, Return, Shell
from mash.shell.ast.nodes import Lines, Nodes, Terms
from mash.shell.ast.term import Method, Quoted, Term, Variable, NestedVariable, PositionalVariable, Word

classes = (Node, Nodes, Term, Terms, Lines, Indent,
           Assign, BashPipe, BinaryExpression, LogicExpression,
           FunctionDefinition, InlineFunctionDefinition, SetDefinition,
           Map, Math, Pipe, Return, Shell,
           Word, Method, Quoted, Variable, PositionalVariable, NestedVariable)

conditions = (If, IfThen, Then,
              ElseCondition, Else, ElseIf, ElseIfThen,
              IfThenElse)
