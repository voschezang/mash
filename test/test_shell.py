from pytest import raises

import io_util
from io_util import check_output, run_subprocess
from shell import Function, run_command


def catch_output(line='', func=run_command) -> str:
    return io_util.catch_output(line, func)


def test_Function_args():
    synopsis = 'list'
    func = Function(list, args=[], synopsis=synopsis, doc='')
    assert func.func == list
    assert func.help == synopsis


def test_Function_call():
    value = '1'

    f = Function(int, args=[], synopsis='')

    assert f(value) in [int(value), value + '\n']
    assert f() == 0


def test_multi_commands():
    assert catch_output('print a; print b\n print c') == 'a\nb\nc'


def test_pipe():
    x = catch_output('print 100 |> print')
    assert catch_output('print 100 |> print') == '100'


def test_pipe_unix():
    assert catch_output('print 100 | less') == '100'


def test_pipe_input():
    assert catch_output('print abc | grep abc') == 'abc'

    with raises(RuntimeError):
        catch_output('echo abc | grep def')


def test_cli():
    assert check_output('./src/shell.py print 3') == '3'
    assert check_output('./src/shell.py "print 3"') == '3'


def test_cli_unhappy():
    with raises(RuntimeError):
        run_subprocess('./src/shell.py "printnumber 123"')


def test_cli_multi_commands():
    assert check_output(
        './src/shell.py "print a; print b\n print c"') == 'a\nb\nc'


def test_cli_pipe_input():
    out = check_output('./src/shell.py "print abc | grep abc"')
    assert out == 'abc'

    with raises(RuntimeError):
        run_subprocess('./src/shell.py "print abc | grep def"')


def test_cli_pipe_interop():
    cmd = 'print abc | grep abc |> print'
    assert catch_output(cmd) == 'abc'
    assert check_output(f'./src/shell.py "{cmd}"') == 'abc'


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
