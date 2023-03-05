from collections import UserString
import ply.lex as lex
import ply.yacc as yacc
from mash.shell.parsing import indent_width
from mash.shell.errors import ShellError
# ShellError = RuntimeError
# def indent_width(x): return 1

lexer = None

tokens = (
    'BASH',  # | >>
    'SHELL',  # !
    'PIPE',  # |>

    'BREAK',  # \n ;
    'INDENT',
    'SPACE',
    'DEFINE_FUNCTION',  # f ( ):

    'ASSIGN',  # =
    'ASSIGN_RIGHT',  # ->
    'EQUALS',  # ==
    'INFIX_OPERATOR',  # == < >

    'RPAREN',  # (
    'LPAREN',  # )
    # 'RBRACE',  # [
    # 'LBRACE',  # ]
    'DOUBLE_QUOTED_STRING',  # "a 'b' c"
    'SINGLE_QUOTED_STRING',  # 'a\'bc'

    'METHOD',  # some_method_V1
    'SPECIAL',  # $
    'VARIABLE',  # $x
    'WORD',
    'WORD_WITH_DOT',
    'WILDCARD',
    'WILDCARD_RANGE',
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
    'math': 'MATH',
}
tokens += tuple(reserved.values())


class Term(UserString):
    def __init__(self, value, string_type='term'):
        self.data = value
        self.type = string_type


def init_lex():
    """
    Token regexes are defined with the prefix `t_`.
    From ply docs:
    - functions are matched in order of specification
    - strings are sorted by regular expression length
    """

    t_DEFINE_FUNCTION = r':'

    t_SPECIAL = r'\$'
    t_VARIABLE = r'\$[a-zA-Z_][a-zA-Z_0-9]*'

    t_ignore = ''
    t_ignore_COMMENT = r'\#[^\n]*'

    def t_LPAREN(t):
        r'\('
        return t

    def t_RPAREN(t):
        r'\)'
        return t

    # def t_LBRACE(t):
    #     r'\{'
    #     return t

    # def t_RBRACE(t):
    #     r'\}'
    #     return t

    def t_BREAK(t):
        r'[\n\r]|((\;)+[\ \t]*)'
        # semicolon_with_whitespace = r'((\;)+[ \t]*)'
        # newlines = r'(\n+)'

        # TOOD if not ;
        t.lexer.lineno += len(t.value)
        return t

    # def t_COMMENT(t):
    #     r'\#.*'

    def t_INDENT(t):
        r'\ {2,}|\t+'
        return t

    def t_DOUBLE_QUOTED_STRING(t):
        r'"((\\\")|[^\""])*"'
        t.type = reserved.get(t.value, 'DOUBLE_QUOTED_STRING')

        # omit quotes
        t.value = t.value[1:-1]

        return t

    def t_SINGLE_QUOTED_STRING(t):
        r"'(?:\.|(\\\')|[^\''])*'"
        t.type = reserved.get(t.value, 'SINGLE_QUOTED_STRING')

        # omit quotes
        t.value = t.value[1:-1]

        return t

    def t_SPACE(t):
        r'\ '
        # TODO use `t_ignore` to improve performance

    def t_WILDCARD(t):
        r'[\w\d\-]*[\*\?\[][\w\d\-\*\?\!\[\]]*'
        # TODO verify matching []
        return t

    def t_WILDCARD_RANGE(t):
        r'[\w\d\-]*\{\d\.\.\d}[\w\d\-]*'
        # TODO verify matching []
        return t

    def t_WORD_WITH_DOT(t):
        r'([\w\d]+\.[\.\w\d]*)|([\w\d]*\.[\.\w\d]+)'
        # match *. or .* or *.*
        return t

    def t_METHOD(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'METHOD')
        return t

    def t_PIPE(t):
        r'\|>' '|' r'>>='
        return t

    def t_BASH(t):
        r'\||>-|>>|1>|1>>|2>|2>>'
        return t

    def t_EQUALS(t):
        '=='
        return t

    def t_ASSIGN(t):
        r'<-|='
        return t

    def t_ASSIGN_RIGHT(t):
        r'->'
        return t

    def t_INFIX_OPERATOR(t):
        r'!=|<|>|<=|>='
        return t

    def t_WORD(t):
        r'[\w\d\+\-\*/%&\~]+'
        return t

    def t_NUMBER(t):
        r'\d+'
        return t

    def t_SHELL(t):
        r'\!'
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


def parse(text, init=True):
    # TODO use Node/Tree classes rather than tuples
    # e.g. classes with a .run() method (extends Runnable<>)

    precedence = (
        ('left', 'BREAK'),
        ('left', 'INDENT'),
        ('left', 'ASSIGN', 'ASSIGN'),
        ('left', 'PIPE', 'BASH'),
        ('left', 'MATH'),
        ('left', 'INFIX_OPERATOR'),
        ('left', 'EQUALS'),
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'NOT')
    )

    def p_newlines_empty(p):
        'lines : BREAK'
        # TODO handle `indent expr ; expr`
        p[0] = ('lines', [])

    def p_newlines_suffix(p):
        """lines : statement
                 | statement BREAK
        """
        p[0] = ('lines', [p[1]])

    def p_newlines_infix(p):
        'lines : statement BREAK lines'
        _, lines = p[3]
        p[0] = ('lines', [p[1]] + lines)

    def p_newlines_prefix(p):
        'lines : BREAK lines'
        p[0] = p[2]

    def p_statement(p):
        """statement : definition
                     | expression
        """
        p[0] = p[1]

    def p_statement_indent(p):
        'statement : INDENT expression'
        n = indent_width(p[1])
        p[0] = ('indent', n, p[2])

    def p_indent_empty(p):
        'expression : INDENT'
        n = indent_width(p[1])
        p[0] = ('indent', n, None)

    def p_def_inline_function(p):
        'definition : METHOD LPAREN basic_expression RPAREN DEFINE_FUNCTION expression'
        p[0] = ('define-inline-function', p[1], p[3], p[6])

    def p_def_inline_function_constant(p):
        'definition : METHOD LPAREN RPAREN DEFINE_FUNCTION expression'
        p[0] = ('define-inline-function', p[1], '', p[5])

    def p_def_function(p):
        'definition : METHOD LPAREN basic_expression RPAREN DEFINE_FUNCTION'
        p[0] = ('define-function', p[1], p[3])

    def p_def_function_constant(p):
        'definition : METHOD LPAREN RPAREN DEFINE_FUNCTION'
        p[0] = ('define-function', p[1], p[3])

    def p_scope(p):
        'scope : LPAREN expression RPAREN'
        q = p[2]
        p[0] = ('scope', q)

    def p_math(p):
        'expression : MATH expression'
        p[0] = ('math', p[2])

    def p_return(p):
        'expression : RETURN expression'
        # 'definition : RETURN expression'
        p[0] = ('return', p[2])

    def p_if(p):
        'expression : IF expression'
        p[0] = ('if', p[2])

    def p_if_then_else_inline(p):
        'expression : IF expression THEN expression ELSE expression'
        _, _if, cond, _then, true, _else, false = p
        p[0] = ('if-then-else', cond, true, false)

    def p_if_then_else(p):
        'expression : IF expression THEN expression ELSE'
        _, _if, cond, _then, true, _else = p
        p[0] = ('if-then-else', cond, true, None)

    def p_if_then(p):
        'expression : IF expression THEN'
        p[0] = ('if-then', p[2], None)

    def p_if_then_inline(p):
        'expression : IF expression THEN expression'
        _, _if, cond, _then, true = p
        p[0] = ('if-then', cond, true)

    def p_then(p):
        """expression : THEN expression
                      | THEN
        """
        if len(p) == 2:
            p[0] = ('then', None)
        else:
            p[0] = ('then', p[2])

    def p_else_if_then(p):
        """expression : ELSE IF expression THEN expression
                      | ELSE IF expression THEN
        """
        if len(p) == 5:
            p[0] = ('else-if-then', p[3], p[4])
        else:
            p[0] = ('else-if-then', p[3], None)

    def p_else_if(p):
        'expression : ELSE IF expression'
        p[0] = ('else-if', p[3])

    def p_else(p):
        """expression : ELSE expression
                      | ELSE
        """
        if len(p) == 2:
            p[0] = ('else', None)
        else:
            p[0] = ('else', p[2])

    def p_logical_bin(p):
        """expression : expression AND expression
                      | expression OR expression
        """
        # TODO use flat tree any/all (or, a, b, c) = any : e OR any  | e OR e
        p[0] = ('logic', p[2], p[1], p[3])

    def p_logical_not(p):
        'expression : NOT basic_expression'
        p[0] = ('not', p[2])

    def p_shell(p):
        'expression : SHELL basic_expression'
        p[0] = ('!', p[2])

    def p_pipe_py(p):
        'expression : expression PIPE expression'
        p[0] = ('pipe', p[2], p[1], p[3])

    def p_pipe_bash(p):
        'expression : expression BASH expression'
        p[0] = ('bash', p[2], p[1], p[3])

    def p_assign(p):
        'expression : basic_expression ASSIGN expression'
        p[0] = ('assign', p[2], p[1], p[3])

    def p_assign_right(p):
        'expression : expression ASSIGN_RIGHT basic_expression'
        p[0] = ('assign', p[2], p[1], p[3])

    def p_expression_infix(p):
        'expression : basic_expression INFIX_OPERATOR expression'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_expression_infix_equals(p):
        'expression : expression EQUALS expression'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_expression_basic(p):
        'expression : basic_expression'
        p[0] = p[1]

    def p_basic_expression(p):
        """basic_expression : term
                            | list
        """
        p[0] = p[1]

    def p_list(p):
        """list : term term
                | term list
        """
        # TODO rename list => terms
        if isinstance(p[1], list):
            0
        if isinstance(p[2], str) or isinstance(p[2], Term):
            # if len(p) == 3:
            p[0] = ('list', [p[1], p[2]])
        else:
            a = p[1]
            key, values = p[2]
            if key == 'scope':
                values = [p[2]]

            p[0] = ('list', [a] + values)

    def p_term(p):
        """term : SPECIAL 
                | WORD
                | WORD_WITH_DOT
        """
        p[0] = Term(p[1])

    def p_term_value(p):
        """term : value
                | method
                | scope
        """
        p[0] = p[1]

    def p_value_wildcard(p):
        'value : WILDCARD'
        p[0] = Term(p[1], 'wildcard')

    def p_value_wildcard_range(p):
        'value : WILDCARD_RANGE'
        p[0] = Term(p[1], 'range')

    def p_value_number(p):
        'value : NUMBER'
        p[0] = Term(p[1], 'number')

    def p_value_method(p):
        'method : METHOD'
        p[0] = Term(p[1], 'method')

    def p_value_variable(p):
        'value : VARIABLE'
        p[0] = Term(p[1], 'variable')

    def p_value_literal_string(p):
        'value : SINGLE_QUOTED_STRING'
        p[0] = Term(p[1], 'literal string')

    def p_value_string(p):
        'value : DOUBLE_QUOTED_STRING'
        p[0] = Term(p[1], 'quoted string')

    def p_error(p):
        print(f'Syntax error: {p}')
        raise ShellError(f'Syntax error: {p}')

    if init:
        global lexer
        lexer = init_lex()
    else:
        lexer.clone()

    parser = yacc.yacc(debug=True)

    # add a newline to allow empty strings to be matched
    return parser.parse('\n' + text)


if __name__ == '__main__':
    data = """

    echo x
    if 1 = 3 then 2 else 3
    """

    result = parse(data)
    print('out', result)
