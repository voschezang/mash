
from pytest import raises
from mash.shell.errors import ShellError
from mash.shell2.ast.variable import Variable


def test_variable():
    x = Variable('x')
    assert x.value == 'x'
    assert str(x) == 'x'


def test_run_variable():
    x = Variable('x')
    assert x.run({'x': 10}) == 10

    with raises(ShellError):
        x.run(None)

    with raises(ShellError):
        x.run({'y': 10})
