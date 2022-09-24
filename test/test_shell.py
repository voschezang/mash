from argparse import ArgumentParser, RawTextHelpFormatter
from time import perf_counter
from pathlib import Path
from pytest import raises

import io_util
from io_util import check_output, read_file, run_subprocess
from shell import Shell, ShellException, add_cli_args, run_command

# TODO split up testcases for BaseShell and Shell

run = 'python src/shell.py '


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_run_command():
    run_command('print a')

    with raises(ShellException):
        run_command('echoooo a', strict=True)


def test_onecmd_output():
    assert catch_output('print a') == 'a'
    assert catch_output('print a ; print b') == 'a\nb'
    assert 'Unknown syntax' in catch_output('aaaa a')

    with raises(ShellException):
        run_command('aaaa a', strict=True)


def test_onecmd_syntax():
    # ignore invalid syntax in strict mode
    run_command('print "\""', strict=False)
    run_command('aaaa a', strict=False)

    s = 'A string with ;'
    assert catch_output(f'print " {s} " ') == s

    with raises(ShellException):
        run_command('print "\""', strict=True)


def test_multi_commands():
    assert catch_output('print a ; print b\n print c') == 'a\nb\nc'


def test_pipe():
    assert catch_output('print 100 |> print') == '100'


def test_pipe_unix():
    assert catch_output('print 100 | less') == '100'

    # with quotes
    assert catch_output('print "2; echo 12" | grep 2') == '2; echo 12'


def test_pipe_input():
    assert catch_output('print abc | grep abc') == 'abc'

    with raises(ShellException):
        catch_output('echo abc | grep def', strict=False)


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
    # Note that this may be run with a different python version,
    # based on the shebang (#!) in shell.py

    assert check_output(run + 'print 3') == '3'
    assert check_output(run + '"print 3"') == '3'
    assert check_output(run + '\"print 3\"') == '3'
    ## assert check_output(run + '"print ( \' ) "') == "( \' )"
    # assert check_output(run + 'print "|" ') == '|'
    # assert check_output(run + 'print "\n" ') == '|'


def test_cli_unhappy():
    with raises(RuntimeError):
        run_subprocess(run + '"printnumber 123"')

    # invalid quotes
    with raises(AssertionError):
        check_output(run + '"print \" "')


def test_cli_multi_commands():
    assert check_output(run + '"print a ; print b\n print c"') == 'a\nb\nc'


def test_cli_pipe_input():
    assert check_output(run + '"print abc | grep abc"') == 'abc'
    assert check_output(run + '"print abc |> print "') == 'abc'

    with raises(RuntimeError):
        run_subprocess(run + '"print abc | grep def"')


def test_subprocess_run():
    import subprocess
    cmd = 'echo abc | print'
    result = subprocess.run(
        args=cmd, capture_output=True, shell=True)
    print(result)
    assert result.returncode != 0
    assert result.returncode == 127


def test_cli_pipe_interop():
    # cmd = 'print abc | grep abc |> print'
    # assert catch_output(cmd) == 'abc'
    # assert check_output(f'{run} "{cmd}"') == 'abc'

    cmd = 'print abc | grep abc | print'
    with raises(ShellException):
        catch_output(cmd)

    cmd = 'print abc | grep ab |> print | grep abc |> print def'
    assert catch_output(cmd) == 'def abc'
    assert check_output(f'{run} "{cmd}"') == 'def abc'


def test_pipe_to_file():
    text = 'abc'
    filename = '.pytest_tmp_out.txt'

    # clear file content
    f = Path(filename)
    f.write_text('')

    result = catch_output(f'print {text} > {filename}')
    assert result == ''

    # verify output file
    assert f.read_text().rstrip() == text


def test_pipe_to_file_with_interop():
    t = str(perf_counter())
    f = '.pytest_time'
    cmd = f'print {t} > {f} ; cat {f}'

    assert catch_output(cmd).strip() == t, cmd


def test_pipe_to_cli():
    check_output(f'echo 1 | {run} print')
    check_output(f'echo 1 | {run} !echo')

    out = check_output(f'echo abc | {run} print')
    assert 'abc' in out
    out = check_output(f'echo abc | {run} !echo')
    assert 'abc' in out


def test_cli_file():
    # try execution without cli
    filename = 'test/echo_abc.sh'
    command = read_file(filename)
    run_command(command, strict=True)

    # execute using cli

    out = check_output(run + f'-f {filename}')
    assert 'abc' in out

    # commands and files
    key = '238u3r'
    out = check_output(f'{run} echo {key} -f {filename}')

    assert 'abc' in out
    assert key in out

    # files and commands
    out = check_output(
        f'{run} -f {filename} echo {key} ')

    assert 'abc' in out
    assert key in out


def test_cli_pipe_file():
    out = check_output('cat test/echo_abc.sh | ' + run)
    assert 'abc' in out


def test_add_functions():
    Shell.ignore_invalid_syntax = True
    shell = Shell()

    key = 'test_add_functions'

    out = catch_output('id 10')
    assert 'Unknown syntax: id' in out

    shell.add_functions({'id': print}, group_key=key)
    run_command('id 10')
    out = catch_output('id 10')
    assert '10' in out

    # removing another key should have no impact
    shell.remove_functions('another key')
    out = catch_output('id 10')
    assert '10' in out

    shell.remove_functions(key)
    assert 'Unknown syntax: id' in out
