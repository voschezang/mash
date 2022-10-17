from shell.shell import Function


def test_Function_args():
    synopsis = 'list'
    func = Function(list, args=[], synopsis=synopsis, doc='')
    assert func.func == list
    assert func.help == synopsis


def test_Function_call():
    value = '1'

    f = Function(int, args=[], synopsis='')

    assert f(value) in [int(value), value + '\n']
    assert f() == 0
