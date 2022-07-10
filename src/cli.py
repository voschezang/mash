#!/usr/bin/python3
import sys
from quo.completion import NestedCompleter
from quo.history import MemoryHistory
from quo.prompt import Prompt
from quo.text import Text

from dsl import Shell, run_command, Function, ShellException
from util import has_method, infer_synopsis


def main():
    shell = Shell()

    # setup a completion-dropdown
    completer = NestedCompleter.add({k: None for k in Shell.all_commands()})

    # setup a history-completion
    for cmd in Shell.all_commands():
        MemoryHistory.append(cmd)

    session = Prompt(
        history=MemoryHistory,
        suggest="history",
        enable_history_search=True,
        completer=completer,
        vi_mode=True,
        bottom_toolbar=lambda: toolbar(shell)
    )
    while True:
        step(session, shell)


def step(session, shell):
    try:
        cmd = session.prompt('$ ')
        try:
            run_command(cmd, shell)
        except ShellException as e:
            print(e)
    except KeyboardInterrupt:
        pass
    except EOFError:
        sys.exit(1)


def toolbar(shell: Shell, text='Run any command to show info'):
    method = shell.last_method()
    if method:
        text = generate_help(method)

    return Text(text)


def generate_help(func):
    synopsis = infer_synopsis(func)
    full_text = synopsis
    if func.__doc__:
        full_text += f'  |  {func.__doc__}'

    # keep the first few lines
    return '\n'.join(full_text.split('\n')[:3])


if __name__ == '__main__':
    main()
