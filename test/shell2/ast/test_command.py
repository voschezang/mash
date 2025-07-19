
from pytest import raises
from mash.io_util import catch_output
from mash.shell.errors import ShellTypeError
from mash.shell2.ast.command import Command, infer_args, verify_function_args
from mash.shell2.ast.term import Term, Word


def test_command_init():
    cmd = Command(Word('yes'))
    assert cmd.f == 'yes'

    cmd = Command(Word('print'), Word('a'), Word('b'), Word('c'))
    assert cmd.f == 'print'
    assert cmd.args == ('a', 'b', 'c')

    assert str(cmd) == '[Command] print a b c'


def test_command_run():
    cmd = Command(Word('print'), Word('a'), Word('b'), Word('c'))
    cmd.run(None)


def test_command_run_no_term():
    cmd = Command(Word('print'), 1)
    # TODO
    # cmd.run(None)


def test_command_output():
    cmd = Command(Word('print'), Word('a'), Word('b'), Word('c'))
    result = catch_output(None, cmd.run)
    assert result == 'a b c'


def test_verify_function_args():
    verify_function_args(echo, [Term('abc')])

    # subclass
    verify_function_args(echo, [Word('abc')])

    # too few arguments
    with raises(ShellTypeError):
        verify_function_args(dummy, [])

    # too many arguments
    with raises(ShellTypeError):
        verify_function_args(dummy, [Word('abc'), Word('def')])

    # invalid type
    with raises(ShellTypeError):
        verify_function_args(dummy, ['abc'])


def test_verify_function_args_variadic():
    verify_function_args(dummy, [1, 0.1])

    # multiple variadic args
    verify_function_args(dummy, [1, 0.1, 0.2])

    # too few arguments
    with raises(ShellTypeError):
        verify_function_args(dummy, [])

    with raises(ShellTypeError):
        verify_function_args(dummy, [])

    # wrong type
    with raises(ShellTypeError):
        verify_function_args(dummy, ['1'])


def test_infer_args():
    pos_args, var_args = infer_args(dummy)

    assert pos_args == ['a']
    assert var_args == ['b']


def dummy(a: int, *b: float):
    return a + b[0]


def echo(a: Term):
    return a
