from enum import Enum

Bool = str

# language constants to a new file
# TODO mv these to a new module
FALSE = ''
TRUE = '1'

comparators = ['==', '!=', '>', '<', '>=', '<=']


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
    ELSE = 'else'
    SET_ENV_VARIABLE = '='
    INLINE_COMMENT = '#'
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
ELSE = Python.ELSE.value
# AND = Python.AND.value
# OR = Python.OR.value
INLINE_THEN = 'inline-then'
INLINE_ELSE = 'inline-else'


class KeyWords(Enum):
    AND = 'and'
    OR = 'or'


def to_bool(line: str) -> Bool:
    if line != FALSE and line is not None:
        return TRUE
    return FALSE
