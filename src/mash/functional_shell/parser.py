from logging import getLogger
from ply import yacc

from mash.functional_shell.tokenizer import main, tokens
from mash.functional_shell.ast.term import Node
from mash.shell.errors import ShellSyntaxError


tokenizer = None


def parse(text, init=True):
    """Implement ply methods to parse text.
    """

    # precedence = (
    #     ('left', 'BREAK'),
    #     ('left', 'INDENT'),
    #     ('left', 'ASSIGN'),
    #     ('left', 'PIPE', 'BASH'),
    #     ('left', 'MATH'),
    #     ('left', 'INFIX_OPERATOR'),
    #     ('left', 'IN'),
    #     ('left', 'EQUALS'),
    #     ('left', 'OR'),
    #     ('left', 'AND'),
    #     ('left', 'NOT')
    # )
    # _ply_constants = precedence, tokens
    _ply_constants = tokens

    def p_all(p):
        """lines : BREAK WORD
                 | BREAK WORD WORD
                 | BREAK INT
        """
        # pos = p.slice[2].lexpos
        # indent = pos / 2
        p[0] = Node(p[2])

    def p_error(p):
        print(f'Syntax error: {p}')
        raise ShellSyntaxError(f'Syntax error: {p}')

    if init:
        global tokenizer
        tokenizer = main()
    else:
        tokenizer.clone()

    log = getLogger()
    parser = yacc.yacc(debug=log)
    if not isinstance(text, str):
        raise ValueError(text)

    # insert a newline to allow empty strings to be matched
    return parser.parse('\n' + text)
