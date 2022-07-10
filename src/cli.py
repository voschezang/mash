#!/usr/bin/python3
from quo.history import MemoryHistory
from quo.prompt import Prompt

from dsl import Shell, run_command


def main():
    shell = Shell()

    for cmd in Shell.all_commands():
        MemoryHistory.append(cmd)

    session = Prompt(
        history=MemoryHistory,
        suggest="history",
        enable_history_search=True,
    )
    while True:
        step(session, shell)


def step(session, shell):
    try:
        cmd = session.prompt('$ ')
        print('cmd', cmd)
    except KeyboardInterrupt:
        pass

    run_command(cmd, shell)


if __name__ == '__main__':
    main()
