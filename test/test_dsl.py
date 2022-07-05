from contextlib import redirect_stdout
from io import StringIO
from pydoc import synopsis
import pytest

from dsl import Function, run_command


def test_Function_args():
    synopsis = 'list'
    func = Function(list, args=[], synopsis=synopsis, doc='')
    assert func.func == list
    assert func.help == synopsis


def test_Function_call():
    value = '1'

    f = Function(int, args=[], synopsis='')

    assert f(value) in [int(value), value + '\n']
    assert f() is None


def test_pipe():
    line = 'echo 100 |> echo'
    out = StringIO()
    with redirect_stdout(out):
        run_command(line)
        x = out.getvalue()

    assert out.getvalue() == '100\n'
