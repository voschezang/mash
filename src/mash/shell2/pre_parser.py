from typing import List
from ply.lex import Lexer, LexToken

from mash.shell2.tokenizer import inner, main


class PreParser(Lexer):
    """A wrapper for a ply lexer (tokenizer).
    Each instance caches tokens and processes them on demand.

    Methods
    -------
    input(text)
        Process text

    token()
        Produce the next token
    """
    _tokenizer: Lexer | None = None

    def __init__(self, debug=True, init=True):
        """Use tokenizer.main to create a new tokenizer and access it as an attribute.
        This provides the necessary flexibility in defining token rules and using multiple tokenizers.
        """
        self._init_tokens()

        self.debug = debug
        self.has_input = False

        if init:
            PreParser._tokenizer = main(debug)
        else:
            if PreParser._tokenizer is None:
                raise RuntimeError('Tokenizer is not initialized')

            PreParser._tokenizer.clone()

    def _init_tokens(self):
        self.has_input = True
        self.tokens: List[LexToken] = []
        self.last_token: LexToken | None = None
        self.line = -1
        self.indent_stack: list[LexToken] = []

    def input(self, s):
        self.tokenizer.input(s)

        self._init_tokens()

    def token(self):
        """Produce the next token.
        Returns None when all tokens have been exhausted.
        """
        while self.tokens or self.has_input:

            if self.tokens:
                return self.pop_from_cache()

            token = self.tokenizer.token()

            if token and token.type == 'NEWLINE':
                # drop preceding newlines
                if self.last_token is None:
                    continue
                elif self.last_token.type in ('BEGIN', 'END'):
                    continue

                subsequent = self.peek()
                if not subsequent:
                    # drop trailing newlines
                    continue

                if infer_indent(subsequent) != self.indent():
                    # drop newline in favor of BEGIN/END blocks
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

    def peek(self) -> LexToken | None:
        """Returns the next token without consuming it.
        """
        if self.tokens:
            return self.tokens[-1]

        token = self.tokenizer.token()

        if token is None:
            return

        # copy token to the stack
        self.tokens.insert(0, token)

        return token

    @property
    def tokenizer(self):
        if PreParser._tokenizer is None:
            raise RuntimeError('Tokenizer is not initialized')

        return PreParser._tokenizer

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


def infer_indent(token: LexToken | None):
    if token is None:
        return 0

    if token.lexpos == 0:
        return 0

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
