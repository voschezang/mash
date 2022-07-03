import io
import sys
from contextlib import redirect_stdout
# from io import StringIO
from pydoc import synopsis
from dsl import Function


def test_Function_args():
    synopsis = 'list'
    func = Function(list, args=[], synopsis=synopsis, doc='')
    assert func.func == list
    assert func.help == synopsis


def test_Function_call():
    value = '1'

    # note that results are printed rather than returned
    out = io.StringIO()
    with redirect_stdout(out):
        Function(int, args=[], synopsis='')(value)
        assert out.getvalue() == value + '\n'

        # with missing argument
        Function(int, args=[], synopsis='')()
        assert 'ValueError' in out.getvalue()
