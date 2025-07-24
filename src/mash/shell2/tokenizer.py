import ply.lex as lex
from mash.shell.errors import ShellSyntaxError
from mash.shell.grammer.literals import keywords

tokens = (
    # 'PIPE',  # |
    # 'BASH',  # >> 1> 1>> 2> 2>>
    # 'MAP',  # >>=
    'NEWLINE',  # \n
    # 'BREAK',  # ;
    'COMMA',  # ;
    'SLASH',  # /
    # 'COLON',

    # 'DEFINE_FUNCTION',  # f ( ):
    # 'ASSIGN',  # =
    # 'EQUALS',  # ==
    # 'GREATER',  # >
    # 'COMPARE',  # > >= <=

    # 'RPAREN',  # (
    # 'LPAREN',  # )
    # 'CURLY_BRACE_R',  # {
    # 'CURLY_BRACE_L',  # }
    'RBRACE',  # [
    'LBRACE',  # ]
    # 'DOUBLE_QUOTED_STRING',  # "text"
    # 'SINGLE_QUOTED_STRING',  # 'text'

    # 'DOLLAR',  # $
    'VARIABLE',  # $x
    'FLOAT',  # 3.14
    # 'DOTTED_WORD',  # foo.bar
    'METHOD',  # some_method_V1
    'WORD',  # hel?os*

    # 'WILDCARD',
    # 'WILDCARD_RANGE',  # {1..3}
    'INT',  # 0123456789
    # 'MATH',  # + * -
    # 'LONG_SYMBOL',  # ++ => ->
    # 'SYMBOL',  # ~ -
    # 'DOTS',  # . ..
)
# tokens += tuple(keywords.values())


def main(debug=True, ignore=' \t'):
    """
    Token regexes are defined with the prefix `t_`.
    From ply docs:

    * functions are matched in order of specification
    * strings are sorted by regular expression length
    """

    # t_COLON = r':'
    t_COMMA = r','
    t_RBRACE = r'\]'
    t_LBRACE = r'\['

    # t_DOLLAR = r'\$'
    t_VARIABLE = r'\$[a-zA-Z_][a-zA-Z_0-9]*'

    t_ignore = ignore
    t_ignore_COMMENT = r'\#[^\n]*'

    # def t_LPAREN(t):
    #     r'\('
    #     return t

    # def t_RPAREN(t):
    #     r'\)'
    #     return t

    def t_NEWLINE(t):
        r'[\n\r]+'
        t.lexer.lineno += len(t.value)
        return t

    # def t_BREAK(t):
    #     r'(\;)+'
    #     return t

    def t_SLASH(t):
        r'/+'
        return t

    # def t_DOUBLE_QUOTED_STRING(t):
    #     r'"((\\\")|[^\""])*"'
    #     t.type = keywords.get(t.value, 'DOUBLE_QUOTED_STRING')

    #     # omit quotes
    #     t.value = t.value[1:-1]

    #     return t

    # def t_SINGLE_QUOTED_STRING(t):
    #     r"'(?:\.|(\\\')|[^\''])*'"
    #     t.type = keywords.get(t.value, 'SINGLE_QUOTED_STRING')

    #     # omit quotes
    #     t.value = t.value[1:-1]

    #     return t

    # def t_WILDCARD(t):
    #     r'[\w\d\-]*[\*\?\[][\w\d\-\*\?\!\[\]]*'
    #     return t

    # def t_WILDCARD_RANGE(t):
    #     r'[\w\d\-]*\{\d+\.\.\d+}[\w\d\-]*'
    #     # TODO verify matching []
    #     return t

    # def t_CURLY_BRACE_L(t):
    #     r'{'
    #     return t

    # def t_CURLY_BRACE_R(t):
    #     r'}'
    #     return t

    def t_FLOAT(t):
        r'-?(\d+\.\d*)|(\d*\.\d+)'
        # match *. or .* or *.*
        return t

    # def t_DOTTED_WORD(t):
    #     r'([\w\d]+\.[\.\w\d]*)|([\w\d\.]*\.[\w\d]+)'
    #     # match *. or .* or *.*
    #     return t

    def t_METHOD(t):
        r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
        return t

    # def t_LONG_SYMBOL(t):
    #     r'\+\+|::|=>|~>|\|->'
    #     return t

    # def t_PIPE(t):
    #     r'\|'
    #     return t

    # def t_BASH(t):
    #     r'1>|1>>|2>|2>>'
    #     return t

    # def t_EQUALS(t):
    #     '=='
    #     return t

    # def t_ASSIGN(t):
    #     r'='
    #     return t

    def t_INT(t):
        r'-?\d+'
        return t

    def t_WORD(t):
        r'\w[\w\d\-%&\~/]*'
        return t

    def t_error(t):
        t.lexer.skip(1)
        raise ShellSyntaxError(f'Illegal character: `{t.value[0]}`')

    if debug:
        return lex.lex()
    return lex.lex(optimize=1)


def inner(data: str, tokenizer: lex.Lexer):
    tokenizer.input(data)

    while True:
        token = tokenizer.token()
        if not token:
            break

        yield token


def tokenize(data: str):
    tokenizer = main()
    return inner(data, tokenizer)
