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
    |── list
    |   └── [ .., .. ]
    |── record_definition 
    |   └── { .. = .., \\n .. = .. }
    |── record_update
    |   └── { .. | .. , \\n .. }
    |── set 
    |   └── { .. || .. , \\n .. }
    |── assignment
    |   └── terms ASSIGN conjunction
    └── terms
         └── term

Notes

- multiline statements are not allowed in repl mode?
- The (indent) is optional.
- The term "inline" represents a partial line.

"""
from logging import getLogger
from ply import yacc

from mash.functional_shell.ast.lines import Lines
from mash.functional_shell.ast.node import Node
from mash.functional_shell.tokenizer import main, tokens
from mash.shell.errors import ShellSyntaxError


tokenizer = None


def parse(text, init=True):
    """Implement ply methods to parse text.
    """

    # precedence = (
    #     ('left', 'BREAK'),
    # )
    # _ply_constants = precedence, tokens
    _ply_constants = tokens

    def p_empty(p):
        """lines : NEWLINE
                 |
        """
        # p[0] = Lines()
        pass

    def p_lines_suffix(p):
        """lines : line
                 | line NEWLINE
        """
        # ignore trailing newline
        p[0] = Lines(p[1])

    def p_lines_infix(p):
        'lines : line NEWLINE lines'
        p[0] = Lines(p[1], *p[3])

    def p_lines_prefix(p):
        'lines : NEWLINE lines'
        # ignore leading newline
        p[0] = p[2]

    def p_all(p):
        """line : WORD
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
        raise ValueError("Input is not a string: ", text, type(text))

    return parser.parse(text)
