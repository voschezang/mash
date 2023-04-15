from mash.shell.ast.conditions import Condition, Else, ElseCondition, ElseIf, ElseIfThen, If, IfThen, IfThenElse, Then
from mash.shell.ast.function_definition import FunctionDefinition, InlineFunctionDefinition
from mash.shell.ast.infix import Assign, BashPipe, BinaryExpression, LogicExpression, Map, Pipe
from mash.shell.ast.node import Indent, Math, Node, Return, Shell
from mash.shell.ast.nodes import Lines, Nodes, Terms
from mash.shell.ast.term import Method, Quoted, Term, Variable, Word

classes = (Node, Nodes, Term, Terms, Lines, Indent,
           Assign, BashPipe, BinaryExpression, LogicExpression,
           FunctionDefinition, InlineFunctionDefinition,
           Map, Math, Pipe, Return, Shell,
           Word, Method, Quoted, Variable)

conditions = (Condition, If, IfThen, Then,
              ElseCondition, Else, ElseIf, ElseIfThen,
              IfThenElse)
