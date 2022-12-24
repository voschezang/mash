from pytest import raises

from mash import io_util
from mash.shell import ShellError
from mash.shell.shell import Shell, run_command


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


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
    assert catch_output('assign x |> print 20 ', shell=shell) == ''
    assert shell.env['x'] == '20'

    assert catch_output('y <- echo 20 |> echo 1 ; print 30',
                        shell=shell) == '1\n30'

    # TODO this should be '1 20'
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

    run_command('export k', shell)
    assert 'k' in shell.env
    assert shell.env['k'] == ''


def test_do_unset():
    shell = Shell()

    shell.env['k'] = '1'
    run_command('unset k', shell)
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

    run_command('run = print', shell=shell)
    assert catch_output('$run 4', shell=shell) == '4'


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
