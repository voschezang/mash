from pytest import raises
from mash import io_util
from mash.shell.errors import ShellError
from mash.shell2.core import Core


def run_command(lines: str):
    Core().compile(lines)


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_shel():
    line = 'print hello'
    run_command(line)


def test_run_command():
    line = 'print hello'
    assert catch_output(line) == 'hello'

    with raises(ShellError):
        run_command('no-op')


def test_shell_cli():
    run = 'cd src; python3 -m mash.shell2.core'
    assert io_util.check_output(run) == 'ok'
