import ply.lex as lex
from mash.shell.errors import ShellSyntaxError
from mash.shell.grammer.literals import keywords

tokens = (
    'BASH',  # | >>
    'SHELL',  # !
    'PIPE',  # |>
    'MAP',  # >>=

    'BREAK',  # \n ;
    'INDENT',
    'DEFINE_FUNCTION',  # f ( ):

    'ASSIGN',  # =
    'ASSIGN_RIGHT',  # ->
    'EQUALS',  # ==
    'INFIX_OPERATOR',  # >= <= < >

    'RPAREN',  # (
    'LPAREN',  # )
    'CURLY_BRACE_R',  # {
    'CURLY_BRACE_L',  # }
    # 'RBRACE',  # [
    # 'LBRACE',  # ]
    'DOUBLE_QUOTED_STRING',  # "a 'b' c"
    'SINGLE_QUOTED_STRING',  # 'a\'bc'

    'NESTED_VARIABLE',
    'POSITIONAL_VARIABLE',
    'SPECIAL',  # $
    'VARIABLE',  # $x
    'STANDALONE_DOTTED_WORD',
    'DOTTED_WORD', # .foo
    # 'DOTTED_NUMBER', # .foo
    'METHOD',  # some_method_V1
    'WORD',
    'NUMBER_WITH_DOT', # 3.14

    'WILDCARD',
    'WILDCARD_RANGE',
    'NUMBER',  # 0123456789
    'LONG_SYMBOL',
    'SYMBOL',
)
tokens += tuple(keywords.values())


def main():
    """
    Token regexes are defined with the prefix `t_`.
    From ply docs:

    * functions are matched in order of specification
    * strings are sorted by regular expression length
    """

    t_DEFINE_FUNCTION = r':'

    t_SPECIAL = r'\$'
    t_NESTED_VARIABLE = r'\$(\.[a-zA-Z_0-9]+)+'
    t_POSITIONAL_VARIABLE = r'\$[\d+](\.[a-zA-Z_0-9]+)*'
    t_VARIABLE = r'\$[a-zA-Z_][a-zA-Z_0-9]*'

    t_ignore = ''
    t_ignore_COMMENT = r'\#[^\n]*'

    def t_LPAREN(t):
        r'\('
        return t

    def t_RPAREN(t):
        r'\)'
        return t

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
        t.type = keywords.get(t.value, 'DOUBLE_QUOTED_STRING')

        # omit quotes
        t.value = t.value[1:-1]

        return t

    def t_SINGLE_QUOTED_STRING(t):
        r"'(?:\.|(\\\')|[^\''])*'"
        t.type = keywords.get(t.value, 'SINGLE_QUOTED_STRING')

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

    def t_CURLY_BRACE_L(t):
        r'{'
        return t

    def t_CURLY_BRACE_R(t):
        r'}'
        return t

    def t_STANDALONE_DOTTED_WORD(t):
        r'\b\.\w+'
        # match .foo
        return t

    def t_DOTTED_WORD(t):
        r'\.\w+'
        # match .foo
        return t

    # def t_DOTTED_NUMBER(t):
    #     r'\.[\w\d]+'
    #     # match .1
    #     return t

    def t_METHOD(t):
        r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
        t.type = keywords.get(t.value, 'METHOD')
        return t

    def t_NUMBER_WITH_DOT(t):
        r'-?(\d+\.\d*)|(\d*\.\d+)'
        # match *. or .* or *.*
        return t

    def t_LONG_SYMBOL(t):
        r'\+\+|::|=>|~>|\|->'
        return t

    def t_MAP(t):
        r'>>=|\|>\smap'
        """Syntax for "map":

        .. code-block:: bash

            f x >>= g

        or

        .. code-block:: bsh

            `f x |> map g`

        """
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
        r'[\w\d\-%&\~/]+'
        return t

    def t_NUMBER(t):
        r'-?\d+'
        return t

    def t_SHELL(t):
        r'\!'
        return t

    def t_SYMBOL(t):
        r'[\~\+\*\-%&.]+'
        return t

    def t_error(t):
        t.lexer.skip(1)
        raise ShellSyntaxError(f'Illegal character: `{t.value[0]}`')

    return lex.lex()


def tokenize(data: str):
    tokenizer = main()
    tokenizer.input(data)

    while True:
        token = tokenizer.token()
        if not token:
            break

        yield token
