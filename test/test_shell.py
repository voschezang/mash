from contextlib import redirect_stdout
from io import StringIO
from sys import stderr
from this import d
import pytest
import subprocess

from shell import Function, run_command


def test_Function_args():
    synopsis = 'list'
    func = Function(list, args=[], synopsis=synopsis, doc='')
    assert func.func == list
    assert func.help == synopsis


def test_Function_call():
    value = '1'

    f = Function(int, args=[], synopsis='')

    assert f(value) in [int(value), value + '\n']
    assert f() is None


def test_multi_commands():
    assert catch_output('print a; print b\n print c') == 'a\nb\nc'


def test_pipe():
    assert catch_output('print 100 |> print') == '100'


def test_pipe_unix():
    assert catch_output('print 100 | less') == '100'


def test_pipe_input():
    catch_output('print abc | grep abc')

    with pytest.raises(RuntimeError):
        catch_output('echo abc | grep def')


def test_cli():
    check_output('./src/shell.py print 1')


def test_cli_multi_commands():
    assert check_output(
        './src/shell.py "print a; print b\n print c"') == 'a\nb\nc'


def test_cli_pipe_input():
    out = check_output('./src/shell.py "print abc | grep abc"')
    assert out == 'abc'

    with pytest.raises(RuntimeError):
        run('./src/shell.py "print abc | grep def"')


def test_pipe_to_cli():
    check_output('echo 1 | ./src/shell.py print')
    check_output('echo 1 | ./src/shell.py !echo')

    out = check_output('echo abc | ./src/shell.py print')
    assert 'abc' in out
    out = check_output('echo abc | ./src/shell.py !echo')
    assert 'abc' in out


def test_cli_file():
    out = check_output('./src/shell.py test/echo_abc.sh')
    assert 'abc' in out


def test_cli_pipe_file():
    out = check_output('cat test/echo_abc.sh | ./src/shell.py')
    assert 'abc' in out


def catch_output(line='', func=run_command) -> str:
    out = StringIO()
    with redirect_stdout(out):
        func(line)
        result = out.getvalue()

    return result.rstrip('\n')


def run(line: str) -> str:
    result = subprocess.run(line, capture_output=True, shell=True)
    if result.returncode != 0:
        raise RuntimeError(result)


def check_output(line: str) -> str:
    """Similar to subprocess.check_output, but with more detailed error messages 
    """
    result = subprocess.run(line, capture_output=True, shell=True)

    msg = result.stdout.decode(), result.stderr.decode()
    assert result.returncode == 0, msg

    return result.stdout.decode().rstrip('\n')
