
from pytest import raises
from mash.io_util import catch_output
from mash.shell2.ast.command import Command
from mash.shell2.ast.term import Float, Integer, Word
from mash.shell2.ast.variable import Variable
from mash.shell2.builtins import Builtins


def test_metaclass():
    # test __contains__
    assert 'print' in Builtins

    # test __iter__
    iter(Builtins)

    # test __getitem__
    Builtins['print']


def test_missing_key():
    with raises(KeyError):
        Builtins['never']


def test_print():
    result = catch_output('abc', Builtins['print'])
    assert result == 'abc'


def test_type():
    for term, expected_type in [
        (Command(''), 'command'),
        (Float(10), 'float'),
        (Integer(10), 'int'),
        (Variable('x'), 'variable'),
        (Word('abc'), 'text')
    ]:
        result = catch_output(term, Builtins['type'])
        assert result == expected_type


def test_exit():
    with raises(SystemExit):
        Builtins['exit'](0)
