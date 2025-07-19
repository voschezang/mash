
from pytest import raises
from mash.io_util import catch_output
from mash.shell2.ast.command import Command
from mash.shell2.ast.term import Word


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


def test_command_output():
    cmd = Command(Word('print'), Word('a'), Word('b'), Word('c'))
    result = catch_output(None, cmd.run)
    assert result == 'a b c'
