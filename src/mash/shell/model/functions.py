from contextlib import contextmanager
from dataclasses import dataclass
from itertools import repeat
import logging
import shlex
import subprocess
from typing import List, Union
from mash.filesystem.filesystem import cd
from mash.io_util import log
from mash.shell.base import BaseShell
from mash.shell.model.delimiters import bash, FALSE
from mash.shell.errors import ShellError
from mash.shell.function import scope
from mash.shell.if_statement import Abort
from mash.util import quote_all

INNER_SCOPE = 'inner_scope'


@dataclass
class ReturnValue:
    data: str


def run_shell_command(line: str, prev_result: str, delimiter='|') -> str:
    """
    May raise subprocess.CalledProcessError
    """
    assert delimiter in bash or delimiter is None

    if delimiter == '>-':
        delimiter = '>'

    if delimiter is not None:
        # pass last result to stdin
        line = f'echo {shlex.quote(prev_result)} {delimiter} {line}'

    logging.info(f'Cmd = {line}')

    result = subprocess.run(line,
                            capture_output=True,
                            check=True,
                            shell=True)

    stdout = result.stdout.decode().rstrip('\n')
    stderr = result.stderr.decode().rstrip('\n')

    log(stderr)
    return stdout


def run_function(k, args: List[str], shell=None):
    # TODO encapsulate these branches in the domain classes
    if shell.is_special_function(k):
        return shell.run_special_function(k, args)

    if shell.is_inline_function(k):
        return call_inline_function(shell, k, args)

    if shell.is_hidden_function(k):
        return shell.run_hidden_function(k, args)

    raise Abort()


def call_inline_function(shell, func_key: str, args: list):
    f = shell.env[func_key]
    args = [str(arg) for arg in args]

    translations = {}

    if len(args) != len(f.args):
        msg = f'Invalid number of arguments: {len(f.args)} arguments expected.'
        if shell.ignore_invalid_syntax:
            log(msg)
            return FALSE
        else:
            raise ShellError(msg)

    # translate variables in inline functions
    for i, k in enumerate(f.args):
        # quote item to preserve `\n`
        translations[k] = shlex.quote(args[i])

    with enter_new_scope(shell):

        for i, k in enumerate(f.args):
            # quote item to preserve `\n`
            # self.env[k] = shlex.quote(args[i])
            shell.env[k] = args[i]

        if f.inner == []:
            return shell.run_commands(f.command, run=True)

        # TODO rm impossible state
        assert f.command == ''

        result = ''
        for ast in f.inner:
            result = shell.run_commands(ast, prev_result=result,
                                        run=True)

            if isinstance(result, ReturnValue):
                return result.data

        if isinstance(result, ReturnValue):
            return result.data


def set_env_variables(shell, keys: Union[str, List[str]], result: str):
    """Set the variables `keys` to the values in result.
    """
    if result is None:
        raise ShellError(f'Missing return value in assignment: {keys}')

    if isinstance(keys, str):
        keys = keys.split(' ')
    elif not isinstance(keys, list):
        # assume isinstance(keys, Node)
        keys = keys.values

    try:
        if len(result) == len(keys):
            shell.env.update(items=zip(keys, result))
            return
    except TypeError:
        pass

    if len(keys) == 1:
        if isinstance(result, list):
            result = ' '.join(quote_all(result))
        shell.env[keys[0]] = result
    elif isinstance(result, str) or isinstance(result, Term):
        lines = result.split('\n')
        terms = result.split(' ')
        if len(lines) == len(keys):
            shell.env.update(items=zip(keys, lines))

        elif len(terms) == len(keys):
            shell.env.update(items=zip(keys, terms))

        elif result == '':
            shell.env.update(items=zip(keys, repeat('')))

    else:
        raise ShellError(
            f'Cannot assign values to all keys: {" ".join(keys)}')


@contextmanager
def enter_new_scope(cls: BaseShell, scope_name=INNER_SCOPE):
    """Create a new scope, then change directory into that scope.
    Finally exit the new scope.
    """
    cls.locals.set(scope_name, scope())
    try:
        with cd(cls.locals, scope_name):
            cls.init_current_scope()
            yield
    finally:
        pass
