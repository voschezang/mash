from argparse import ArgumentParser, RawTextHelpFormatter
from pytest import raises

import io_util
from io_util import ArgparseWrapper, check_output, run_subprocess
from shell import Function, Shell, ShellException, add_cli_args, run_command


run = 'python src/shell.py '


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


def test_run_command():
    Shell.ignore_invalid_syntax = False
    run_command('print a')

    with raises(ShellException):
        run_command('echoooo a')


def test_simple():
    Shell.ignore_invalid_syntax = True
    assert catch_output('print a') == 'a'
    assert 'Unknown syntax' in catch_output('aaaa a')

    Shell.ignore_invalid_syntax = False
    with raises(ShellException):
        catch_output('aaaa a')


def test_multi_commands():
    assert catch_output('print a; print b\n print c') == 'a\nb\nc'


def test_pipe():
    x = catch_output('print 100 |> print')
    assert catch_output('print 100 |> print') == '100'


def test_pipe_unix():
    assert catch_output('print 100 | less') == '100'


def test_pipe_input():
    assert catch_output('print abc | grep abc') == 'abc'

    with raises(ShellException):
        catch_output('echo abc | grep def')


def test_add_cli_args():
    parser = ArgumentParser(conflict_handler='resolve',
                            formatter_class=RawTextHelpFormatter)
    add_cli_args(parser)

    fn = 'myfile'
    parse_args = parser.parse_args(['-f', fn])
    assert parse_args.file == fn
    assert parse_args.safe == False

    cmds = 'echo 2'
    parse_args = parser.parse_args(cmds.split(' ') + ['-s'])
    assert parse_args.cmd == cmds.split(' ')
    assert parse_args.safe


def test_cli():
    # Note that this may be run with a different python version
    assert check_output(run + 'print 3') == '3'
    assert check_output(run + '"print 3"') == '3'


def test_cli_unhappy():
    with raises(RuntimeError):
        run_subprocess(run + '"printnumber 123"')


def test_cli_multi_commands():
    assert check_output(run +
                        '"print a; print b\n print c"') == 'a\nb\nc'


def test_cli_pipe_input():
    out = check_output(run + '"print abc | grep abc"')
    assert out == 'abc'

    with raises(RuntimeError):
        run_subprocess(run + '"print abc | grep def"')


def test_cli_pipe_interop():
    cmd = 'print abc | grep abc |> print'
    assert catch_output(cmd) == 'abc'
    assert check_output(f'{run} "{cmd}"') == 'abc'


def test_pipe_to_cli():
    check_output(f'echo 1 | {run} print')
    check_output(f'echo 1 | {run} !echo')

    out = check_output(f'echo abc | {run} print')
    assert 'abc' in out
    out = check_output(f'echo abc | {run} !echo')
    assert 'abc' in out


def test_cli_file():
    out = check_output(run + '-f test/echo_abc.sh')
    assert 'abc' in out

    # multiple files
    out = check_output(run + '-f test/echo_abc.sh')
    assert 'abc' in out

    # commands and files
    key = '238u3r'
    out = check_output(f'{run} echo {key} -f test/echo_abc.sh')

    assert 'abc' in out
    assert key in out

    # files and commands
    out = check_output(
        f'{run} -f test/echo_abc.sh echo {key} ')

    assert 'abc' in out
    assert key in out


def test_cli_pipe_file():
    out = check_output('cat test/echo_abc.sh | ' + run)
    assert 'abc' in out
