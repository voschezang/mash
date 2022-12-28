from enum import Enum

# language constants to a new file
# TODO mv these to a new module
FALSE = ''
TRUE = '1'

class Python(Enum):
    RETURN = 'return'
    IF = 'if'
    THEN = 'then'
    NEW_COMMAND = ';'
    DEFINE_FUNCTION = ':'
    RIGHT_ASSIGNMENT = '->'
    LEFT_ASSIGNMENT = '<-'
    PIPE = '|>'
    MAP = '>>='
    SET_ENV_VARIABLE = '='
    # ELSE = 'else'
    # AND = 'and'
    # OR = 'or'


# TODO add '<'
bash = ['|', '>', '>>', '1>', '1>>', '2>', '2>>']
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
