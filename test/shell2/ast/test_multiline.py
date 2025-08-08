
from contextlib import redirect_stdout
from io import StringIO

from pytest import raises
from mash.io_util import catch_output
from mash.shell.errors import ShellError
from mash.shell2.ast.command import Command
from mash.shell2.ast.lines import Lines
from mash.shell2.ast.multiline import IfElse
from mash.shell2.ast.function import Function
from mash.shell2.ast.term import Boolean, Word
from mash.shell2.ast.variable import Variable
from mash.shell2.env import Environment


def test_multiline_if_else():
    condition = IfElse(Boolean(True),
                       then=Command(Word('print'), Word('first')),
                       otherwise=Command(Word('print'), Word('last')),
                       )
    assert isinstance(condition.condition, Boolean)
    assert isinstance(condition.then, Command)
    assert isinstance(condition.otherwise, Command)

    assert str(condition) == '(?) (true)'

    result = catch_output(None, condition.run)
    assert result == 'first'


def test_multiline_function_definition():
    body = Command(Word('print'), Variable('x'), Variable('x'))
    args = [Variable('x')]
    fun = Function('repeat', args, Lines(body))
    alt = Function('repeat', args, Lines(body))

    assert str(fun) == 'repeat ($x)'
    assert fun == fun
    assert alt != fun

    # env = Environment({}, {})
    env = {}
    fun.run(env)
    assert 'repeat' in env

    line = Lines(Command(Word('repeat'), Word('hello')))
    result = catch_output(env, line.run)

    assert result == 'hello hello'

    # not engough arguments
    with raises(ShellError):
        Lines(Command(Word('repeat'))).run(env)
