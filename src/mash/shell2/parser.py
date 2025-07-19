"""
AST
**********************

Tree structure.

.. code-block:: sh

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
        └── command terms
                    └── terms
                        └── term terms
                            |── word
                            |── float
                            └── int

Notes

- multiline statements are not allowed in repl mode?
- The (indent) is optional.
- The term "inline" represents a partial line.

"""
from ply import yacc

from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.node import Node
from mash.shell2.ast.term import Word
from mash.shell2.tokenizer import main, tokens
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

    def p_lines_suffix(p):
        'lines : lines NEWLINE'
        # ignore trailing newline
        p[0] = p[2]

    def p_lines_infix(p):
        'lines : lines NEWLINE line'
        # parse from left to right
        p[1].extend(p[3])
        p[0] = p[1]

    def p_lines_newline(p):
        'lines : NEWLINE'
        pass

    def p_lines_empty(p):
        'lines : empty'
        pass

    def p_lines(p):
        'lines : line'
        p[0] = Lines(p[1])

    def p_line_command_args(p):
        'line : METHOD terms'
        p[0] = Command(Word(p[1]), *p[2])

    def p_line_command(p):
        'line : METHOD'
        p[0] = Command(Word(p[1]))

    # TODO allow e.g.
    # $ {1...3}
    # def p_line_command(p):
    #     'line : expression'
    #     p[0] = Command(p[1])

    def p_terms(p):
        'terms : terms term'
        p[1].extend(p[2])
        p[0] = p[1]

    def p_terms_term(p):
        'terms : term'
        p[0] = [p[1]]

    def p_term_command(p):
        'term : METHOD'
        # note that this yields Word, not Command
        p[0] = Word(p[1])

    def p_word(p):
        'term : WORD'
        p[0] = Word(p[1])

    def p_int(p):
        'term : INT'
        p[0] = Node(p[1])

    def p_empty(p):
        'empty :'
        pass

    def p_error(p):
        print(f'Syntax error: {p}')
        raise ShellSyntaxError(f'Syntax error: {p}')

    if init:
        global tokenizer
        tokenizer = main()
    else:
        tokenizer.clone()

    # parser = yacc.yacc(debug=True, write_tables=False)
    parser = yacc.yacc()

    if not isinstance(text, str):
        raise ValueError("Input is not a string: ", text, type(text))

    return parser.parse(text)


if __name__ == '__main__':
    # log = getLogger()
    # log.setLevel(1)
    print(parse('ok'))
