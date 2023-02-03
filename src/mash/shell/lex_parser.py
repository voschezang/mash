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
    'PIPE',  # |>

    'BREAK',  # \n ;
    'INDENT',
    'SPACE',
    'DEFINE_FUNCTION',  # f ( ):

    'ASSIGN',  # =
    'EQUALS',  # ==
    'INFIX_OPERATOR',  # == < >

    'RPAREN',  # (
    'LPAREN',  # )
    'RBRACE',
    'LBRACE',
    'DOUBLE_QUOTED_STRING',  # "a 'b' c"
    'SINGLE_QUOTED_STRING',  # 'a\'bc'

    'METHOD',  # some_method_V1
    'SPECIAL',  # $
    'VARIABLE',  # $x
    'WORD',
    'WORD_WITH_DOT',
    'NUMBER',  # 0123456789
    'SCOPE'
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
    # t_WILDCARD = r'[\w\d\*\?]+'

    t_ignore = ''
    t_ignore_COMMENT = r'\#.*'
    t_scope_ignore = ' \t\n'

    states = (('scope', 'exclusive'),)

    def t_LBRACE(t):
        r'\('
        return t

    def t_RBRACE(t):
        r'\)'
        return t

    def t_scope(t):
        r'\{'
        # TODO deprecate state "scope"
        t.lexer.scope_start = t.lexer.lexpos
        t.lexer.begin('scope')
        t.lexer.level = 1

    def t_scope_LPAREN(t):
        r'\{'
        t.lexer.level += 1

    def t_scope_RPAREN(t):
        r'\}'
        t.lexer.level -= 1

        if t.lexer.level == 0:
            t.value = t.lexer.lexdata[t.lexer.scope_start:t.lexer.lexpos-1]
            t.type = 'SCOPE'
            t.lexer.lineno += t.value.count('\n') + t.value.count(';')
            t.lexer.begin('INITIAL')
            return t

    def t_scope_quotes(t):
        r'("((\\\")|[^\""])*")' '|' r"('(?:\.|(\\\')|[^\''])*')"

    def t_scope_all(t):
        r'[^\s]'

    def t_BREAK(t):
        r'[\n\r]|((\;)+[\ \t]*)'
        # semicolon_with_whitespace = r'((\;)+[ \t]*)'
        # newlines = r'(\n+)'

        # TOOD if not ;
        t.lexer.lineno += len(t.value)
        return t

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

    def t_WORD_WITH_DOT(t):
        r'([\w\d]+\.[\.\w\d]*)|([\w\d]*\.[\.\w\d]+)'
        # match *. or .* or *.*
        return t

    def t_METHOD(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'METHOD')
        return t

    def t_NUMBER(t):
        r'\d+'
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
        r'<-|=|->'
        return t

    def t_INFIX_OPERATOR(t):
        r'==|!=|<|>|<=|>='
        return t

    def t_WORD(t):
        r'[\w\d\+\-\*/%&\~]+'
        return t

    def t_error(t):
        print(f'Illegal character: `{t.value[0]}`')
        t.lexer.skip(1)
        raise ShellError(f'Illegal character: `{t.value[0]}`')

    def t_scope_error(t):
        print(f'Illegal character: `{t.value[0]}`')
        t.lexer.skip(1)
        raise ShellError(f'Illegal character in scope: `{t.value[0]}`')

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

    def p_newlines_empty(p):
        'lines : BREAK'
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
        'definition : METHOD LBRACE basic_expression RBRACE DEFINE_FUNCTION expression'
        # 'definition : scope DEFINE_FUNCTION expression'
        # 'definition : METHOD scope DEFINE_FUNCTION expression'
        # 'expression : METHOD SCOPE DEFINE_FUNCTION'
        # 'expression : METHOD LPAREN list RPAREN DEFINE_FUNCTION expression'
        # scope = parse(p[2], False)
        # p[0] = ('define-inline-function', p[1], p[2], p[4])
        p[0] = ('define-inline-function', p[1], p[3], p[6])

    def p_def_function(p):
        'definition : METHOD LBRACE basic_expression RBRACE DEFINE_FUNCTION'
        # 'definition : scope DEFINE_FUNCTION'
        p[0] = ('define-function', p[1], p[3])

    def p_scope(p):
        'scope : LBRACE expression RBRACE'
        # 'scope : SCOPE'
        # q = parse(p[1], False)
        q = p[2]
        p[0] = ('scope', q)

    def p_math(p):
        'expression : MATH expression'
        p[0] = ('math', p[2])

    # def p_parentheses(p):
    #     'expression : LPAREN expression RPAREN'
    #     p[0] = p[2]

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
        """expression : basic_expression AND expression
                      | basic_expression XOR expression
                      | basic_expression OR expression
        """
        # TODO use flat tree any/all (or, a, b, c) = any : e OR any  | e OR e
        p[0] = ('logic', p[2], p[1], p[3])

    def p_logical_not(p):
        'expression : NOT expression'
        p[0] = ('not', p[2])

    def p_pipe_py(p):
        'expression : basic_expression PIPE expression'
        p[0] = ('pipe', p[2], p[1], p[3])

    def p_pipe_bash(p):
        'expression : basic_expression BASH expression'
        p[0] = ('bash', p[2], p[1], p[3])

    def p_assign(p):
        'expression : basic_expression ASSIGN expression'
        p[0] = ('assign', p[2], p[1], p[3])

    def p_expression_infix(p):
        'expression : basic_expression INFIX_OPERATOR expression'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_expression_infix_equals(p):
        'expression : basic_expression EQUALS expression'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_expression_basic(p):
        """expression : basic_expression
        """
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

    def p_value_number(p):
        'value : NUMBER'
        p[0] = Term(p[1], 'number')

    def p_value_method(p):
        'method : METHOD'
        p[0] = Term(p[1], 'method')

    def p_value_variable(p):
        'value : VARIABLE'
        p[0] = Term(p[1], 'variable')

    def p_value_string(p):
        """value : SINGLE_QUOTED_STRING
                 | DOUBLE_QUOTED_STRING
        """
        p[0] = Term(p[1], 'quoted string')

    def p_error(p):
        print(f'Syntax error: {p}')

    if init:
        global lexer
        lexer = init_lex()
    else:
        lexer.clone()

    parser = yacc.yacc(debug=True)

    return parser.parse(text)


if __name__ == '__main__':
    data = """

    echo x
    if 1 = 3 then 2 else 3
    """

    result = parse(data)
    print('out', result)
