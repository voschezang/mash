from ply.lex import LexToken

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
        self.line = -1

    def input(self, text):
        tokenizer.input(text)

        self._init_tokens()

    def token(self):
        """Produce the next token.
        Returns None when all tokens have been exhausted.
        """
        while self.tokens or self.has_input:
            if self.tokens:
                lexpos = self.tokens[0].lexpos
                lineno = self.tokens[0].lineno

                # handle indentation
                if lineno > self.line:
                    self.line = lineno
                    if lexpos > 0:
                        token = create_indent_token(lexpos, lineno)
                        self.tokens.insert(0, token)

                return self.tokens.pop(0)

            token = tokenizer.token()

            if not token:
                self.has_input = False
                break

            self.tokens.append(token)

        return


def create_indent_token(lexpos, lineno):
    token = LexToken()
    token.type = 'INDENT'
    token.value = ''
    token.lineno = lineno
    token.lexpos = lexpos
    return token


def tokenize(data: str):
    return inner(data, tokenizer=PreParser())
