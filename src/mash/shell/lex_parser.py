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
    'MAP',  # >>=

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
    'NUMBER_WITH_DOT',

    'WILDCARD',
    'WILDCARD_RANGE',
    'NUMBER',  # 0123456789
    'SYMBOL',
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

    def t_METHOD(t):
        r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
        t.type = reserved.get(t.value, 'METHOD')
        return t

    def t_WORD_WITH_DOT(t):
        r'\b([\w\d]+\.[\.\w\d]*)|([\w\d]*\.[\.\w\d]+)\b'
        # match *. or .* or *.*
        return t

    def t_NUMBER_WITH_DOT(t):
        r'-?(\d+\.\d*)|(\d*\.\d+)'
        # match *. or .* or *.*
        return t

    def t_MAP(t):
        r'>>='
        return t

    def t_PIPE(t):
        r'\|>'
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
        r'!=|<=|>=|<|>'
        return t

    def t_WORD(t):
        r'[\w\d\-%&\~]+'
        return t

    def t_NUMBER(t):
        r'-?\d+'
        return t

    def t_SHELL(t):
        r'\!'
        return t

    def t_SYMBOL(t):
        r'\~|\+|\*|-|%|&'
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
        ('left', 'ASSIGN'),
        ('left', 'PIPE', 'BASH'),
        ('left', 'MATH'),
        ('left', 'INFIX_OPERATOR'),
        ('left', 'EQUALS'),
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'NOT')
    )

    def p_lines_empty(p):
        """lines : BREAK
                 | INDENT BREAK
        """
        'lines : BREAK'
        # TODO handle `indent expr ; expr`
        p[0] = ('lines', [])

    def p_lines_suffix(p):
        """lines : line
                 | line BREAK
        """
        p[0] = ('lines', [p[1]])

    def p_lines_infix(p):
        'lines : line BREAK lines'
        _, lines = p[3]
        p[0] = ('lines', [p[1]] + lines)

    def p_lines_prefix(p):
        'lines : BREAK lines'
        p[0] = p[2]

    def p_line_indented(p):
        'line : INDENT statement'
        n = indent_width(p[1])
        p[0] = ('indent', n, p[2])

    def p_line(p):
        'line : statement'
        p[0] = p[1]

    def p_line_indent_empty(p):
        'line : INDENT'
        n = indent_width(p[1])
        p[0] = ('indent', n, None)

    def p_statement(p):
        """statement : assignment
                     | conditional
                     | definition
                     | inner_statement
                     | return_statement
        """
        p[0] = p[1]

    def p_statement_return(p):
        'return_statement : RETURN inner_statement'
        p[0] = ('return', p[2])

    def p_inner_statement(p):
        """inner_statement : conjunction
                           | full_conditional
        """
        p[0] = p[1]

    def p_final_statement(p):
        """final_statement : conjunction
                           | return_statement
        """
        p[0] = p[1]

    def p_assign(p):
        'assignment : terms ASSIGN inner_statement'
        p[0] = ('assign', p[2], p[1], p[3])

    def p_assign_right(p):
        'assignment : inner_statement ASSIGN_RIGHT terms'
        p[0] = ('assign', p[2], p[1], p[3])

    def p_def_inline_function(p):
        'definition : METHOD LPAREN terms RPAREN DEFINE_FUNCTION inner_statement'
        p[0] = ('define-inline-function', p[1], p[3], p[6])

    def p_def_inline_function_constant(p):
        'definition : METHOD LPAREN RPAREN DEFINE_FUNCTION inner_statement'
        p[0] = ('define-inline-function', p[1], '', p[5])

    def p_def_function(p):
        'definition : METHOD LPAREN terms RPAREN DEFINE_FUNCTION'
        p[0] = ('define-function', p[1], p[3])

    def p_def_function_constant(p):
        'definition : METHOD LPAREN RPAREN DEFINE_FUNCTION'
        p[0] = ('define-function', p[1], p[3])

    def p_scope(p):
        'scope : LPAREN inner_statement RPAREN'
        q = p[2]
        p[0] = ('scope', q)

    def p_if(p):
        'conditional : IF conjunction'
        p[0] = ('if', p[2])

    def p_full_conditional(p):
        'full_conditional : IF conjunction THEN conjunction ELSE conjunction'
        _, _if, cond, _then, true, _else, false = p
        p[0] = ('if-then-else', cond, true, false)

    def p_if_then_inline(p):
        'full_conditional : IF conjunction THEN conjunction'
        _, _if, cond, _then, true = p
        p[0] = ('if-then', cond, true)

    def p_if_then_else(p):
        'conditional : IF conjunction THEN conjunction ELSE'
        _, _if, cond, _then, true, _else = p
        p[0] = ('if-then-else', cond, true, None)

    def p_if_then(p):
        'conditional : IF conjunction THEN'
        p[0] = ('if-then', p[2], None)

    def p_if_then_inline_final(p):
        'conditional : IF conjunction THEN return_statement'
        _, _if, cond, _then, true = p
        p[0] = ('if-then', cond, true)

    def p_then(p):
        """conditional : THEN final_statement
                       | THEN
        """
        if len(p) == 2:
            p[0] = ('then', None)
        else:
            p[0] = ('then', p[2])

    def p_else_if_then(p):
        """conditional : ELSE IF conjunction THEN final_statement
                      | ELSE IF conjunction THEN
        """
        if len(p) == 6:
            p[0] = ('else-if-then', p[3], p[5])
        else:
            p[0] = ('else-if-then', p[3], None)

    def p_else_if(p):
        'conditional : ELSE IF conjunction'
        p[0] = ('else-if', p[3])

    def p_else(p):
        """conditional : ELSE final_statement
                       | ELSE
        """
        if len(p) == 2:
            p[0] = ('else', None)
        else:
            p[0] = ('else', p[2])

    def p_conditional(p):
        """conditional : conjunction
                       | full_conditional
        """
        p[0] = p[1]

    def p_pipe_py(p):
        'conjunction : expression PIPE conjunction'
        p[0] = ('pipe', p[1], p[3])

    def p_conjunction(p):
        'conjunction : expression'
        p[0] = p[1]

    def p_pipe_bash(p):
        'expression : expression BASH expression'
        p[0] = ('bash', p[2], p[1], p[3])

    def p_pipe_map(p):
        'expression : expression MAP expression'
        p[0] = ('map', p[1], p[3])

    def p_expression_full_conditional(p):
        'expression : full_conditional'
        p[0] = p[1]

    def p_expression(p):
        'expression : basic_expression'
        p[0] = p[1]

    def p_shell(p):
        'expression : SHELL expression'
        p[0] = ('!', p[2])

    def p_math(p):
        'expression : MATH expression'
        p[0] = ('math', p[2])

    def p_basic_expression(p):
        """basic_expression : join
                            | logic_expression
                            | terms
        """
        p[0] = p[1]

    def p_logic_binary(p):
        """join : logic_expression AND join
                | logic_expression AND logic_expression
                | logic_expression OR join
                | logic_expression OR logic_expression
        """
        # TODO use flat tree any/all (or, a, b, c) = any : e OR any  | e OR e
        p[0] = ('logic', p[2], p[1], p[3])

    def p_logic_expression_infix(p):
        'logic_expression : terms INFIX_OPERATOR logic_expression'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_logic_expression_infix_equals(p):
        'logic_expression : logic_expression EQUALS logic_expression'
        p[0] = ('binary-expression', p[2], p[1], p[3])

    def p_logic_negation(p):
        'logic_expression : NOT terms'
        p[0] = ('not', p[2])

    def p_logic(p):
        'logic_expression : terms'
        p[0] = p[1]

    def p_terms_pair(p):
        'terms : term term'
        p[0] = ('terms', [p[1], p[2]])

    def p_terms_head_tail(p):
        'terms : term terms'
        key, tail = p[2]
        p[0] = ('terms', [p[1]] + tail)

    def p_terms_singleton(p):
        'terms : term'
        p[0] = p[1]

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

    def p_value_number_int(p):
        'value : NUMBER'
        p[0] = Term(p[1], 'number')

    def p_value_number_float(p):
        'value : NUMBER_WITH_DOT'
        p[0] = Term(p[1], 'number')

    def p_value_method(p):
        'method : METHOD'
        p[0] = Term(p[1], 'method')

    def p_value_variable(p):
        'value : VARIABLE'
        p[0] = Term(p[1], 'variable')

    def p_value_symbol(p):
        'value : SYMBOL'
        p[0] = Term(p[1], 'symbol')

    def p_value_literal_string(p):
        'value : SINGLE_QUOTED_STRING'
        p[0] = Term(p[1], 'literal string')

    def p_value_string(p):
        'value : DOUBLE_QUOTED_STRING'
        p[0] = Term(p[1], 'quoted string')

    def p_illegal_if_then(p):
        """conditional : IF THEN
                       | IF INDENT THEN
                       | IF ELSE
                       | IF INDENT ELSE
                       | ELSE THEN
                       | ELSE INDENT THEN
        """
        raise ShellError(f'Syntax error: invalid if-then-else statement: {p}')

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


def Terms(args):
    return ('terms', args)


if __name__ == '__main__':
    data = """

    echo x
    if 1 = 3 then 2 else 3
    """

    result = parse(data)
    print('out', result)
