from enum import Enum

# language constants to a new file
# TODO mv these to a new module
FALSE = ''
TRUE = '1'


class Python(Enum):
    RETURN = 'return'
    NEW_COMMAND = ';'
    LEFT_ASSIGNMENT = '<-'
    IF = 'if'
    THEN = 'then'
    DEFINE_FUNCTION = ':'
    RIGHT_ASSIGNMENT = '->'
    PIPE = '|>'
    MAP = '>>='
    SET_ENV_VARIABLE = '='
    # ELSE = 'else'
    # AND = 'and'
    # OR = 'or'


bash = ['|', '>-', '>>', '1>', '1>>', '2>', '2>>']
python = [o.value for o in Python]
all = bash + python

# use dedicated variables to simplify searching
RETURN = Python.RETURN.value
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
