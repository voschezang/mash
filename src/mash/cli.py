#!/usr/bin/python3
import sys
from typing import Tuple
from quo.completion import NestedCompleter
from quo.history import MemoryHistory
from quo.prompt import Prompt
from quo.text import Text

from mash.shell.shell import Shell, all_commands, run_command, main as shell_main
from mash.shell.base import ShellError
from mash.doc_inference import infer_synopsis

rprompt_init = 'Type any command to continue'
rprompt_default = ''
rprompt_error = 'Type `help` or ? for help'


def main(**shell_kwds):
    shell = shell_main(repl=False, **shell_kwds)
    session, shell = setup(shell)
    run(session, shell)


def setup(shell: Shell) -> Tuple[Prompt, Shell]:
    shell.ignore_invalid_syntax = False

    # setup a completion-dropdown
    completer = NestedCompleter.add({k: None for k in all_commands(Shell)})

    # setup a history-completion
    for cmd in all_commands(Shell):
        MemoryHistory.append(cmd)

    session = Prompt(
        history=MemoryHistory,
        suggest="history",
        rprompt=Text(rprompt_init),
        enable_history_search=True,
        completer=completer,
        vi_mode=True,
        bottom_toolbar=lambda: toolbar(shell)
    )
    return session, shell


def run(session: Prompt, shell: Shell):
    print('Press ctrl-d to exit, ctrl-c to cancel and TAB for word completion')
    while True:
        step(session, shell)


def step(session, shell):
    try:
        cmd = session.prompt(shell.prompt)
        try:
            run_command(cmd, shell)
            session.rprompt = Text(rprompt_default)
        except ShellError as e:
            print(e)
            session.rprompt = Text(rprompt_error)
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
