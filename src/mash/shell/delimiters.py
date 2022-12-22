from enum import Enum


class Python(Enum):
    THEN = 'then'
    NEW_COMMAND = ';'
    IF = 'if'
    DEFINE_FUNCTION = ':'
    RIGHT_ASSIGNMENT = '->'
    LEFT_ASSIGNMENT = '<-'
    PIPE = '|>'
    MAP = '>>='
    SET_ENV_VARIABLE = '='
    # ELSE = 'else'
    # AND = 'and'
    # OR = 'or'


bash = ['|', '>', '>>', '1>', '1>>', '2>', '2>>']
python = [o.value for o in Python]
all = bash + python

# use dedicated variables to simplify searching
DEFINE_FUNCTION = Python.DEFINE_FUNCTION.value
RIGHT_ASSIGNMENT = Python.RIGHT_ASSIGNMENT.value
LEFT_ASSIGNMENT = Python.LEFT_ASSIGNMENT.value
IF = Python.IF.value
THEN = Python.THEN.value
# ELSE = Python.ELSE.value
# AND = Python.AND.value
# OR = Python.OR.value


class KeyWords(Enum):
    AND = 'and'
    OR = 'or'
