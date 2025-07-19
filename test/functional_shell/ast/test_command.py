
from pytest import raises
from mash.functional_shell.ast.command import Command
from mash.functional_shell.ast.term import Term
from mash.functional_shell.ast.terms import Terms


def test_command_init():
    cmd = Command('yes')
    assert cmd.f == 'yes'

    cmd = Command('print', Terms(Term('a'), Term('b'), Term('c')))
    assert cmd.f == 'print'
    assert cmd.terms.values == ('a', 'b', 'c')


def test_command_run():
    cmd = Command('print', Terms(Term('a'), Term('b'), Term('c')))

    # result = cmd.run(None)
    # assert result == 'a b c'

    with raises(NotImplementedError):
        cmd.run(None)
