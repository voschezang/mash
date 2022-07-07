from contextlib import redirect_stdout
from io import StringIO
from sys import stderr
from this import d
import pytest
import subprocess

from dsl import Function, run_command


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


def test_pipe():
    assert catch_output('echo 100 |> echo') == '100\n'


def test_pipe_unix():
    b = catch_output('echo 100 | less')
    assert catch_output('echo 100 | less') == '100\n'


def test_pipe_input():
    catch_output('echo abc | grep abc')

    with pytest.raises(RuntimeError):
        catch_output('echo abc | grep def')


def test_cli():
    check_output('./src/dsl.py echo 1')


def test_cli_pipe_input():
    out = check_output('./src/dsl.py "echo abc | grep abc"')
    assert out == 'abc'

    with pytest.raises(RuntimeError):
        run('./src/dsl.py "echo abc | grep def"')


def test_pipe_to_cli():
    check_output('echo 1 | ./src/dsl.py echo')
    check_output('echo 1 | ./src/dsl.py !echo')

    out = check_output('echo abc | ./src/dsl.py echo')
    assert 'abc' in out
    out = check_output('echo abc | ./src/dsl.py !echo')
    assert 'abc' in out


def test_cli_file():
    out = check_output('./src/dsl.py test/echo_abc.sh')
    assert 'abc' in out


def test_cli_pipe_file():
    out = check_output('cat test/echo_abc.sh | ./src/dsl.py')
    assert 'abc' in out


def catch_output(line='', func=run_command) -> str:
    out = StringIO()
    with redirect_stdout(out):
        func(line)
        result = out.getvalue()

    return result


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
