from pytest import raises

from mash import io_util
from mash.shell import ShellError
from mash.shell.grammer.delimiters import TRUE
from mash.shell.errors import ShellSyntaxError
from mash.shell.shell import Shell, run_command


def catch_output(line='', func=run_command, **kwds) -> str:
    return io_util.catch_output(line, func, **kwds)


def test_shell_if_then():
    shell = Shell()
    shell.ignore_invalid_syntax = False
    assert catch_output('if "" then 2 |> echo 1', shell=shell) == ''

    assert catch_output('if "" then print 1', shell=shell) == ''
    assert catch_output('if 1 then print 1', shell=shell) == '1'

    run_command('a = ""', shell=shell)
    assert catch_output('if $a then print 1', shell=shell) == ''
    run_command('a = false or true', shell=shell)
    assert catch_output('if $a then print 1', shell=shell) == '1'

    assert catch_output('if echo 1 |> echo then 2', shell=shell) == '2'
    assert catch_output('if echo "" |> echo then 2', shell=shell) == ''

    assert catch_output('if 10 then 2 |> echo 1', shell=shell) == '1 2'
    assert catch_output('if "" then 2 |> echo 1', shell=shell) == ''


def test_shell_if_eval():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    assert catch_output('if echo then print 1', shell=shell) == ''
    assert catch_output('if echo 2 then print 1', shell=shell) == '1'
    assert catch_output('if bool "" then print 1', shell=shell) == ''
    assert catch_output('if bool ... then print 1', shell=shell) == ''


def test_shell_if_compare():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    assert catch_output('if 1 < 2 then print 1', shell=shell) == '1'
    assert catch_output('if 1 > 2 then print 1', shell=shell) == ''


# def test_shell_if_then_multiline():
#     shell = Shell()

#     run_command('if ""', shell=shell)
#     assert catch_output('then print 1', shell=shell) == ''

#     run_command('if 1', shell=shell)
#     assert catch_output('then print 1', shell=shell) == '1'

#     # fail on double else
#     with raises(ShellError):
#         run_command('then 1', shell=shell, strict=True)


def test_shell_if_then_semicolons():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    assert catch_output('if 10 then print 1 ; print 2', shell=shell) == '1\n2'
    assert catch_output('if "" then print 1 ; print 2', shell=shell) == '2'


def test_shell_if_then_nested():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    assert catch_output('if 1 then if 2 then print 3',
                        shell=shell) == '3'

    with raises(ShellError):
        run_command('if 1 then if "" print 3', shell=shell)

    assert catch_output('if "" then if 2 then print 3',
                        shell=shell) == ''

    assert catch_output('if 1 then if "" then print 3',
                        shell=shell) == ''


def test_shell_if_with_assign():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    run_command('a <- if "" then 3 else 4', shell=shell)
    assert shell.env['a'] == '4'

    run_command('b <- if 1 then range 2', shell=shell)
    assert 'b' in shell.env
    assert shell.env['b'] == '0\n1'

    # skip missing else
    run_command('a <- if 1 then 3', shell=shell)
    assert 'a' in shell.env
    assert shell.env['a'] == '3'

    # missing else should default to ''
    run_command('a <- if "" then 3', shell=shell)
    assert shell.env['a'] == ''


def test_shell_if_else():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    assert catch_output('if "" then print 1 else print 2') == '2'
    assert catch_output('if 10 then print 1 else print 2') == '1'


def test_shell_if_else_with_pipes():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    # pipe in IF
    assert catch_output('if echo 10 |> echo then 2 else 3', shell=shell) == '2'
    assert catch_output('if echo 10 |> echo then 2 else 3', shell=shell) == '2'

    assert catch_output('if echo "" |> echo 1 then 2 else 3',
                        shell=shell) == '2'

    # pipe in THEN
    assert catch_output('if 10 then echo 2 |> echo 3 else 4',
                        shell=shell) == '3 2'
    assert catch_output('if "" then echo 2 |> echo 3 else 4',
                        shell=shell) == '4'

    assert catch_output(
        'if 10 then echo 2 |> math 1 + else 4', shell=shell) == '3'
    assert catch_output(
        'if "" then echo 2 |> math 1 + else 4', shell=shell) == '4'

    # pipe in ELSE
    assert catch_output('if 10 then echo 4 else 2 |> echo 3',
                        shell=shell) == '4'
    assert catch_output('if "" then echo 4 else 2 |> echo 3',
                        shell=shell) == '3 2'


def test_shell_if_then_if_else():
    """Test the following pattern:
    if () then
        if () then 
            print 1
        else 
            print 2
    else
        print 3
    """
    shell = Shell()
    shell.ignore_invalid_syntax = False

    x = 'if 20 then print 1 else print 2'
    not_x = 'if "" then print 1 else print 2'

    # True & True
    assert catch_output(f'if 10 then {x}') == '1'
    # True & True
    assert catch_output(f'if 10 then {x} else print 3') == '1'
    # True & False
    # the double else behaves like a |> operator
    assert catch_output(f'if 10 then {not_x} else print 3') == '2'
    # # False & True
    assert catch_output(f'if "" then {x} else print 3') == '3'
    # # False & False
    assert catch_output(f'if "" then {not_x} else print 3') == '3'


def test_shell_if_then_else_if_then():
    """Test the following pattern:
    if () then
        print 1
    else 
        if () then 
            print 2
        else
            print 3
    """
    shell = Shell()
    shell.ignore_invalid_syntax = False

    then_elif = 'then print 1 else if 20 then'
    then_elif_not = 'then print 1 else if "" then'

    # True, True
    assert catch_output(f'if 10 {then_elif} print 2') == '1'
    # True, True
    assert catch_output(f'if 10 {then_elif} print 2 else print 3') == '1'
    # True, False
    assert catch_output(f'if 10 {then_elif_not} print 2 else print 3') == '1'

    # False, True
    assert catch_output(f'if "" {then_elif} print 2 else print 3') == '2'
    # False, False
    assert catch_output(f'if "" {then_elif_not} print 2 else print 3') == '3'


def test_shell_if_else_unhappy():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    with raises(ShellSyntaxError):
        run_command('if "" else print 2', shell=shell)

    with raises(ShellError):
        run_command('if "" then print 1 else print 2 else print 3',
                    shell=shell)


def test_shell_if_else_multiline():
    """Test the following pattern:
    if () then print 1
    else 
        if () then print 2
        else
            if () then print 2
                else
                    ..
    """
    shell = Shell()
    shell.ignore_invalid_syntax = False

    def line(a, b, c):
        return f"""
if {a} then 
    print 1
else if {b} 
then print 2
else
    print 3

# a second independent branch
if {c} then print 4
    """

    t = TRUE
    f = '""'
    assert catch_output(line(t, f, f)) == '1'
    assert catch_output(line(t, t, f)) == '1'
    assert catch_output(line(f, f, f)) == '3'

    assert catch_output(line(t, f, t)) == '1\n4'
    assert catch_output(line(t, t, t)) == '1\n4'
    assert catch_output(line(f, t, t)) == '2\n4'
    assert catch_output(line(f, f, t)) == '3\n4'


def test_shell_if_else_multiline_nested():
    shell = Shell()
    shell.ignore_invalid_syntax = False

    def line(a, b, c, d):
        return f"""
if {a} then 
    if {b} then
        print 1
    else
        print 2

else if {c} then
    if {d} then
        print 3
    else
        print 4
else
    print 5
    """

    t = TRUE
    f = '""'
    if 0:
        # TODO implement
        assert catch_output(line(t, f, f, f)).strip() == '2'
        assert catch_output(line('1', ' ', ' ', '1')).strip() == '2'
        assert catch_output(line('1', '1', '1', '1')).strip() == '1'
        assert catch_output(line('1', '1', ' ', ' ')).strip() == '1'
        assert catch_output(line(' ', '1', ' ', ' ')).strip() == '5'
        assert catch_output(line(' ', '1', '1', '1')).strip() == '3'
        assert catch_output(line(' ', '1', '1', ' ')).strip() == '4'
        assert catch_output(line(' ', ' ', '1', ' ')).strip() == '4'
        assert catch_output(line(' ', ' ', ' ', '1')).strip() == '5'
        assert catch_output(line(' ', ' ', ' ', ' ')).strip() == '5'
