import ply.lex as lex
import ply.yacc as yacc

tokens = (
    # 'LEFT_ASSIGNMENT',
    # 'NEW_COMMAND',
    # 'PIPE',
    # 'RETURN',
    # 'RIGHT_ASSIGNMENT',
    'BREAK',  # ;
    'COMMENT',
    'DEFINE_FUNCTION',

    'SET_ENV_VARIABLE',  # =
    'INFIX_OPERATOR',  # =
    'RPAREN',  # (
    'LPAREN',  # )

    'METHOD',  # some_method_V1
    'SPECIAL',  # $
    'VARIABLE',  # $x
    'STRING',

    'NUMBER',  # 0123456789
)
reserved = {
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE'
}
tokens += tuple(reserved.values())


def init_lex():
    """
    Token regexes are defined with the prefix `t_`.
    From ply docs:
    - functions are matched in order of specification
    - strings are sorted by regular expression length
    """

    t_BREAK = r'\;'
    t_DEFINE_FUNCTION = r':'

    t_INFIX_OPERATOR = r'==|[=\+\-]'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    t_SPECIAL = r'\$'
    t_VARIABLE = r'\$[a-zA-Z_][a-zA-Z_0-9]*'
    t_STRING = r'[\w\d]+'

    t_ignore = ' \t'
    t_ignore_COMMENT = r'\#.*'

    def t_METHOD(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'METHOD')
        return t

    def t_NUMBER(t):
        r'\d+'
        return t

    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    return lex.lex()


def tokenize(data: str):
    lexer = init_lex()
    lexer.input(data)

    while True:
        token = lexer.token()
        if not token:
            break

        yield token


def parse(text):
    def p_expr_def_inline_function(p):
        'expression : term LPAREN term RPAREN DEFINE_FUNCTION expression'
        p[0] = ('define-inline-function', p[1], p[3], p[6])

    def p_expr_def_function(p):
        'expression : term LPAREN term RPAREN DEFINE_FUNCTION'
        p[0] = ('define-function', p[1], p[3])

    def p_expression_if_then_else(p):
        'expression : IF expression THEN expression ELSE expression'
        _, _if, cond, _then, true, _else, false = p
        p[0] = ('if-then-else', cond, true, false)

    def p_expression_if_then(p):
        'expression : IF expression THEN expression'
        p[0] = ('if-then', p[2], p[3])

    def p_expression_infix(p):
        'expression : expression INFIX_OPERATOR term'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_factor_expr(p):
        'term : LPAREN expression RPAREN'
        p[0] = p[2]

    def p_expression_term(p):
        'expression : term'
        p[0] = p[1]

    def p_term_sequence(p):
        'term : term term'
        p[0] = p[1] + ', ' + p[2]

    def p_term(p):
        """term : NUMBER 
                | VARIABLE 
                | METHOD 
                | STRING
        """
        p[0] = p[1]

    def p_error(p):
        print(f'Syntax error: {p}')

    lexer = init_lex()
    parser = yacc.yacc(debug=0)

    for line in text.splitlines():
        result = parser.parse(line)
        if not line:
            continue

        if result is not None:
            yield result


def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


data = """
echo x
if 1 = 3 then 2 else 3
"""
data = """
 1
"""

result = list(parse(data))
print('out', result)
