from mash.shell import ShellFunction


def test_Function_args():
    synopsis = 'list'
    func = ShellFunction(list, args=[], synopsis=synopsis, doc='')
    assert func.func == list
    assert func.help == synopsis


def test_Function_call():
    value = '1'

    f = ShellFunction(int, args=[], synopsis='')

    assert f(value) in [int(value), value + '\n']
    assert f() == 0
