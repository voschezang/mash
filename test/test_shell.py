from argparse import ArgumentParser, RawTextHelpFormatter
from multiprocessing.sharedctypes import Value
from pathlib import Path
from pytest import raises
from time import perf_counter

import io_util
from io_util import check_output, read_file, run_subprocess
from shell import Shell, add_cli_args, run_command
from shell_base import ShellError, bash_delimiters, py_delimiters
from util import identity


run = 'python src/shell.py '


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_run_command():
    run_command('print a')

    with raises(ShellError):
        run_command('echoooo a', strict=True)


def test_onecmd_output():
    assert catch_output('print a') == 'a'
    assert catch_output('print a ; print b') == 'a\nb'
    assert 'Unknown syntax' in catch_output('aaaa a')

    with raises(ShellError):
        run_command('aaaa a', strict=True)


def test_onecmd_syntax():
    # ignore invalid syntax in strict mode
    run_command('print "\""', strict=False)
    run_command('aaaa a', strict=False)

    s = 'A string with ;'
    assert catch_output(f'print " {s} " ') == s

    with raises(ShellError):
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

    with raises(ShellError):
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
        catch_output(cmd)


def test_pipe_to_file():
    text = 'abc'
    filename = '.pytest_tmp_out.txt'

    # clear file content
    f = Path(filename)
    f.unlink(True)

    result = catch_output(f'print {text} > {filename}')
    assert result == ''

    # verify output file
    assert f.read_text().rstrip() == text

    f.unlink()


def test_pipe_to_file_with_interop():
    t = str(perf_counter())
    f = '.pytest_time'
    cmd = f'print {t} > {f} ; cat {f}'

    assert catch_output(cmd).strip() == t, cmd

    Path(f).unlink()


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


def test_set_variable_infix():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    k = 'some_key'
    v = '| ; 1 2   '

    assert catch_output(f'{k} = "{v}"', shell=shell) == k
    assert k in shell.env
    assert shell.env[k] == v


def test_set_variable_infix_multiple_values():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    k = 'some_key'
    v = '1 2'

    assert catch_output(f'{k} = {v}', shell=shell) == k
    assert k in shell.env
    assert shell.env[k] == v

    assert catch_output(f'echo ${k}', shell=shell) == v


def test_set_variable_infix_eval():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    k = 'some_key'
    v = '! expr 2 + 2'

    assert catch_output(f'{k} <- {v}', shell=shell) == k
    assert k in shell.env
    assert shell.env[k] == '4'

    v = '! "x=$(( 2 + 2 )); echo $x"'
    assert catch_output(f'{k} <- {v}', shell=shell) == k
    assert k in shell.env
    assert shell.env[k] == '4'


def test_do_export():
    k = 'some_key'
    shell = Shell()
    shell.ignore_invalid_syntax = False

    v = '123'
    for cmd in [f'export {k} {v}',
                f'export {k} "{v}"']:

        run_command(cmd, shell)
        assert k in shell.env
        assert shell.env[k] == v

    v = '1 2'
    for cmd in [f'export {k} {v}',
                f'export {k} "{v}"']:
        run_command(f'export {k} "1 2"', shell)
        assert shell.env[k] == v

    v = '| ; 2'
    run_command(f'export {k} "{v}"', shell)
    assert shell.env[k] == v


def test_do_export_unset():
    shell = Shell()

    # unset var when no values are given
    shell.env['k'] = '1'
    run_command('export k', shell)
    assert 'k' not in shell.env


def test_do_export_after_pipe():
    shell = Shell()

    v = 'abc'
    # run_command(f'print {v} |> export k', shell)
    # assert shell.env['k'] == v

    v = 'def'
    run_command(f'! echo {v} |> export k', shell)
    assert shell.env['k'] == v


def test_variable_expansion():
    shell = Shell()
    assert catch_output('a = 2', shell=shell) == 'a'
    assert shell.env['a'] == '2'

    assert catch_output('print $a', shell=shell) == '2'


def test_variable_expansion_regex():
    shell = Shell()
    shell.completenames_options = ['abc', 'prefix123']

    all = ' '.join(shell.completenames_options)
    assert catch_output('echo *', shell=shell) == all

    assert catch_output('echo ab?', shell=shell) == 'abc'
    assert catch_output('echo ???b', shell=shell) == '???b'
    assert catch_output('echo a*', shell=shell) == 'abc'
    assert catch_output('echo [a-z]*123', shell=shell) == 'prefix123'


def test_set_do_char_method():
    shell = Shell()
    op = '~'

    # invalid syntax
    with raises(ShellError):
        run_command(op, shell, strict=True)

    shell.set_do_char_method(print, op)
    assert catch_output(op, shell=shell, strict=True) == op

    # verify that clashes are resolved
    for op in [bash_delimiters[0], py_delimiters[0]]:
        assert catch_output(op, shell=shell, strict=True) == ''

        shell.set_do_char_method(print, op)
        assert catch_output(op, shell=shell, strict=True).strip() == op


def test_save_and_load_session():
    filename = '.pytest_session_file.json'
    Path(filename).unlink(True)

    k = 'key'
    v = 22

    shell = Shell()
    assert k not in shell.env

    shell.set_env_variable(k, str(v))
    shell.save_session(filename)

    shell = Shell()
    assert k not in shell.env

    shell.load_session(filename)
    assert k in shell.env
    assert shell.env[k] == str(v)

    Path(filename).unlink(True)
