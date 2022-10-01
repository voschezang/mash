#!/usr/bin/python3
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple
import logging
import os
import sys
import traceback

import io_util
from shell_base import BaseShell
import shell_function as func
from shell_function import ShellFunction as Function
from io_util import ArgparseWrapper, bold, has_argument, has_output, log, read_file
import util


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

{bold('Interopability')}
Interopability with Bash can be done with pipes:
    `|>` for Python.
    `|`  for Bash
    `>`  for Bash (write to file)

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
    """Extend BaseShell(Cmd) with helper functions.
    """
    default_function_group_key = '_'

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.functions: Dict[str, List[str, Function]] = defaultdict(list)

    def do_exit(self, args):
        """exit [code]

        Wrapper for sys.exit(code) with default code: 0
        """
        if not args:
            args = 0

        sys.exit(int(args))

    def do_shell(self, args):
        """System call
        """
        logging.info(f'Cmd = !{args}')
        # TODO add option to forward environment variables
        os.system(args)

    def do_cat(self, filename):
        """Concatenate and print files
        """
        return ''.join((Path(f).read_text() for f in filename.split()))

    def do_print(self, args):
        """Mimic Python's print function
        """
        logging.debug(f'Cmd = print {args}')
        return args

    def do_echo(self, args):
        """Mimic Bash's print function
        """
        logging.debug(f'Cmd = echo {args}')
        return args

    def do_env(self, keys: str):
        """Retrieve environment variables.
        Return all variables if no key is given.
        """
        data = self.env
        if keys:
            try:
                data = {k: self.env[k] for k in keys.split()}
            except KeyError:
                log('Invalid key')
                return

        return data

    def do_export(self, args: str):
        """Set an environment variable.
        `export(k, *values)`
        """
        k, *v = args.split()

        if len(v) == 0:
            log(f'unset {k}')
            if k in self.env:
                del self.env[k]
            else:
                log('Invalid key')
            return

        elif len(v) == 1:
            v = v[0]

        log(f'set {k}')
        self.set_env_variable(k, v)

    def do_E(self, args):
        """Show the last exception
        """
        traceback.print_exception(
            type(func.last_exception), func.last_exception, func.last_traceback)

    def do_save(self, _):
        self.save_session()

    def do_reload(self, _):
        self.load_session()

    def last_method(self):
        """Find the method corresponding to the last command run in `shell`.
        It has the form: do_{cmd}

        Return a the last method if it exists and None otherwise.
        """
        # TODO integrate this into Shell and store the last succesful cmd

        if not self.lastcmd:
            return

        cmd = self.lastcmd.split()[0]
        return Shell.get_method(cmd)

    @staticmethod
    def get_method(method_suffix: str):
        method_name = f'do_{method_suffix}'
        if not util.has_method(Shell, method_name):
            return

        method = getattr(Shell, method_name)

        if isinstance(method, Function):
            return method.func

        return method

    def add_functions(self, functions: Dict[str, Function], group_key=None):
        """Add commands to this instance of CMD.
        These will be hidden from the help view, unlike shell.set_functions.
        Use a key to select a group of functions
        """
        if group_key is None:
            group_key = Shell.default_function_group_key

        for key, func in functions.items():
            set_functions({key: func}, self)
            self.functions[group_key].append(key)

    def remove_functions(self, group_key=None):
        if group_key is None:
            group_key = Shell.default_function_group_key

        for key in self.functions[group_key]:
            delattr(self, f'do_{key}')

        del self.functions[group_key]


def all_commands(cls=Shell):
    for cmd in vars(cls):
        if cmd.startswith('do_') and util.has_method(cls, cmd):
            yield cmd.lstrip('do_')


def set_functions(functions: Dict[str, Function], cls=Shell):
    """Extend `Shell` with a set of functions
    Note that this modifies the class Shell directly, rather than an instance.
    """
    for key, func in functions.items():
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


def add_cli_args(parser: ArgumentParser):
    if not has_argument(parser, 'cmd'):
        parser.add_argument('cmd', nargs='*',
                            help='A comma- or newline-separated list of commands')
    if not has_argument(parser, 'safe'):
        parser.add_argument('-s', '--safe', action='store_true',
                            help='Safe-mode. Ask for confirmation before executing commands.')
    if not has_argument(parser, 'file'):
        parser.add_argument('-f', '--file',
                            help='Read and run FILE as a commands')
    if not has_argument(parser, 'reload'):
        parser.add_argument('-r', '--reload', action='store_true',
                            help='Reload last session')
    if not has_argument(parser, 'session'):
        parser.add_argument('--session', default=None,
                            help='Use session SESSION')


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

    return io_util.parse_args.cmd != []


def read_stdin():
    if not has_output(sys.stdin):
        return ''

    try:
        yield from sys.__stdin__

    except KeyboardInterrupt as e:
        print()
        logging.info(e)
        exit(130)


def run(shell, commands, filename, repl=True):
    if commands or filename is not None:
        # compile mode
        if filename is not None:
            run_commands_from_file(filename, shell)

        if commands:
            run_command(commands, shell, strict=True)

    elif repl:
        run_interactively(shell)


def setup(shell) -> Tuple[Shell, List[str], str]:
    set_cli_args()
    logging.info(f'args = {io_util.parse_args}')

    if shell is None:
        shell = Shell()

        if io_util.parse_args.reload:
            shell.try_load_session()

        if io_util.parse_args.session:
            shell.load_session(io_util.parse_args.session)

    commands = ' '.join(io_util.parse_args.cmd + list(read_stdin()))
    filename = io_util.parse_args.file
    return shell, commands, filename


def run_commands_from_file(filename: str, shell: Shell):
    command = read_file(filename)
    run_command(command, shell, strict=True)


def run_command(command='', shell: Shell = None, strict=None):
    """Run a single command in using `shell`.

    Parameters
    ----------
        strict : bool
            Raise exceptions when encountering invalid syntax.
    """
    if shell is None:
        shell = Shell()

    if strict is not None:
        shell.ignore_invalid_syntax = not strict

    for line in command.splitlines():
        if line:
            shell.onecmd(line)


def run_interactively(shell):
    io_util.interactive = True
    shell.auto_save = True
    shell.cmdloop()


def main(functions: Dict[str, Function] = {}, shell=None, repl=True) -> Shell:
    if functions:
        set_functions(functions)

    shell, commands, filename = setup(shell)
    run(shell, commands, filename, repl)
    return shell


if __name__ == '__main__':
    main()
