"""Parse tokens.
Tokens are defined in shell.grammer.tokenizer

Parsing rules;

.. code-block:: yaml

    lines: a BREAK-separated sequence of line
    line: statement with optional INDENT
    statement: 
        - assignment
        - conditional
        - conjunction
        - definition
        - return_statement
    conjunction: a PIPE-separated sequence of expression
    expression: a command

"""
from logging import getLogger
import ply.yacc as yacc
from mash.shell.ast import Assign, BashPipe, BinaryExpression, Else, ElseIf, ElseIfThen, FunctionDefinition, If, IfThen, IfThenElse, Indent, InlineFunctionDefinition, Lines, LogicExpression, Map, Math, Method, Pipe, Quoted, Return, Shell, Terms, Then, Variable, Word
from mash.shell.grammer.tokenizer import main, tokens
from mash.shell.grammer.parse_functions import indent_width
from mash.shell.errors import ShellSyntaxError

tokenizer = None


def parse(text, init=True):
    """Implement ply methods
    """

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
    _ply_constants = precedence, tokens

    def p_lines_empty(p):
        """lines : BREAK
                 | INDENT BREAK
        """
        'lines : BREAK'
        # TODO handle `indent expr ; expr`
        p[0] = Lines([])

    def p_lines_suffix(p):
        """lines : line
                 | line BREAK
        """
        p[0] = Lines([p[1]])

    def p_lines_infix(p):
        'lines : line BREAK lines'
        p[0] = Lines([p[1]]) + p[3]

    def p_lines_prefix(p):
        'lines : BREAK lines'
        p[0] = p[2]

    def p_line_indented(p):
        'line : INDENT statement'
        n = indent_width(p[1])
        p[0] = Indent(p[2], n)

    def p_line(p):
        'line : statement'
        p[0] = p[1]

    def p_line_indent_empty(p):
        'line : INDENT'
        n = indent_width(p[1])
        p[0] = Indent(None, n)

    def p_statement(p):
        """statement : assignment
                     | conditional
                     | conjunction
                     | definition
                     | return_statement
        """
        p[0] = p[1]

    def p_statement_return(p):
        'return_statement : RETURN conjunction'
        p[0] = Return(p[2])

    def p_final_statement(p):
        """final_statement : conjunction
                           | return_statement
        """
        p[0] = p[1]

    def p_assign(p):
        'assignment : terms ASSIGN conjunction'
        p[0] = Assign(p[1], p[3], p[2])

    def p_assign_right(p):
        'assignment : conjunction ASSIGN_RIGHT terms'
        p[0] = Assign(p[3], p[1], p[2])

    def p_def_inline_function(p):
        'definition : METHOD LPAREN terms RPAREN DEFINE_FUNCTION conjunction'
        p[0] = InlineFunctionDefinition(p[1], p[3], body=p[6])

    def p_def_inline_function_constant(p):
        'definition : METHOD LPAREN RPAREN DEFINE_FUNCTION conjunction'
        p[0] = InlineFunctionDefinition(p[1], body=p[5])

    def p_def_function(p):
        'definition : METHOD LPAREN terms RPAREN DEFINE_FUNCTION'
        p[0] = FunctionDefinition(p[1], p[3])

    def p_def_function_constant(p):
        'definition : METHOD LPAREN RPAREN DEFINE_FUNCTION'
        p[0] = FunctionDefinition(p[1])

    def p_scope(p):
        'scope : LPAREN conjunction RPAREN'
        q = p[2]
        p[0] = ('scope', q)

    def p_if(p):
        'conditional : IF conjunction'
        p[0] = If(p[2])

    def p_full_conditional(p):
        'full_conditional : IF conjunction THEN conjunction ELSE conjunction'
        _, _if, cond, _then, true, _else, false = p
        p[0] = IfThenElse(cond, true, false)

    def p_if_then_else(p):
        'conditional : IF conjunction THEN conjunction ELSE'
        _, _if, cond, _then, true, _else = p
        p[0] = IfThenElse(cond, true)

    def p_if_then_inline(p):
        'full_conditional : IF conjunction THEN conjunction'
        _, _if, cond, _then, true = p
        p[0] = IfThen(cond, true)

    def p_if_then(p):
        'conditional : IF conjunction THEN'
        p[0] = IfThen(p[2])

    def p_if_then_inline_final(p):
        'conditional : IF conjunction THEN return_statement'
        _, _if, cond, _then, true = p
        p[0] = IfThen(cond, true)

    def p_then(p):
        """conditional : THEN final_statement
                       | THEN
        """
        if len(p) == 2:
            p[0] = Then()
        else:
            p[0] = Then(then=p[2])

    def p_else_if_then(p):
        """conditional : ELSE IF conjunction THEN final_statement
                      | ELSE IF conjunction THEN
        """
        if len(p) == 6:
            p[0] = ElseIfThen(p[3], p[5])
        else:
            p[0] = ElseIfThen(p[3])

    def p_else_if(p):
        'conditional : ELSE IF conjunction'
        p[0] = ElseIf(p[3])

    def p_else(p):
        """conditional : ELSE final_statement
                       | ELSE
        """
        if len(p) == 2:
            p[0] = Else()
        else:
            p[0] = Else(otherwise=p[2])

    def p_conjunction_of_expressions(p):
        'conjunction : expression PIPE conjunction'
        p[0] = Pipe(p[1], p[3], p[2])

    def p_conjunction(p):
        'conjunction : expression'
        p[0] = p[1]

    def p_pipe_bash(p):
        'expression : expression BASH expression'
        p[0] = BashPipe(p[1], p[3], p[2])

    def p_pipe_map(p):
        'expression : expression MAP expression'
        p[0] = Map(p[1], p[3])

    def p_expression_full_conditional(p):
        'expression : full_conditional'
        p[0] = p[1]

    def p_expression(p):
        """expression : join
                            | logic_expression
        """
        p[0] = p[1]

    def p_shell(p):
        'expression : SHELL expression'
        p[0] = Shell(p[2])

    def p_shell_empty(p):
        'expression : SHELL'
        p[0] = Shell()

    def p_math(p):
        'expression : MATH expression'
        p[0] = Math(p[2])

    def p_logic_binary(p):
        """join : logic_expression AND join
                | logic_expression AND logic_expression
                | logic_expression OR join
                | logic_expression OR logic_expression
        """
        # TODO use flat tree any/all (or, a, b, c) = any : e OR any  | e OR e
        p[0] = LogicExpression(p[1], p[3], p[2])

    def p_logic_expression_infix(p):
        'logic_expression : terms INFIX_OPERATOR logic_expression'
        p[0] = BinaryExpression(p[1], p[3], p[2])

    def p_logic_expression_infix_equals(p):
        'logic_expression : logic_expression EQUALS logic_expression'
        p[0] = BinaryExpression(p[1], p[3], p[2])

    def p_logic_negation(p):
        'logic_expression : NOT terms'
        # TODO
        p[0] = ('not', p[2])

    def p_logic(p):
        'logic_expression : terms'
        p[0] = p[1]

    # def p_terms_pair(p):
    #     'terms : term term'
    #     p[0] = Terms([p[1], p[2]])

    def p_terms_head_tail(p):
        'terms : term terms'
        p[0] = Terms([p[1]] + p[2].values)

    def p_terms_singleton(p):
        'terms : term'
        p[0] = Terms([p[1]])

    def p_term(p):
        """term : SPECIAL
                | WORD
                | WORD_WITH_DOT
        """
        p[0] = Word(p[1], 'term')

    def p_term_value(p):
        """term : value
                | method
                | scope
        """
        p[0] = p[1]

    def p_value_wildcard(p):
        'value : WILDCARD'
        p[0] = Word(p[1], 'wildcard')

    def p_value_wildcard_range(p):
        'value : WILDCARD_RANGE'
        p[0] = Word(p[1], 'range')

    def p_value_number_int(p):
        'value : NUMBER'
        p[0] = Word(p[1], 'number')

    def p_value_number_float(p):
        'value : NUMBER_WITH_DOT'
        p[0] = Word(p[1], 'number')

    def p_value_method(p):
        'method : METHOD'
        p[0] = Method(p[1])

    def p_value_variable(p):
        'value : VARIABLE'
        p[0] = Variable(p[1])

    def p_value_symbol(p):
        """value : SYMBOL
                 | LONG_SYMBOL
        """
        p[0] = Word(p[1], 'symbol')

    def p_value_literal_string(p):
        'value : SINGLE_QUOTED_STRING'
        p[0] = Word(p[1], 'literal string')

    def p_value_string(p):
        'value : DOUBLE_QUOTED_STRING'
        p[0] = Quoted(p[1])

    def p_illegal_if_then(p):
        """conditional : IF THEN
                       | IF INDENT THEN
                       | IF ELSE
                       | IF INDENT ELSE
                       | ELSE THEN
                       | ELSE INDENT THEN
        """
        raise ShellSyntaxError(
            f'Syntax error: invalid if-then-else statement: {p}')

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
