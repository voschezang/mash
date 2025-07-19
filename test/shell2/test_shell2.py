from mash import io_util
from mash.shell2.core import Core


def run_command(lines: str):
    Core().compile(lines)


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_shel():
    lines = 'abc'
    Core().compile(lines)


def test_run_command():
    lines = 'abc'

    run_command(lines)

    assert catch_output(lines) == ''


def test_shell_cli():
    run = 'cd src; python3 -m mash.functional_shell.core'
    assert io_util.check_output(run) == ''
