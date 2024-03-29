from mash.shell.shell import Shell
from mash.shell.cmd2 import run_command
from mash.util import use_recursion_limit

from test_shell import catch_output



def test_multiline_function():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
f (x):
    # example comment
    y = 10 # an inline comment
    return 1 |> math 1 +
    """
    run_command(cmd, shell=shell)

    assert catch_output('f 1', shell=shell) == '2'
    assert catch_output(cmd + '\nprint 10', shell=shell) == '10'


def test_multiline_function_missing_return():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
f (x):
    print 10

print 20
    """
    # continue to extend the function definition
    assert catch_output(cmd, shell=shell) == '20'
    assert catch_output('f 1', shell=shell) == ''

    # return with too large indent should be skipped
    assert catch_output('        return 1', shell=shell) == ''
    assert catch_output('f 1', shell=shell) == ''

    # return with too small indent should fail
    # with raises(ShellError):
    assert catch_output('return 2', shell=shell) == ''

    assert catch_output('    return 3', shell=shell) == ''

    with use_recursion_limit(100):
        #     with raises(RecursionError):
        run_command('f 40', shell=shell)


def test_multiline_function_with_assignments():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
f (x):
    y = 20
    # TODO print 'echo'
    # z <- echo 2 |> math 1 +
    z <- math 1 + 2 
    return $x $y $z # done
    """
    run_command(cmd, shell=shell)

    assert catch_output('f 10', shell=shell) == '10 20 3'
    assert catch_output('z <- f 10', shell=shell) == ''
    assert 'z' in shell.env
    assert shell.env['z'] == '10 20 3'


def test_multiline_function_with_branches():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
f (x):
    a <- math x < 0
    b <- math x > 0
    return "[$a]" "[$b]"
    """
    run_command(cmd, shell=shell)

    assert catch_output('f 1', shell=shell) == "[] [1]"


def test_multiline_function_with_maps():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
f (x):
    y <- math 1 + $x
    return $y
    """
    run_command(cmd, shell=shell)

    assert catch_output('f 1', shell=shell) == '2'

    assert catch_output('range 2 |> map f', shell=shell) == '1\n2'

    run_command(f'x <- range 2 |> map f |> map f', shell=shell)
    assert shell.env['x'] == '2\n3'


def test_multiline_function_nested():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
g (x):
    return $x $x

f (x):
    y <- g $x
    return $y $y
    """
    run_command(cmd, shell=shell)

    assert catch_output(f'g 1', shell=shell) == '1 1'
    assert catch_output(f'f 1', shell=shell) == '1 1 1 1'


def test_multiline_function_recursion():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
f (x):
    y <- math $x - 1

    if $y > 0 then
        return f $y
    if $y < 0 then
        return -10
    if $y == 0 then
        return -20
    """
    run_command(cmd, shell=shell)

    assert catch_output('f -1', shell=shell) == '-10'
    assert catch_output('f 1', shell=shell) == '-20'
    assert catch_output('f 2', shell=shell) == '-20'
    assert catch_output('f 3', shell=shell) == '-20'


def test_multiline_function_early_return():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    cmd = """
f (x):
    if $x == 1 then return 10
    if $x == 2 then
        return 20

    return 30
    """

    run_command(cmd, shell=shell)
    assert catch_output('f 1', shell=shell) == '10'
    assert catch_output(f'f 2', shell=shell) == '20'
    assert catch_output(f'f 3', shell=shell) == '30'
