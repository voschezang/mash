from argparse import ArgumentParser, RawTextHelpFormatter
from pathlib import Path
from pytest import raises
from time import perf_counter


from mash import io_util
from mash.io_util import check_output, read_file, run_subprocess
from mash.shell import delimiters
from mash.shell import ShellError
from mash.shell.shell import Shell, add_cli_args, run_command
from mash.util import identity


# Beware of the trailing space
run = 'python src/examples/shell_example.py '


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


def test_println():
    assert catch_output('print 1 2') == '1 2'
    assert catch_output('println 1 2') == '1\n2'


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

    # fail in strict mode
    with raises(ShellError):
        catch_output('echo abc | grep def', strict=True)

    # fail silently without in strict mode
    assert catch_output('echo abc | grep def', strict=False) == ''


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
        catch_output(cmd, strict=True)


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
    v = '| ; 1 2  = '

    run_command(f'{k} = "{v}"', shell=shell)
    assert k in shell.env
    assert shell.env[k] == v


def test_set_variable_infix_multiple_values():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    k = 'some_key'
    v = '1 2'

    run_command(f'{k} = {v}', shell=shell)
    assert k in shell.env
    assert shell.env[k] == v

    assert catch_output(f'echo ${k}', shell=shell) == v


def test_set_variable_infix_eval():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    k = 'some_key'
    v = '! expr 1 + 2'

    run_command(f'{k} <- {v}', shell=shell)
    assert k in shell.env
    assert shell.env[k] == '3'

    # variables in `${ }` notations should not be expanded
    v = '! "x=$(( 2 + 2 )); echo ${x}"'
    run_command(f'{k} <- {v}', shell=shell)
    assert shell.env[k] == '4'

    # without `${ }` notation
    # $x should be set to a constant value at compile time
    # the result of the previous expression should be ignored
    v = '! "x=$(( 2 + 3 )); echo $x"'

    # x is not defined at "compile" time
    with raises(ShellError):
        run_command(f'{k} <- {v}', shell=shell)

    # set x to a dummy value
    run_command(f'x = a constant', shell=shell)
    assert shell.env['x'] == 'a constant'

    run_command(f'{k} <- {v}', shell=shell)
    assert shell.env[k] == 'a constant'


def test_assign_variable():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('x <- echo 1', shell=shell)
    assert 'x' in shell.env
    assert shell.env['x'] == '1'

    run_command('assign x y z', shell=shell)
    assert shell.env['x'] == ''
    # TODO
    # assert 'y' in shell.env

    with raises(ShellError):
        run_command('x <- assign y', shell=shell)

    # veriy that assignment can be done after errors
    run_command('x <- echo 2', shell=shell)

    assert 'x' in shell.env
    assert shell.env['x'] == '2'


def test_assign_variable_left_hand():
    shell = Shell()
    run_command('echo abc -> x', shell=shell)
    assert 'x' in shell.env
    assert shell.env['x'] == 'abc'


def test_assign_multicommand():
    shell = Shell()
    # assert catch_output('assign x |> print 20 ', shell=shell) == ''
    # assert shell.env['x'] == '20'

    assert catch_output('y <- echo 20 |> echo ; print 30',
                        shell=shell) == '\n30'
    assert shell.env['y'] == '20'


def test_assign_multiple():
    shell = Shell()
    run_command('x = 1 ; y = 2', shell=shell)
    assert shell.env['x'] == '1'
    assert shell.env['y'] == '2'


def test_assign_eval_multiple():
    shell = Shell()
    run_command('echo 1 ; x <- echo 2 ; y <- echo 3', shell=shell)
    assert 'x' in shell.env
    assert shell.env['x'] == '2'

    run_command('y <- echo 1 ; z <- echo 2', shell=shell)
    assert shell.env['y'] == '1'
    assert shell.env['z'] == '2'


def test_set_variable_infix_eval_with_pipes():
    shell = Shell()
    assert catch_output('x <- print a |> print b', shell=shell) == 'b'
    assert shell.env['x'] == 'a'


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
    run_command('a = 2', shell=shell)
    assert shell.env['a'] == '2'

    assert catch_output('print $a', shell=shell) == '2'
    assert catch_output('print $a$a $a', shell=shell) == '22 2'


def test_variable_expansion_regex():
    shell = Shell()
    shell.completenames_options = ['abc', 'prefix123']

    all = ' '.join(shell.completenames_options)
    assert catch_output('echo *', shell=shell) == all

    assert catch_output('echo ab?', shell=shell) == 'abc'
    assert catch_output('echo ???b', shell=shell) == '???b'
    assert catch_output('echo a*', shell=shell) == 'abc'
    assert catch_output('echo [a-z]*123', shell=shell) == 'prefix123'


def test_variable_expansion_range():
    shell = Shell()
    # assert catch_output('echo {1..3}', shell=shell) == '1 2 3'
    run_command('x = 3', shell=shell)
    assert catch_output('print "{1..$x}"', shell=shell) == '1 2 3'

    # TODO this should result in `{1..3`
    assert catch_output("echo '{1..3}'", shell=shell) == '1 2 3'
    # TODO this should result in `{1..3`
    assert catch_output('echo \{1..3\}', shell=shell) == '1 2 3'


def test_variable_assignment_with_pipes():
    shell = Shell()
    run_command('a = 2', shell=shell)
    assert shell.env['a'] == '2'


def test_shell_do_math():
    shell = Shell()
    catch_output(f'math 1 + 10', shell=shell) == '11'
    catch_output(f'math 1 + 2 * 3', shell=shell) == '7'


def test_shell_range():
    shell = Shell()
    assert catch_output('range 1 3', shell=shell) == '1\n2'
    assert catch_output('range 2', shell=shell) == '0\n1'
    assert catch_output('range 3 1 -1', shell=shell) == '3\n2'


def test_shell_numbers():
    shell = Shell()
    run_command(f'x <- int 10', shell=shell)
    assert 'x' in shell.env

    run_command(f'y <- float 1.5', shell=shell)
    assert 'y' in shell.env

    run_command(f'z <- math x + y', shell=shell)
    assert 'z' in shell.env

    assert catch_output('math x + 10', shell=shell) == '20'
    assert catch_output('math x + y', shell=shell) == '11.5'
    assert catch_output('math x + z', shell=shell) == '21.5'

    # catch NameError
    with raises(ShellError):
        run_command(f'math x + +', shell=shell)

    # catch SyntaxError
    with raises(ShellError):
        run_command(f'math abc', shell=shell)


def test_shell_inline_function_simple():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    # identity
    run_command('f (x): x', shell=shell)
    assert catch_output('f 100', shell=shell) == '100'

    # too many arguments
    with raises(ShellError):
        run_command('f 1 2 3', shell=shell)

    # too few arguments
    with raises(ShellError):
        run_command('f', shell=shell)

    # invalid syntax
    with raises(ShellError):
        run_command('g "(x):" x', shell=shell)


def test_shell_inline_function_constant():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('f () : 10', shell=shell)
    assert catch_output('f', shell=shell) == '10'

    # echo
    run_command('f (x): print x', shell=shell)
    assert catch_output('f 100', shell=shell) == '100'


def test_shell_inline_function():
    shell = Shell()

    # repeat input
    run_command('g (x): x x', shell=shell)
    assert catch_output('g 2', shell=shell) == '2 2'

    # math expressions
    run_command('add (x y): math x + y', shell=shell)
    assert catch_output('add 1 2', shell=shell) == '3'

    # faulty math expressions
    run_command('add (x y): x + y', shell=shell)
    assert catch_output('add 1 2', shell=shell) == '1 + 2'


def test_shell_inline_function_with_pipe():
    shell = Shell()

    run_command('f (x): print x |> print', shell=shell)
    assert catch_output('f 100', shell=shell) == '100'

    run_command('f (x): math 1 + 2 |> echo result is', shell=shell)
    assert catch_output('f 100', shell=shell) == 'result is 3'

    run_command('f (x): math 1 + 2 |> echo result "=" ', shell=shell)
    assert catch_output('f 100', shell=shell) == 'result "=" 3'


def test_shell_inline_function_with_macros():
    shell = Shell()

    run_command('a = 10', shell=shell)
    run_command('f (b): $a b', shell=shell)
    assert catch_output('f 2', shell=shell) == '10 2'


def test_shell_inline_function_with_map():
    shell = Shell()
    # TODO implement pipe support for inline functions
    line = 'f (n) : range n >>= echo $'
    x = catch_output(line, shell=shell, strict=True)
    line = 'f 3'
    y = catch_output(line, shell=shell, strict=True)
    assert catch_output(line, shell=shell, strict=True)


def test_set_do_char_method():
    shell = Shell()
    op = '~'

    # invalid syntax
    with raises(ShellError):
        run_command(op, shell, strict=True)

    shell.set_do_char_method(print, op)
    assert catch_output(op, shell=shell, strict=True) == op

    # verify that clashes are resolved
    for op in [delimiters.bash[0], delimiters.python[0]]:
        assert catch_output(op, shell=shell, strict=True) == ''

        with raises(ShellError):
            shell.set_do_char_method(print, op)


def test_set_do_foldr():
    shell = Shell()
    run_command('add (a b): math a + b', shell=shell)

    line = 'range 4 |> foldr add 0'
    assert catch_output(line, shell=shell, strict=True) == '6'

    line = 'range 4 |> foldr add 0 $'
    assert catch_output(line, shell=shell, strict=True) == '6'


def test_set_do_flatten():
    shell = Shell()
    line = 'echo a b |> flatten'
    assert catch_output(line, shell=shell) == 'a\nb'

    run_command('x <- flatten a b c', shell=shell)
    line = 'echo $x $x'
    assert catch_output(line, shell=shell) == 'a\nb\nc a\nb\nc'

    line = 'echo $x $x |> flatten'
    assert catch_output(line, shell=shell) == 'a\nb\nc\na\nb\nc'


def test_set_do_map():
    shell = Shell()
    line = 'echo a b |> flatten |> map echo'
    assert catch_output(line, shell=shell, strict=True) == 'a\nb'

    line = 'echo a b |> flatten |> map echo [ $ ]'
    assert catch_output(line, shell=shell, strict=True) == '[ a ]\n[ b ]'

    line = 'range 3 |> map echo $'
    assert catch_output(line, shell=shell, strict=True) == '0\n1\n2'


def test_set_do_pipe_map():
    shell = Shell()
    line = 'echo a b |> flatten >>= echo'
    assert catch_output(line, shell=shell, strict=True) == 'a\nb'

    line = 'echo a b |> flatten >>= echo [ $ ]'
    assert catch_output(line, shell=shell, strict=True) == '[ a ]\n[ b ]'


def test_set_do_foreach():
    shell = Shell()
    line = 'echo a b |> foreach echo'
    assert catch_output(line, shell=shell, strict=True) == 'a\nb'

    line = 'echo 1 2 |> foreach echo 0'
    assert catch_output(line, shell=shell, strict=True) == '0\n1\n2'


def test_set_map_reduce():
    shell = Shell()
    run_command('sum (a b): math a + b', shell=shell)

    line = 'range 4 >>= math 2 * $ |> reduce sum 0 $'
    assert catch_output(line, shell=shell, strict=True) == '12'


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
