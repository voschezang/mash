from pathlib import Path
from pytest import raises

from mash import io_util
from mash.shell.grammer import literals
from mash.shell.errors import ShellError, ShellSyntaxError
from mash.shell.shell import Shell, run_command


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_run_command():
    run_command('print a')
    run_command('? echo')

    # with raises(ShellError):
    #     run_command('echoooo a', strict=True)


def test_onecmd_output():
    assert catch_output('print a') == 'a'
    assert catch_output('print a b c d e f') == 'a b c d e f'
    assert catch_output('print a ; print b') == 'a\nb'
    assert catch_output('aaaa a') == 'aaaa a'

    # assert 'Unknown syntax' in catch_output('aaaa a')

    # with raises(ShellError):
    run_command('aaaa a', strict=True)


def test_onecmd_help():
    helper = 'Documented commands (type help <topic>):\n=========='
    assert helper in catch_output('?')
    assert helper in catch_output('help')

    echo = "Mimic Bash's print function."
    assert echo in catch_output('? echo')

    error = '*** No help on abc123'
    assert catch_output('? abc123') == error


def test_onecmd_numbers():
    assert catch_output('123', strict=True) == '123'


def test_println():
    assert catch_output('print 1 2') == '1 2'
    assert catch_output('println 1 2') == '1\n2'


def test_onecmd_syntax():
    # ignore invalid syntax if strict mode is false
    run_command(r'print "\""', strict=True)
    run_command('aaaa a', strict=False)

    s = 'A string with ;'
    assert catch_output(f'print " {s} " ') == f"' {s} '"

    with raises(ShellSyntaxError):
        run_command('print "\""', strict=True)


def test_onecmd_syntax_quotes():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    assert catch_output('a = 1', shell=shell) == ''

    # TODO quoting terms can shadow other terms
    # with raises(ShellError):
    assert catch_output('a = 1 "="', shell=shell) == ''


def test_set_do_env():
    shell = Shell()
    # TODO this fails
    assert catch_output('env', shell=shell) == ''


def test_onecmd_syntax_escape():
    if 0:
        assert catch_output(r'echo \\| echo') == '| echo'
        assert catch_output(r'echo \| echo') == '| echo'


def test_multi_commands():
    assert catch_output('print a ; print b\n print c') == 'a\nb\nc'


def test_add_functions():
    Shell.ignore_invalid_syntax = True
    shell = Shell()

    key = 'test_add_functions'

    out = catch_output('id 10', shell=shell)
    assert out == 'id 10'

    # with raises(ShellError):
    out = catch_output('id 10', shell=shell, strict=True)
    assert out == 'id 10'

    shell.add_functions({'id': print}, group_key=key)
    out = catch_output('id 10', shell=shell)
    assert out == '10'

    # removing another key should have no impact
    shell.remove_functions('another key')
    out = catch_output('id 10', shell=shell)
    assert '10' in out

    shell.remove_functions(key)
    # with raises(ShellError):
    out = catch_output('id 10', shell=shell, strict=True)
    assert out == 'id 10'


def test_shell_define_function_inline():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('flip (a b): $b $a', shell=shell)
    assert catch_output('flip 1 2', shell=shell) == '2 1'


def test_shell_define_function_multiline():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('flip (a b):', shell=shell)
    run_command('  return $b $a', shell=shell)
    assert catch_output('flip 1 2', shell=shell) == '2 1'
    run_command('env', shell=shell)

    # fail if the indent is omitted
    run_command('flip (a b):', shell=shell)
    with raises(ShellError):
        run_command('return $b $a', shell=shell)


def test_do_fail():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    # TODO verify that count is reset after errrors
    line = 'range 1 3 >>= fail'

    with raises(ShellError):
        run_command('fail 1', shell=shell)

    with raises(ShellError):
        run_command(line, shell=shell)
    # TODO support nested loops
    # line = 'range 3 >>= fac 1 + '


def test_shell_do_math():
    shell = Shell()
    assert catch_output('math 1 + 10', shell=shell) == '11'
    assert catch_output('math 1 + 2 * 3', shell=shell) == '7'


def test_shell_do_math_compare():
    shell = Shell()
    assert catch_output('math 1 == 10', shell=shell) == ''
    assert catch_output('math 1 < 10', shell=shell) == '1'
    assert catch_output('math 1 > 10', shell=shell) == ''
    assert catch_output('math 1 > 10', shell=shell) == ''


def test_shell_range():
    shell = Shell()
    assert catch_output('range 1 3', shell=shell) == '1\n2'
    assert catch_output('range 2', shell=shell) == '0\n1'
    assert catch_output('range 3 1 -1', shell=shell) == '3\n2'


def test_shell_numbers():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    run_command('x <- int 10', shell=shell)
    assert 'x' in shell.env
    assert shell.env['x'] == 10

    run_command('y <- float 1.5', shell=shell)
    assert 'y' in shell.env

    run_command('z <- math x + y', shell=shell)
    assert 'z' in shell.env

    assert catch_output('math x + 10', shell=shell) == '20'
    assert catch_output('math x + y', shell=shell) == '11.5'
    assert catch_output('math x + z', shell=shell) == '21.5'

    # catch NameError
    with raises(ShellError):
        run_command('math x + +', shell=shell)

    # catch SyntaxError
    with raises(ShellError):
        run_command('math abc', shell=shell)


def test_set_do_char_method():
    shell = Shell()
    op = '~>'

    # invalid syntax
    # with raises(ShellError):
    run_command(op, shell, strict=True)
    shell.add_special_function(op, print)

    assert catch_output(op, shell=shell, strict=True) == ''
    assert catch_output(f'{op} a', shell=shell, strict=True) == 'a'

    # verify that clashes are resolved
    for op in [literals.bash[0], '->']:
        with raises(ShellError):
            assert catch_output(op, shell=shell, strict=True) == ''

        with raises(ShellError):
            shell.add_special_function(op, print)


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
    assert shell.env['x'] == 'a\nb\nc'
    line = 'echo $x $x'
    assert catch_output(line, shell=shell) == 'a\nb\nc a\nb\nc'

    line = 'echo $x $x |> flatten'
    assert catch_output(line, shell=shell) == 'a\nb\nc\na\nb\nc'


def test_set_do_map():
    shell = Shell()
    line = 'echo a b |> flatten >>= echo'
    assert catch_output(line, shell=shell, strict=True) == 'a\nb'

    line = 'echo a b |> flatten |> map echo'
    assert catch_output(line, shell=shell, strict=True) == 'a\nb'

    line = 'echo a b |> flatten |> map echo p $ q'
    # assert catch_output(line, shell=shell, strict=True) == "'p a q'\n'p b q'"
    assert catch_output(line, shell=shell, strict=True) == "p a q\np b q"

    line = 'range 3 |> map echo $'
    assert catch_output(line, shell=shell, strict=True) == '0\n1\n2'


def test_map_raw_string():
    assert catch_output('echo "a@b" >>= echo') == 'a@b'

    result = """0 a@b
1 a@b"""
    assert catch_output('range 2 >>= echo $ "a@b" >>= echo') == result

    line = 'echo "a," >>= echo'
    assert catch_output(line, strict=True) == 'a,'


def test_set_do_pipe_map():
    shell = Shell()
    line = 'echo a b |> flatten >>= echo'

    assert catch_output(line, shell=shell, strict=True) == 'a\nb'

    line = 'echo a b |> flatten >>= echo p $ q'
    assert catch_output(line, shell=shell, strict=True) == "p a q\np b q"


def test_set_map_reduce():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    # note the absent $-signs in the args of `math`
    run_command('sum (a b): math a + b', shell=shell)
    assert catch_output('sum 1 1', shell=shell) == '2'

    line = 'range 4 >>= math 2 * $ |> reduce sum 0 $'
    assert catch_output(line, shell=shell) == '12'


def test_product_reduce():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    run_command('mul (a b): math a * b', shell=shell)
    run_command('addOne (a): math 1 + a', shell=shell)
    run_command('product (x): echo $x |> reduce mul 1', shell=shell)

    assert catch_output('mul 2 2', shell=shell) == '4'
    line = 'range 3 >>= addOne |> product'
    assert catch_output(line, shell=shell) == '6'


def test_save_and_load_session():
    filename = '.pytest_session_file.json'
    Path(filename).unlink(True)

    k = 'key'
    v = 22

    shell = Shell()
    assert k not in shell.env

    shell.env[k] = str(v)
    shell.save_session(filename)

    shell = Shell()
    assert k not in shell.env

    shell.load_session(filename)
    assert k in shell.env
    assert shell.env[k] == str(v)

    Path(filename).unlink(True)


def test_shell_scope():
    if 0:
        with raises(NotImplementedError):
            run_command('( 1 )')


def test_set_definition():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('a <- range 3', shell=shell)
    run_command('b <- range 3', shell=shell)
    run_command('c <- { $a }', shell=shell)
    assert shell.env['c'] == [{'a': '0'}, {'a': '1'}, {'a': '2'}]

    # TODO
    # run_command('c <- { a b }', shell=shell)
    # run_command('c <- { a b | a == b }', shell=shell)


def test_set_notation():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('x <- range 5', shell=shell)
    run_command('y <- { $x }', shell=shell)
    assert len(shell.env['y']) == 5
    assert shell.env['y'][0] == {'x': '0'}
    assert shell.env['y'][4] == {'x': '4'}


def test_set_with_condition():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('x <- range 5', shell=shell)
    run_command('y <- { $x | x > 2 }', shell=shell)
    assert len(shell.env['y']) == 2
    assert shell.env['y'][0] == {'x': '3'}

    run_command('z <- { $x | 2 < x }', shell=shell)
    assert len(shell.env['y']) == 2
    assert shell.env['z'][0] == {'x': '3'}

    result = catch_output('{ $x | x > 2 } >>= echo $.x', shell=shell)
    assert result.splitlines() == ['3', '4']

def test_set_multivariate():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('x <- range 3', shell=shell)
    run_command('y <- range 10 13', shell=shell)
    run_command('z <- { $x $y }', shell=shell)
    assert len(shell.env['z']) == 9
    assert shell.env['z'][0] == {'x': '0', 'y': '10'}

    result = catch_output('{ $x $y } >>= echo $.y', shell=shell)
    assert result.splitlines()[0] == '10'
    assert result.splitlines()[2] == '12'

    run_command('z <- { $x $y | x < 2 }', shell=shell)
    assert len(shell.env['z']) == 6
    assert shell.env['z'][0] == {'x': '0', 'y': '10'}
    assert shell.env['z'][4] == {'x': '1', 'y': '11'}