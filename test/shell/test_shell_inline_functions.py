from pytest import raises

from mash import io_util
from mash.shell import ShellError
from mash.shell.shell import Shell, run_command


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_inline_function_simple():
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


def test_inline_function_constant():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('f () : 10', shell=shell)
    assert catch_output('f', shell=shell) == '10'

    # echo
    run_command('f (x): print x', shell=shell)
    assert catch_output('f 100', shell=shell) == '100'


def test_inline_function_with_variable():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('a = 1', shell=shell)
    run_command('f (b) : $a', shell=shell)
    assert catch_output('f 2', shell=shell) == '1'


def test_inline_function_with_args():
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


def test_inline_function_with_pipe():
    shell = Shell()

    run_command('f (x): print $x |> print', shell=shell)
    assert catch_output('f 100', shell=shell) == '100'

    run_command('f (x): math 1 + 2 |> echo result is', shell=shell)
    assert catch_output('f 100', shell=shell) == 'result is 3'

    run_command('f (x): math 1 + 2 |> echo result "=" ', shell=shell)
    assert catch_output('f 100', shell=shell) == 'result = 3'


def test_inline_function_with_macros():
    shell = Shell()

    run_command('a = 10', shell=shell)
    run_command('f (b): $a b', shell=shell)
    assert catch_output('f 2', shell=shell) == '10 2'


def test_inline_function_with_map():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    line = 'f (n) : range $n >>= echo - $ -'
    run_command(line, shell=shell)
    line = 'f 3'
    assert catch_output('f 3', shell=shell) == '- 0 -\n- 1 -\n- 2 -'
