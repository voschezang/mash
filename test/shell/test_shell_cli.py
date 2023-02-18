from argparse import ArgumentParser, RawTextHelpFormatter
from pytest import raises


from mash import io_util
from mash.io_util import check_output, read_file, run_subprocess
from mash.shell import ShellError
from mash.shell.shell import Shell, add_cli_args, run_command
from mash.util import identity


# Beware of the trailing space
run = 'python3 src/examples/shell_example.py '


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


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
    assert check_output(run + 'print 3') == '3'
    assert check_output(run + '"print 3"') == '3'
    assert check_output(run + '\"print 3\"') == '3'


def test_cli_unhappy():
    # with raises(RuntimeError):
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


def test_cli_pipe_interop():
    cmd = 'print abc | grep abc |> print'
    assert catch_output(cmd) == 'abc'
    assert check_output(f'{run} "{cmd}"') == 'abc'

    cmd = 'print abc | grep ab |> print | grep abc |> print def'
    assert catch_output(cmd) == 'def abc'
    assert check_output(f'{run} "{cmd}"') == 'def abc'

    shell = Shell()
    shell.add_functions({'custom_func': identity})
    cmd = 'print abc | grep abc | custom_func'
    with raises(ShellError):
        catch_output(cmd, strict=True)
