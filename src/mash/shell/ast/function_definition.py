import logging
from mash.shell.delimiters import DEFINE_FUNCTION
from mash.shell.ast.node import Node
from mash.shell.base import BaseShell
from mash.shell.errors import ShellError
from mash.shell.function import InlineFunction
from mash.util import has_method


class FunctionDefinition(Node):
    def __init__(self, f, args=None, body=None):
        self.f = f
        self.args = [] if args is None else args
        self.body = body

    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        args = self.define_function(shell, lazy)

        # TODO use line_indent=self.locals[RAW_LINE_INDENT]
        shell.locals.set(DEFINE_FUNCTION,
                         InlineFunction('', args, func_name=self.f))
        shell.prompt = '>>>    '

    def define_function(self, shell, lazy: bool):
        if lazy:
            raise NotImplementedError()

        args = self.args
        if args:
            args = shell.run_commands(args)

        if has_method(shell, f'do_{self.f}'):
            raise ShellError()
        elif shell.is_function(self.f):
            logging.debug(f'Re-define existing function: {self.f}')

        if shell.auto_save:
            logging.warning(
                'Instances of InlineFunction are incompatible with serialization')
            shell.auto_save = False

        return args

    @property
    def data(self) -> str:
        return f'{self.f}( {self.args} )'


class InlineFunctionDefinition(FunctionDefinition):
    def run(self, prev_result='', shell: BaseShell = None, lazy=False):
        args = self.define_function(shell, lazy)

        # TODO use parsing.expand_variables_inline
        shell.env[self.f] = InlineFunction(self.body, args, func_name=self.f)
