FALSE = ''
TRUE = '1'

keywords = {
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'return': 'RETURN',
    'not': 'NOT',
    'and': 'AND',
    'or': 'OR',
    'in': 'IN',
    'math': 'MATH',
}
token_values = {v: k for k, v in keywords.items()}

comparators = ['==', '!=', '>', '<', '>=', '<=']

operators = {'<-': 'left_assignment',
             '->': 'right_assignment',
             '=': 'literal_assignment',
             '|>': 'pipe',
             '>>=': 'map',
             ':': 'define_function',
             ';': 'return'
             }


bash = ['|', '>-', '>>', '1>', '1>>', '2>', '2>>']
python = list(operators.keys()) + list(keywords.keys()) + comparators
all = bash + python

# use dedicated variables to simplify searching
DEFINE_FUNCTION = ':'
IF = token_values['IF']
THEN = token_values['THEN']
ELSE = token_values['ELSE']
ELSE_IF_THEN = 'else-if-then'
INLINE_THEN = 'inline-then'
INLINE_ELSE = 'inline-else'
