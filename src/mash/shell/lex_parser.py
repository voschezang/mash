import ply.lex as lex
import ply.yacc as yacc

tokens = (
    # 'RETURN',
    # 'NEW_COMMAND',
    # 'LEFT_ASSIGNMENT',
    # 'IF',
    # 'THEN',
    # 'RIGHT_ASSIGNMENT',
    # 'PIPE',
    # 'ELSE',
    'BREAK',  # ;
    'DEFINE_FUNCTION',
    'SET_ENV_VARIABLE',  # =
    'INFIX_OPERATOR',  # =
    # 'INLINE_COMMENT'
    'LPAREN',  # )
    'RPAREN',  # (
    'SPECIAL',  # $
    'VARIABLE',  # $x
    'METHOD',  # some_method_V1
    'NUMBER',  # 0123456789
    'STRING',
)


def init():
    # t_RETURN = r'.*return.*'
    # t_RETURN = r'return'
    t_BREAK = r'\;'
    t_DEFINE_FUNCTION = r':'
    # t_SET_ENV_VARIABLE = r'='
    t_INFIX_OPERATOR = r'[=\+\-]'
    # t_INFIX_OPERATOR = r'='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    t_SPECIAL = r'\$'
    t_METHOD = r'[a-zA-Z_]\w+'
    t_VARIABLE = t_SPECIAL + t_METHOD
    t_STRING = r'[\w\d]+'

    t_ignore = ' \t'

    def t_NUMBER(t):
        r'\d+'
        # t.value = int(t.value)
        return t

    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    return lex.lex()


def tokenize(data: str):
    # lexer = lex.lex()
    lexer = init()
    lexer.input(data)

    while True:
        token = lexer.token()
        if not token:
            break

        print(token)
        print(token.type, token.value, token.lineno, token.lexpos)
        yield token


def parse(text):
    def p_expr_def_function(p):
        'expression : term LPAREN term RPAREN DEFINE_FUNCTION expression'
        p[0] = ('define-function', p[1], p[3], p[6])

    def p_expression_infix(p):
        'expression : expression INFIX_OPERATOR term'
        # if p[2] == '=':
        #     p[0] = p[1] + p[3]
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_factor_expr(p):
        'term : LPAREN expression RPAREN'
        p[0] = p[2]

    def p_expression_term(p):
        'expression : term'
        p[0] = p[1]

    def p_term_sequence(p):
        'term : term term'
        p[0] = p[1] + p[2]

    def p_term_factor(p):
        """term : NUMBER 
                | VARIABLE 
                | METHOD 
                | STRING
        """
        p[0] = p[1]

    # def p_term_text(p):
    #     'term : STRING'
    #     p[0] = p[1]

    def p_error(p):
        print(f'Syntax error: {p}')

    lexer = init()
    parser = yacc.yacc(debug=1)

    # data = '(x = 2)'
    print('in', data)
    result = parser.parse(data)
    print('out', result)


data = """
f (x): x + 1
"""

# tokenize(data)
parse(data)
