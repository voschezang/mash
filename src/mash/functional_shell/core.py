from cmd import Cmd
from dataclasses import dataclass
from mash.functional_shell.env import Environment
from mash.functional_shell.parser import parse


class Shell(Cmd):
    def __init__(self, env):
        super().__init__()
        self.env = env

    def precmd(self, line):
        ast = parse(line)
        self.env = ast.run(self.env)
        return line


class Core:
    def __init__(self):
        self.env = Environment({}, {})
        self.shell = Shell(self.env)

    def compile(self, lines: str):
        ast = parse(lines)
        ast.run(self.env)

    def repl(self):
        self.shell.cmdloop()

    def repl2(self):
        text = []
        ast = []
        line = None

        while True:
            if line is not None:
                try:
                    self.env = next(line)
                except StopIteration:
                    line = None
            elif ast:
                line = [ast.pop()]
            elif text:
                ast = parse(text.pop())


if __name__ == '__main__':
    core = Core()
    # core.repl()
    core.compile('abc')
