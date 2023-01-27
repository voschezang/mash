import ply.lex as lex
import ply.yacc as yacc
from mash.shell.parsing import indent_width
from mash.shell.errors import ShellError
# ShellError = RuntimeError
# def indent_width(x): return 1


tokens = (
    'BASH',  # | >>
    'PIPE',  # |>

    'BREAK',  # \n ;
    'INDENT',
    'SPACE',
    'DEFINE_FUNCTION',  # f ( ):

    'ASSIGN',  # =
    'INFIX_OPERATOR',  # == + - * /

    'RPAREN',  # (
    'LPAREN',  # )
    'DOUBLE_QUOTED_STRING',  # "a 'b' c"
    'SINGLE_QUOTED_STRING',  # 'a\'bc'

    'METHOD',  # some_method_V1
    'SPECIAL',  # $
    'VARIABLE',  # $x
    'WORD',
    'NUMBER',  # 0123456789
)
reserved = {
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'return': 'RETURN',
    'not': 'NOT',
    'and': 'AND',
    'or': 'OR',
    'xor': 'XOR',
}
tokens += tuple(reserved.values())


def init_lex():
    """
    Token regexes are defined with the prefix `t_`.
    From ply docs:
    - functions are matched in order of specification
    - strings are sorted by regular expression length
    """

    t_DEFINE_FUNCTION = r':'
    t_BASH = r'\||>-|>>|1>|1>>|2>|2>>'
    t_PIPE = r'\|>' '|' r'>>='
    t_ASSIGN = r'<-|=|->'

    t_INFIX_OPERATOR = r'==|[\+\-*//]'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    t_SPECIAL = r'\$'
    t_VARIABLE = r'\$[a-zA-Z_][a-zA-Z_0-9]*'
    # t_WILDCARD = r'[\w\d\*\?]+'
    t_WORD = r'[\w\d]+'

    t_ignore = ''
    t_ignore_COMMENT = r'\#.*'

    def t_BREAK(t):
        r'[\n\r]|((\;)+[\ \t]*)'
        # semicolon_with_whitespace = r'((\;)+[ \t]*)'
        # newlines = r'(\n+)'

        # TOOD if not ;
        t.lexer.lineno += len(t.value)
        return t

    def t_INDENT(t):
        r'\ {2,}|\t+'
        # r'\s{2,}|\t'
        # r'(\ {4})+|\t+'
        # r'\n(\ {4})+|\t+'
        # r'\n(\ {4})+|\t+'
        # r'(\ {4})+|\t+'
        # r'[((\ ){4})\t]+'
        # r'(^\s)|(\n\s)'
        return t

    def t_DOUBLE_QUOTED_STRING(t):
        r'"((\\\")|[^\""])*"'
        # r'"((\\\")|[^\""])*"'
        # r'"([^\""])*"'
        # r'"(\.|(\\\")|[^\""])*"'
        # r'"(\.|(\\\")|[^\""]|\n)*"'
        t.type = reserved.get(t.value, 'DOUBLE_QUOTED_STRING')
        return t

    def t_SINGLE_QUOTED_STRING(t):
        r"'(?:\.|(\\\')|[^\''])*'"
        t.type = reserved.get(t.value, 'SINGLE_QUOTED_STRING')
        return t

    def t_SPACE(t):
        r'\ '
        # TODO use `t_ignore` to improve performance

    def t_METHOD(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'METHOD')
        return t

    def t_NUMBER(t):
        r'\d+'
        return t

    def t_error(t):
        print(f'Illegal character: `{t.value[0]}`')
        t.lexer.skip(1)
        raise ShellError(f'Illegal character: `{t.value[0]}`')

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
    # TODO use Node/Tree classes rather than tuples

    def p_newlines_empty(p):
        """lines : BREAK
        """
        p[0] = ('lines', [])

    def p_newlines_suffix(p):
        """lines : expression
                 | expression BREAK
        """
        p[0] = ('lines', [p[1]])

    def p_newlines_infix(p):
        """lines : expression BREAK lines
        """
        _, lines = p[3]
        p[0] = ('lines', [p[1]] + lines)

    def p_newlines_prefix(p):
        """lines : BREAK lines
        """
        p[0] = p[2]

    def p_indent(p):
        'expression : INDENT expression'
        n = indent_width(p[1])
        p[0] = ('indent', n, p[2])

    def p_indent_empty(p):
        'expression : INDENT'
        n = indent_width(p[1])
        p[0] = ('indent', n, None)

    def p_def_inline_function(p):
        'expression : METHOD LPAREN expression RPAREN DEFINE_FUNCTION expression'
        p[0] = ('define-inline-function', p[1], p[3], p[6])

    def p_def_function(p):
        'expression : METHOD LPAREN expression RPAREN DEFINE_FUNCTION'
        p[0] = ('define-function', p[1], p[3])

    def p_parentheses(p):
        'term : LPAREN expression RPAREN'
        p[0] = p[2]

    def p_return(p):
        'expression : RETURN expression'
        p[0] = ('return', p[2])

    def p_if_then(p):
        """expression : IF expression THEN expression ELSE expression
                      | IF expression THEN expression ELSE
                      | IF expression THEN expression
                      | IF expression THEN
                      | IF expression
        """
        if len(p) == 3 or len(p) == 4:
            p[0] = ('if', p[2])
            return

        _, _if, cond, *then_else = p

        if len(then_else) == 4:
            _then, true, _else, false = then_else
            p[0] = ('if-then-else', cond, true, false)
            return

        if len(then_else) == 2:
            _then, true = then_else
        elif len(then_else) == 3:
            _then, true, _else = then_else

        p[0] = ('if-then', cond, true)

    def p_logical_bin(p):
        """expression : expression AND expression
                      | expression XOR expression
                      | expression OR expression
        """
        p[0] = ('logic', p[2], p[1], p[3])

    def p_logical_not(p):
        'expression : NOT expression'
        p[0] = ('not', p[2])

    def p_pipe_py(p):
        'expression : term PIPE expression'
        p[0] = ('pipe', p[0], p[2])

    def p_pipe_bash(p):
        'expression : term BASH expression'
        p[0] = ('bash', p[0], p[2])

    def p_assign(p):
        'expression : expression ASSIGN expression'
        p[0] = ('assign', p[2], p[1], p[3])

    def p_expression_infix(p):
        'expression : expression INFIX_OPERATOR expression'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_list(p):
        """list : term term
                | term list
        """
        if isinstance(p[1], list):
            0
        if isinstance(p[2], str):
            # if len(p) == 3:
            p[0] = ('list', [p[1], p[2]])
        else:
            a = p[1]
            _list, values = p[2]
            p[0] = ('list', [a] + values)

    def p_expression_term(p):
        """expression : term
                      | list
        """
        p[0] = p[1]

    def p_term(p):
        """term : NUMBER 
                | VARIABLE 
                | SPECIAL 
                | METHOD 
                | WORD
                | SINGLE_QUOTED_STRING
                | DOUBLE_QUOTED_STRING
        """
        p[0] = p[1]

    def p_error(p):
        print(f'Syntax error: {p}')

    init_lex()
    parser = yacc.yacc(debug=True)

    return parser.parse(text)


if __name__ == '__main__':
    data = """

    echo x
    if 1 = 3 then 2 else 3
    """

    result = parse(data)
    print('out', result)
