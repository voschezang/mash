from pytest import raises

from shell_with_crud import ShellWithCRUD
from crud import Options
from crud_example import repository
from shell import run_command
import io_util


def init():
    return ShellWithCRUD(repository=repository)


def catch_output(line='', func=run_command, **func_kwds) -> str:
    return io_util.catch_output(line, func, **func_kwds)


def test_crud_ls():
    obj = init()
    shell = obj.shell

    assert catch_output('ls worlds', shell=shell) == 'earth'
    assert catch_output('ll worlds', shell=shell) == 'earth'

    # autocomplete prefix
    assert catch_output('ll wo', shell=shell) == 'earth'

    # fuzzy match prefix
    assert catch_output('ll wow', shell=shell) == 'earth'

    # non-existing resource name
    assert catch_output('ls abc', shell=shell) == ''


def test_crud_expansion():
    obj = init()
    shell = obj.shell
    assert catch_output('print *', shell=shell) == 'worlds'


def test_crud_cd_dict():
    obj = init()
    shell = obj.shell

    assert 'worlds' not in shell.prompt

    # invalid resource name
    run_command('cd abc', obj.shell)
    assert 'worlds' not in shell.prompt

    # valid resource name
    run_command('cd worlds', obj.shell)
    assert 'worlds' in shell.prompt

    obj.crud.cd()
    assert 'worlds' not in shell.prompt

    obj.crud.cd('worlds')
    assert 'worlds' in shell.prompt


def test_crud_ls_after_cd():
    obj = init()
    obj.crud.cd('worlds')

    # use ls()
    result = obj.crud.ls_str()
    assert result[0].name == 'earth'

    # use do_ls()
    result = catch_output('ls', shell=obj.shell)
    assert result == 'earth'


def test_crud_cd_list():
    # TODO this testcase fails when tests are run in parallel

    obj = init()
    shell = obj.shell

    assert 'w' not in shell.prompt

    run_command('cd w', obj.shell)

    assert '0' not in shell.prompt

    # invalid index
    run_command('cd 1', obj.shell)
    assert 'earth' not in shell.prompt
    assert '10' not in shell.prompt

    # valid index
    run_command('cd 0', obj.shell)
    assert 'earth' in shell.prompt


def test_set_cd_aliasses():
    obj = init()
    shell = obj.shell

    parent = 'worlds'
    child = 'earth'

    assert parent not in shell.prompt
    assert child not in shell.prompt

    # this should fail silently
    run_command(child, obj.shell)
    assert child not in shell.prompt

    run_command(parent, obj.shell)
    assert parent in shell.prompt

    run_command(child, obj.shell)
    # the child-dir is translated into an index
    assert 'earth' in shell.prompt

    run_command('animals', obj.shell)
    assert 'animals' in shell.prompt


def test_crud_env_get():
    k = 'root'
    v = 'abc'

    obj = init()
    obj.shell.env[k] = v

    line = f'env {k}'
    result = catch_output(line, shell=obj.shell, strict=True)
    assert result == "{'root': 'abc'}"


def test_crud_env_set():
    obj = init()
    k = 'a'
    v = '10'

    obj.shell.set_env_variable(k, v)

    assert obj.shell.env[k] == v

    line = f'env {k}'
    assert v in catch_output(line, shell=obj.shell, strict=True)

    line = f'echo ${k}'
    assert v in catch_output(line, shell=obj.shell, strict=True)

    del obj.shell.env[k]

    with raises(KeyError):
        obj.shell.env[k]


def test_crud_env_expand():
    obj = init()
    k = 'root'
    v = '10'

    # set value using infix operator (`=`)
    line = f'{k} = {v}'
    assert k in catch_output(line, shell=obj.shell, strict=True)

    line = f'echo ${k}'
    assert v in catch_output(line, shell=obj.shell, strict=True)


def test_cd_with_Options():
    o = init()
    o.crud.cd('worlds')
    assert o.crud.path == ['worlds']

    run_command('..', o.shell)
    assert o.crud.path == []

    run_command('-', o.shell)
    assert o.crud.path == ['worlds']
