from argparse import ArgumentParser
from cmd import Cmd
from copy import deepcopy
import subprocess
from typing import Callable, Dict, Iterable, List, Tuple
import logging
import os
import sys

from mash import io_util
from mash.io_util import ArgparseWrapper, bold, has_argument, has_output, log, log_once
from mash.shell.function import LAST_RESULTS
from mash.shell.ast import ElseCondition, Indent, Lines, Map, Math, Node, Term, Terms
from mash.shell.base import BaseShell
from mash.shell.cmd2 import default_prompt, run
from mash.shell.grammer.delimiters import DEFINE_FUNCTION
from mash.shell.errors import ShellError, ShellPipeError, ShellSyntaxError
from mash.shell.errors import ShellSyntaxError
from mash.shell.function import ShellFunction as Function
from mash.shell.internals.if_statement import Abort, handle_prev_then_else_statements
from mash.shell.grammer.parser import parse
from mash.util import has_method, is_valid_method_name

description = 'If no positional arguments are given then an interactive subshell is started.'
epilog = f"""
--------------------------------------------------------------------------------
{bold('Default Commands')}
Run shell commands by prefixing them with `!`.
E.g.
    ./shell.py !echo abc; echo def # Bash

Run multiple Python commands by separating each command with colons or newlines.
E.g.
    ./shell.py 'print abc; print def \n print ghi'

{bold('Variables')}
Assign constants or evaluate expressiosn:
```
a = 100
b <- print $a
echo $a $b
```

{bold('Interopability')}
Interopability with Bash can be done with pipes:
    `|>` for Python.
    `|`  for Bash
    `>-`  for Bash (write to file)
    `>>`  for Bash (append to file)

1. To stdin and stdout
E.g.
    echo abc | ./shell.py print
    ./shell.py print abc | echo

2. Within the dsl
E.g.
    ./shell.py print abc # Python
    ./shell.py 'print abc | echo'
    ./shell.py 'print abc |> print'
"""


class Shell(BaseShell):
    def onecmd_inner(self, lines: str):
        if not self.use_model:
            return super().onecmd_inner(lines)

        ast = parse(lines)
        if ast is None:
            raise ShellError('Invalid syntax: AST is empty')

        try:
            self.run_commands(ast, '', run=True)

        except ShellPipeError as e:
            if self.ignore_invalid_syntax:
                log(e)
                return

            raise ShellError(e)

        except subprocess.CalledProcessError as e:
            returncode, stderr = e.args
            log(f'Shell exited with {returncode}: {stderr}')

            if self.ignore_invalid_syntax:
                return

            raise ShellError(str(e))

    def run_commands(self, ast: Node, prev_result='', run=False):
        if isinstance(ast, Term):
            return ast.run(prev_result, shell=self, lazy=not run)

        elif isinstance(ast, str):
            return self.run_commands(Term(ast), prev_result, run=run)

        done = self._handle_define_function(ast)
        if done:
            return

        if not isinstance(ast, ElseCondition) and \
                not isinstance(ast, Indent) and \
                not isinstance(ast, Lines):
            try:
                handle_prev_then_else_statements(self)
            except Abort:
                return prev_result

        if isinstance(ast, Node):
            return ast.run(prev_result, shell=self, lazy=not run)
        else:
            raise NotImplementedError()

    def _handle_define_function(self, ast: Node) -> bool:
        if DEFINE_FUNCTION not in self.locals:
            return False

        # self._extend_inline_function_definition(line)
        f = self.locals[DEFINE_FUNCTION]

        if isinstance(ast, Indent):
            # TODO compare indent width
            width = ast.indent
            if ast.data is None:
                return True

            if f.line_indent is None:
                f.line_indent = width

            if width >= f.line_indent:
                self.locals[DEFINE_FUNCTION].inner.append(ast)
                return True

            self._finalize_define_function(f)

        elif not isinstance(ast, Lines):
            # TODO this will only be triggered after a non-Word command
            self._finalize_define_function(f)

        return False

    def _finalize_define_function(self, f):
        self.env[f.func_name] = f
        self.locals.rm(DEFINE_FUNCTION)
        self.prompt = default_prompt

    def parse(self, results: str):
        # TODO mv this function
        # SMELL avoid circular import: base => model => lex_parser => model
        return parse(results)

    ############################################################################
    # Commands: do_*
    ############################################################################

    def do_map(self, line=''):
        """Apply a function to each item.
        It can be used as prefix or infix operator.

        Usage (prefix)
        --------------
            `map f x y z` 

        Usage (infix)
        -------------
            `f x |> map g`
            `f x |> map g $ a b`
            `f x >>= g`

        If `$` is present, then each line from stdin is inserted there.
        Otherwise each line is appended.
        """
        items = line.split(' ')
        if len(items) < 2:
            raise ShellError('Expected multiple arguments')

        f, *args = items
        for arg in args:
            self.onecmd(f'{f} {arg}')

    def foldr(self, commands: List[Term], prev_results: str, delimiter='\n'):
        items = parse(prev_results).values
        k, acc, *args = commands

        for item in items:
            command = Terms([k, acc] + args)
            acc = self.run_commands(command, item, run=True)

            if str(acc).strip() == '' and self._last_results:
                acc = self._last_results[-1]
                self.env[LAST_RESULTS] = []

        return acc

    def do_math(self, args: str) -> str:
        result = Math.eval(args, self.env)

        if isinstance(result, bool):
            self._save_result(result)
            return ''

        return str(result)

################################################################################
# Helpers
################################################################################


def all_commands(shell: Shell):
    for cmd in dir(shell):
        if cmd.startswith('do_') and has_method(shell, cmd):
            yield cmd.lstrip('do_')


def set_functions(functions: Dict[str, Function], cls: Cmd = Shell) -> type:
    """Extend `cls` with a set of functions
    Note that this modifies the class Shell directly, rather than an instance.
    """
    for key, func in functions.items():
        if not is_valid_method_name(key):
            log_once(f'Key: {key} is not a valid method name')

        if not isinstance(func, Function):
            func = Function(func)

        setattr(cls, f'do_{key}', func)
        setattr(getattr(cls, f'do_{key}'), '__doc__', func.help)


def set_completions(functions: Dict[str, Callable], shell=Shell):
    for key, func in functions.items():
        setattr(shell, f'complete_{key}', func)


def sh_to_py(cmd: str):
    """A wrapper for shell commands
    """
    def func(*args):
        args = ' '.join(args)
        return os.system(''.join(cmd + ' ' + args))

    func.__name__ = cmd
    return func


def run_command(command='', shell: Shell = None, strict=None):
    """Run a newline-separated string of commands.

    Parameters
    ----------
        strict : bool
            Raise exceptions when encountering invalid syntax.
    """
    if shell is None:
        shell = Shell()

    if strict is not None:
        shell.ignore_invalid_syntax = not strict

    shell.onecmd(command)


def add_cli_args(parser: ArgumentParser):
    if not has_argument(parser, 'cmd'):
        parser.add_argument('cmd', nargs='*',
                            help='A comma- or newline-separated list of commands')
    if not has_argument(parser, 'safe'):
        parser.add_argument('-s', '--safe', action='store_true',
                            help='Safe-mode. Ask for confirmation before executing commands.')
    if not has_argument(parser, 'file'):
        parser.add_argument('-f', '--file',
                            help='Read and run FILE as a command')
    if not has_argument(parser, 'reload'):
        parser.add_argument('-r', '--reload', action='store_true',
                            help='Reload last session')
    if not has_argument(parser, 'session'):
        parser.add_argument('--session', default=None,
                            help='Use SESSION')


def set_cli_args():
    global confirmation_mode

    with ArgparseWrapper(description=description) as parser:
        add_cli_args(parser)

    if io_util.parse_args.safe:
        confirmation_mode = True
        io_util.interactive = True


def has_input():
    # ensure argparse has been called
    with ArgparseWrapper(description=description):
        pass

    if 'cmd' not in io_util.parse_args:
        raise NotImplementedError(
            'Missing expected arg `cmd`. Has set_cli_args() been run?')

    return io_util.parse_args.cmd != []


def read_stdin():
    if not has_output(sys.stdin):
        return ''

    try:
        yield from sys.__stdin__

    except KeyboardInterrupt as e:
        print()
        logging.debug(e)
        exit(130)


def build(functions: Dict[str, Function] = None, completions: Dict[str, Callable] = None, instantiate=True) -> Shell:
    """Extend the class Shell and create an instance of it.
    Note that `set_functions` must be called before instantiating Shell.
    """
    # copy class to avoid side-effects
    CustomShell = deepcopy(Shell)

    if functions:
        set_functions(functions, CustomShell)
    if completions:
        set_completions(completions, CustomShell)

    if instantiate:
        return CustomShell()
    return CustomShell


def setup(shell: Shell = None, functions: Dict[str, Function] = None, completions: Dict[str, Callable] = None) -> Tuple[Shell, List[str], str]:
    """Setup an instance of Shell with any given cli options.

    First initialize Shell with `functions` and `completions`.
    Then apply any relevant cli options.
    """
    set_cli_args()
    logging.info(f'args: {io_util.parse_args}')

    if shell is None:
        shell = build(functions, completions)
    elif functions is not None or completions is not None:
        raise ValueError(
            'Incompatible argumets: `shell` and `functions` or `completions`')

    if io_util.parse_args.reload:
        shell.try_load_session()
    if io_util.parse_args.session:
        shell.load_session(io_util.parse_args.session)

    commands = ' '.join(io_util.parse_args.cmd + list(read_stdin()))
    filename = io_util.parse_args.file

    return shell, commands, filename


def main(shell: Shell = None, functions: Dict[str, Function] = None, repl=True) -> Shell:
    shell, commands, filename = setup(shell, functions)

    try:
        run(shell, commands, filename, repl)
    except ShellSyntaxError as e:
        log(e, prefix='')
        sys.exit(1)

    return shell


if __name__ == '__main__':
    main()
