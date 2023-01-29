from pathlib import Path
from pytest import raises
from time import perf_counter

from mash import io_util
from mash.shell import delimiters, ShellError
from mash.shell.shell import Shell, run_command


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_run_command():
    run_command('print a')

    # with raises(ShellError):
    #     run_command('echoooo a', strict=True)


def test_onecmd_output():
    assert catch_output('print a') == 'a'
    assert catch_output('print a b c d e f') == 'a b c d e f'
    assert catch_output('print a ; print b') == 'a\nb'
    assert catch_output('aaaa a') == 'aaaa a'
    # assert 'Unknown syntax' in catch_output('aaaa a')

    # with raises(ShellError):
    #     run_command('aaaa a', strict=True)


def test_println():
    assert catch_output('print 1 2') == '1 2'
    assert catch_output('println 1 2') == '1\n2'


def test_onecmd_syntax():
    # ignore invalid syntax if strict mode is false
    run_command(r'print "\""', strict=True)
    run_command('aaaa a', strict=False)

    s = 'A string with ;'
    assert catch_output(f'print " {s} " ') == f'" {s} "'

    with raises(ShellError):
        run_command('print "\""', strict=True)


def test_onecmd_syntax_quotes():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    assert catch_output('a = 1', shell=shell) == ''

    # TODO quoting terms can shadow other terms
    # with raises(ShellError):
    assert catch_output('a = 1 "="', shell=shell) == ''


def test_onecmd_syntax_escape():
    if 0:
        assert catch_output('echo \\| echo') == '| echo'
        assert catch_output('echo \| echo') == '| echo'


def test_multi_commands():
    assert catch_output('print a ; print b\n print c') == 'a\nb\nc'


def test_pipe():
    assert catch_output('print 100 |> print 2') == '2 100'


def test_pipe_unix():
    # assert catch_output('print 100 | less') == '100'

    # with quotes
    assert catch_output('print "2; echo 12" | grep 2') == '2; echo 12'


def test_pipe_input():
    assert catch_output('print abc | grep abc') == 'abc'

    # fail in strict mode
    with raises(ShellError):
        catch_output('echo abc | grep def', strict=True)

    # fail silently without in strict mode
    assert catch_output('echo abc | grep def', strict=False) == ''


def test_pipe_to_file():
    text = 'abc'
    filename = '.pytest_tmp_out.txt'

    # clear file content
    f = Path(filename)
    f.unlink(True)

    result = catch_output(f'print {text} >- {filename}')
    assert result == ''

    # verify output file
    assert f.read_text().rstrip() == text

    f.unlink()


def test_pipe_to_file_with_interop():
    t = str(perf_counter())
    f = '.pytest_time'
    cmd = f'print {t} >- {f} ; cat {f}'

    assert catch_output(cmd).strip() == t, cmd

    Path(f).unlink()


def test_add_functions():
    Shell.ignore_invalid_syntax = True
    shell = Shell()

    key = 'test_add_functions'

    out = catch_output('id 10')
    assert 'Unknown syntax: id' in out

    shell.add_functions({'id': print}, group_key=key)
    run_command('id 10', shell=shell)
    out = catch_output('id 10')
    assert '10' in out

    # removing another key should have no impact
    shell.remove_functions('another key')
    out = catch_output('id 10')
    assert '10' in out

    shell.remove_functions(key)
    assert 'Unknown syntax: id' in out


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
    assert catch_output(f'math 1 + 10', shell=shell) == '11'
    assert catch_output(f'math 1 + 2 * 3', shell=shell) == '7'


def test_shell_do_math_compare():
    shell = Shell()
    assert catch_output(f'math 1 < 10', shell=shell) == '1'
    assert catch_output(f'math 1 > 10', shell=shell) == ''
    assert catch_output(f'math 1 > 10', shell=shell) == ''


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


def test_set_do_char_method():
    shell = Shell()
    op = '~'

    # invalid syntax
    with raises(ShellError):
        run_command(op, shell, strict=True)

    shell.set_do_char_method(print, [op])
    assert catch_output(op, shell=shell, strict=True) == op

    # verify that clashes are resolved
    for op in [delimiters.bash[0], delimiters.RIGHT_ASSIGNMENT]:
        assert catch_output(op, shell=shell, strict=True) == ''

        with raises(ShellError):
            shell.set_do_char_method(print, [op])


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
    # assert catch_output(line, shell=shell, strict=True) == 'a\nb'

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


def test_product_reduce():
    shell = Shell()
    run_command('mul (a b): math a * b', shell=shell)
    run_command('addOne (a): math 1 + a', shell=shell)
    run_command('product (x): echo x |> reduce mul 1', shell=shell)

    assert catch_output('mul 2 2', shell=shell, strict=True) == '4'
    line = 'range 3 >>= addOne |> product'
    assert catch_output(line, shell=shell, strict=True) == '6'


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
