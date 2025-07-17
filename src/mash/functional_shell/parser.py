"""
AST
**********************

Tree structure.

blocks
└── block blocks
    └── OPEN lines CLOSE

lines 
|── multiline
|   |── function
|   |   └── block
|   |       └── OPEN lines CLOSE
|   |── if-then-else
|   |   └── IF inline : block ELSE block
|   └── for-loop
|       └── FOR terms IN term : block
|    
|── line ; line \\n line
└── line \\n line \\n line
    └── inlines
        └── inline ; inline ; inline
            |── list
            |   └── [ .., .. ]
            |── record_definition 
            |   └── { .. = .., \\n .. = .. }
            |── record_update
            |   └── { .. | .. , \\n .. }
            |── set 
            |   └── { .. || .. , \\n .. }
            └── terms
                 └── term

Notes

- multiline statements are not allowed in repl mode?
- The (indent) is optional.
- The term "inline" represents a partial line.

"""
from logging import getLogger
from ply import yacc

from mash.functional_shell.ast.lines import Line, Lines
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

    # def p_blocks(p):
    #     'blocks : block blocks'
    #     'block : OPEN lines CLOSE'

    def p_empty(p):
        """lines : NEWLINE
        """
        p[0] = Lines([])

    def p_lines_suffix(p):
        """lines : line
                 | line NEWLINE
        """
        # ignore trailing newline
        p[0] = Lines([Line([p[1]])])

    def p_lines_infix(p):
        'lines : line NEWLINE lines'
        p[0] = Lines([p[1]] + p[3])

    def p_lines_prefix(p):
        'lines : NEWLINE lines'
        # ignore leading newline
        p[0] = p[2]

    def p_line_inlines(p):
        """line : inlines
        """
        # handle indentation
        p[0] = Line(p[1])

    def p_inline_empty(p):
        """inlines : BREAK
        """
        p[0] = []

    def p_line_suffix(p):
        """inlines : inline
                   | inline BREAK
        """
        p[0] = [Line(p[1])]

    def p_line_infix(p):
        """inlines : inline BREAK inlines
        """
        p[0]

    def p_inlines_prefix(p):
        'inline : BREAK inlines'
        p[0] = p[2]

    # def p_inline_terms(p):
    #     """inline : terms
    #     """
    #     p[0]

    def p_all(p):
        """inline : WORD
                  | INT
        """
        p[0] = Node(p[1])

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
    # return parser.parse('\n' + text)
    return parser.parse(text)
