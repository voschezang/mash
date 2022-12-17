
# use a dedicated variable to simplify searching
from enum import Enum


RIGHT_ASSIGNMENT = '->'
LEFT_ASSIGNMENT = '<-'


class Python(Enum):
    NEW_COMMAND = ';'
    DEFINE_FUNCTION = ':'
    PIPE = '|>'
    MAP = '>>='


DEFINE_FUNCTION = Python.DEFINE_FUNCTION.value
