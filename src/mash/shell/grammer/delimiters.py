from enum import Enum

from mash.shell.grammer import tokenizer

# language constants to a new file
# TODO mv these to a new module
FALSE = ''
TRUE = '1'

bash = ['|', '>-', '>>', '1>', '1>>', '2>', '2>>']

python = list(tokenizer.operators.keys()) + \
    list(tokenizer.reserved_tokens.keys()) + \
    tokenizer.comparators +\
    tokenizer.delimiters

# python = [o.value for o in Python]
all = bash + python

# use dedicated variables to simplify searching
DEFINE_FUNCTION = ':'
IF = tokenizer.token_values['IF']
THEN = tokenizer.token_values['THEN']
ELSE = tokenizer.token_values['ELSE']
ELSE_IF_THEN = 'else-if-then'
INLINE_THEN = 'inline-then'
INLINE_ELSE = 'inline-else'
