
from pytest import raises
from mash.filesystem.filesystem import FileSystem
from mash.filesystem.scope import Scope
from mash.io_util import catch_output
from mash.shell.errors import ShellError, ShellTypeError
from mash.shell2.ast.command import Command, verify_arg_count, verify_arg_types, verify_function_args
from mash.shell2.ast.term import Float, Integer, Term, Word
from mash.shell2.ast.variable import Variable
from mash.util import infer_variadic_args


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

    cmd = Command(Word('print'), Word('a'), Integer(1), Float(.1))
    cmd.run(None)


def test_command_output():
    cmd = Command(Word('print'), Word('a'), Word('b'), Word('c'))
    result = catch_output(None, cmd.run)
    assert result == 'a b c'

    cmd = Command(Word('print'), Word('a'), Integer(1), Float(.1))
    result = catch_output(None, cmd.run)
    assert result == 'a 1 0.1'


def test_env_variable():
    env = {'x': Word('hello')}
    result = catch_output(env, Command(Word('print'), Variable('x')).run)
    assert result == 'hello'

    with raises(ShellError):
        Command(Word('print'), Variable('$y')).run(env)


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


def test_verify_arg_count():
    expected = infer_variadic_args(dummy)

    args = ['a', 'b']
    verify_arg_count(args, *expected)

    with raises(ShellTypeError):
        verify_arg_count([], *expected)


def test_verify_arg_types():
    expected = infer_variadic_args(dummy)
    args = [1, 0.1]
    verify_arg_types(args, dummy, *expected)


def dummy(a: int, *b: float):
    return a + b[0]


def echo(a: Term):
    return a
