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
    |   |   └── IF line : block ELSE block
    |   └── for-loop
    |       └── FOR terms IN term : block
    |
    |── line ; line \\n line
    └── line \\n line \\n line
        |── list
        |   |── [ list , list , list]
        |   └── [ term , term , term ]
        |── list comprehension
        |   └── [ users |> user.id == 'a*' ]
        |── record_definition
        |   └── { .. = .., \\n .. = .. }
        |── record_update
        |   └── { .. | .. , \\n .. }
        |── set
        |   └── { .. || .. , \\n .. }
        |── assignment
        |   └── terms ASSIGN conjunction
        |── bool
        |── float
        |── int
        |── variable
        |── cast
        |   └── (int) 10.5
        └── command terms
                    └── terms term
                        |── word
                        |── float
                        └── int

Notes

- Multiline statements are not allowed in REPL mode.
"""
from ply import yacc

from mash.shell2.ast.array_list import ArrayList
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.multiline import IfElse
from mash.shell2.ast.function import Function
from mash.shell2.ast.term import Boolean, Cast, Float, Integer, Word
from mash.shell2.ast.variable import Variable
from mash.shell2.pre_parser import PreParser
from mash.shell2.tokenizer import tokens
from mash.shell.errors import ShellSyntaxError

tokenizer = None


def parse(text: str, debug=True, init=True):
    """Implement ply methods to parse text.
    """

    # precedence = (
    #     ('left', 'BREAK'),
    # )
    # _ply_constants = precedence, tokens
    _ply_constants = tokens

    def p_lines_infix(p):
        'lines : lines NEWLINE line'
        # parse from left to right
        p[1].items.append(p[3])
        p[0] = p[1]

    def p_lines_suffix(p):
        'lines : lines NEWLINE'
        # ignore trailing newline
        p[0] = p[1]

    # def p_lines_newline(p):
    #     'lines : NEWLINE'
    #     pass

    def p_lines(p):
        'lines : line'
        p[0] = Lines(p[1])

    def p_lines_empty(p):
        'lines : empty'
        pass

    def p_line_if_else(p):
        'line : IF line COLON BEGIN lines END ELSE COLON BEGIN lines END'
        p[0] = IfElse(p[2], p[5], p[10])

    def p_line_function_definition(p):
        'line : METHOD LPAREN terms RPAREN COLON BEGIN lines END'
        p[0] = Function(p[1], p[3], p[7])

    def p_line_terms(p):
        """line : bool
                | cast
                | number
                | list
                | var
        """
        """An expression stated on a new line.
        E.g.

        .. code-block:: sh

            $ [1, 2, 3]          # define a list
            $ (int) 1.5          # convert an int to float 
            $ $x                 # print the value of a variable
            $ print hello $name  # a command with arguments

        """
        p[0] = p[1]

    def p_line_command_args(p):
        'line : METHOD terms'
        p[0] = Command(Word(p[1]), *p[2])

    def p_line_command(p):
        'line : METHOD'
        p[0] = Command(Word(p[1]))

    def p_line_vars(p):
        'line : terms var'
        # E.g. `$x $y`
        raise ShellSyntaxError('No command was given. Only got variables.')

    def p_list(p):
        'list : LBRACE comma_args RBRACE'
        p[0] = ArrayList(p[2])

    def p_empty_list(p):
        'list : LBRACE RBRACE'
        p[0] = ArrayList([])

    def p_comma_args(p):
        'comma_args : comma_args COMMA comma_arg_value'
        p[1].append(p[3])
        p[0] = p[1]

    def p_comma_args_singleton_term(p):
        'comma_args : comma_arg_value'
        p[0] = [p[1]]

    def p_comma_arg_value(p):
        """comma_arg_value : term
                           | cast
                           | list
        """
        p[0] = p[1]

    def p_terms(p):
        """terms : terms cast
                 | terms list
                 | terms term
        """
        p[1].append(p[2])
        p[0] = p[1]

    def p_terms_term(p):
        """terms : cast
                 | term
        """
        p[0] = [p[1]]

    def p_term_var_bool(p):
        """term : bool
                | number
                | var
        """
        p[0] = p[1]

    def p_cast(p):
        """cast : casts list
                | casts term
        """
        p[0] = Cast(p[1], p[2])

    def p_multiple_casts(p):
        'casts : LPAREN METHOD RPAREN casts'
        p[0] = p[4] + (p[2],)

    def p_casts(p):
        'casts : LPAREN METHOD RPAREN'
        p[0] = (p[2],)

    def p_variable(p):
        'var : VARIABLE'
        p[0] = Variable(p[1][1:])

    def p_bool(p):
        'bool : BOOL'
        p[0] = Boolean(p[1])

    def p_term_command(p):
        'term : METHOD'
        # note that this yields Word, not Command
        p[0] = Word(p[1])

    def p_word(p):
        'term : WORD'
        p[0] = Word(p[1])

    def p_float(p):
        'number : FLOAT'
        p[0] = Float(p[1])

    def p_int(p):
        'number : INT'
        p[0] = Integer(p[1])

    def p_empty(p):
        'empty :'
        pass

    def p_error(p):
        print(f'Syntax error: {p}')
        raise ShellSyntaxError(f'Syntax error: {p}')

    if debug:
        parser = yacc.yacc(debug=1, write_tables=True)
    else:
        parser = yacc.yacc(optimize=1)

    if not isinstance(text, str):
        raise ValueError("Input is not a string: ", text, type(text))

    # tokenizer = PreParser.tokenizer
    return parser.parse(text, lexer=PreParser(debug, init))


if __name__ == '__main__':
    # log = getLogger()
    # log.setLevel(1)
    print(parse('ok'))
