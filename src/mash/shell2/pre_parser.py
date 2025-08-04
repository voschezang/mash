from typing import Literal
from ply.lex import LexToken

from mash.shell.grammer import parse_functions
from mash.shell2.tokenizer import tokenize
from mash.shell2.tokenizer import inner, main

tokenizer = None


class PreParser:
    """A wrapper for a ply lexer (tokenizer).
    Each instance caches tokens and processes them on demand.

    Methods
    -------
    input(text)
        Process text

    token()
        Produce the next token
    """

    def __init__(self, debug=True, init=True):
        self._init_tokens()

        self.debug = debug
        self.has_input = False

        if init:
            global tokenizer
            tokenizer = main(debug)
        else:
            tokenizer.clone()

    def _init_tokens(self):
        self.has_input = True
        self.tokens = []
        self.last_token = None
        self.line = -1
        self.indent_stack = []

    def input(self, text):
        tokenizer.input(text)

        self._init_tokens()

    def token(self):
        """Produce the next token.
        Returns None when all tokens have been exhausted.
        """
        while self.tokens or self.has_input:

            if self.tokens:
                return self.pop_from_cache()

            token = tokenizer.token()

            if token and token.type == 'NEWLINE':
                # drop preceding newlines
                if self.last_token is None:
                    continue
                elif self.last_token.type in ('BEGIN', 'END'):
                    continue

                subsequent = self.peek()
                # if subsequent and subsequent.type == 'NEWLINE':
                #     # drop consecutive newlines
                #     continue

                if not subsequent:
                    # drop trailing newlines
                    continue

            if not token:
                self.has_input = False
                break

            self.tokens.append(token)

        while self.indent_stack:
            begin = self.indent_stack.pop()
            # use previous token as reference instead of the next token
            end = create_token('END', reference=begin)
            return end

        return

    def peek(self) -> LexToken:
        """Returns the next token without consuming it.
        """
        if self.tokens:
            return self.tokens[-1]

        token = tokenizer.token()

        if token is None:
            return

        # copy token to the stack
        self.tokens.insert(0, token)

        return token

    def pop_from_cache(self) -> LexToken:
        token = self.tokens[-1]

        if token.lineno > self.line and token.type != 'NEWLINE':
            self.line = token.lineno
            self.handle_indentation()

        # note that the stack may have changed after handle_indentation()
        self.last_token = self.tokens.pop()
        return self.last_token

    def handle_indentation(self):
        """Insert BEGIN and END tokens for each change in indentation.
        """
        token = self.tokens[-1]

        if token.type == 'NEWLINE':
            # ignore indentation of newlines
            indent = infer_indent(self.last_token)
        else:
            indent = infer_indent(token)

        if indent > self.indent():
            begin = create_token('BEGIN', reference=token)

            self.tokens.append(begin)
            self.indent_stack.append(begin)

        elif indent < self.indent():
            self.indent_stack.pop()

            end = create_token('END', reference=token)
            self.tokens.append(end)

            # handle nested indentation
            self.handle_indentation()

    def indent(self) -> int:
        if not self.indent_stack:
            return 0

        return infer_indent(self.indent_stack[-1])


def infer_indent(token: LexToken):
    # tabs are treated like indent of 1
    previous = token.lexer.lexdata.rfind('\n', 0, token.lexpos)

    if previous == -1:
        # no previous newline found
        return token.lexpos

    return token.lexpos - previous - 1


def create_token(token_type: str, reference: LexToken) -> LexToken:
    token = LexToken()
    token.type = token_type
    token.value = ''
    token.lineno = reference.lineno
    token.lexpos = reference.lexpos
    token.lexer = reference.lexer
    return token


def tokenize(data: str):
    return inner(data, tokenizer=PreParser())
