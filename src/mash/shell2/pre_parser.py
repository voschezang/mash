from mash.shell2.tokenizer import tokenize
from mash.shell2.tokenizer import inner, main, tokens

tokenizer = None


class Preparser:
    def __init__(self, debug=True, init=True):
        self.debug = debug
        self.has_input = False

        if init:
            global tokenizer
            tokenizer = main(debug)
        else:
            tokenizer.clone()

    def input(self, text):
        tokenizer.input(text)
        self.has_input = True

    def token(self):
        token = tokenizer.token()
        if token:
            return token

        self.has_input = False
        return
