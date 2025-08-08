
from mash.io_util import catch_output
from mash.shell2.ast.command import Command
from mash.shell2.ast.multiline import IfElse
from mash.shell2.ast.term import Boolean, Word


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
