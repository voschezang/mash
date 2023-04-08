from pytest import raises


from mash import io_util
from mash.shell import ShellError
from mash.shell.shell import Shell, run_command, run_commands_from_file


# Beware of the trailing space
run = 'python src/examples/shell_example.py '


def init() -> Shell:
    shell = Shell()
    shell.ignore_invalid_syntax = False
    run_commands_from_file('src/lib/math.sh', shell)
    return shell


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_math_lib_constants():
    shell = init()
    catch_output('echo pi', shell=shell) == 3.141592653589793


def test_math_lib_abs():
    shell = init()

    catch_output('abs 1.1', shell=shell) == '1.1'
    catch_output('abs -1.1', shell=shell) == '1.1'


def test_math_lib_factorial():
    shell = init()

    # catch_output('fac 3', shell=shell) == '6'
    # catch_output('fac 1', shell=shell) == '1'
    catch_output('fac 0', shell=shell) == '1'

    with raises(ShellError):
        # TODO implement this edge case
        run_command('fac -1', shell=shell)


def test_math_lib_binary_operators():
    shell = init()

    catch_output('add 1 1', shell=shell) == '2'
    catch_output('sub 2 1', shell=shell) == '1'
    catch_output('mul 2 2', shell=shell) == '4'

    run_command('x <- mul 2 2', shell=shell)
    assert 'x' in shell.env
    assert shell.env['x'] == '4'


def test_math_lib_reduction_sum():
    shell = init()

    catch_output('echo 1 2 3 |> flatten |> sum', shell=shell) == '6'
    catch_output('range 4 |> sum', shell=shell) == '6'

    run_command('x <- range 4 |> sum', shell=shell)
    assert shell.env['x'] == '6'


def test_math_lib_reduction_product():
    shell = init()

    catch_output('echo 2 4 |> flatten |> product', shell=shell) == '8'
    catch_output('range 3 |> product', shell=shell) == '2'
