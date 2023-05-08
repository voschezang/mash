from copy import deepcopy
from pytest import raises

from examples.filesystem import repository
from examples.rest_client import init
from src.mash.shell.cmd2 import run_command
from src.mash.shell import ShellWithFileSystem, ShellError
from src.mash import io_util


def init_client(**kwds):
    return ShellWithFileSystem(data=deepcopy(repository), **kwds)


def catch_output(line='', func=run_command, **func_kwds) -> str:
    return io_util.catch_output(line, func, **func_kwds)


def test_crud_ls():
    obj = init_client()
    shell = obj.shell

    assert catch_output('list', shell=shell) == 'worlds'
    assert catch_output('list worlds', shell=shell) == 'earth'
    assert catch_output('l worlds', shell=shell) == 'earth'

    # autocomplete prefix
    assert catch_output('l wo', shell=shell) == 'earth'

    # fuzzy match prefix
    assert catch_output('l wow', shell=shell) == 'earth'

    # non-existing resource name
    assert catch_output('l abc', shell=shell) == ''


def test_crud_get():
    obj = init_client()
    shell = obj.shell

    s = '| worlds | [ earth ]'
    assert s in catch_output('get', shell=shell)
    s = '[ earth ]'
    assert s in catch_output('get worlds', shell=shell)
    s = '| animals | [ terrestrial,aquatic ] |'
    assert s in catch_output('get worlds earth', shell=shell)


def test_crud_set():
    obj = init_client()
    shell = obj.shell

    run_command('set x 10', shell=shell)
    assert catch_output('get x', shell=shell) == '10'

    run_command('set x 1 2 3', shell=shell)
    assert catch_output('get x', shell=shell) == "['1', '2', '3']"


def test_crud_new():
    obj = init_client()
    shell = obj.shell

    run_command('new a', shell=shell)
    assert catch_output('l a', shell=shell) == ''

    run_command('cd a', shell=shell)
    run_command('new b c', shell=shell)
    assert catch_output('pwd', shell=shell) == '/ a'

    assert catch_output('list b', shell=shell) == ''
    assert catch_output('list c', shell=shell) == ''


def test_crud_expansion():
    obj = init_client()
    shell = obj.shell
    assert catch_output('print *', shell=shell) == 'worlds'


def test_crud_cd_dict():
    obj = init_client()
    shell = obj.shell

    assert 'worlds' not in shell.prompt

    # invalid resource name
    run_command('cd abc', obj.shell)
    assert 'worlds' not in shell.prompt

    # valid resource name
    run_command('cd worlds', obj.shell)
    assert 'worlds' in shell.prompt

    obj.repository.cd()
    assert 'worlds' not in shell.prompt

    obj.repository.cd('worlds')
    assert 'worlds' in shell.prompt


def test_crud_ls_after_cd():
    obj = init_client()
    obj.repository.cd('worlds')

    # use ll()
    result = obj.repository.ll()
    assert result == 'earth'

    # use do_ls()
    result = catch_output('list', shell=obj.shell)
    assert result == 'earth'


def test_crud_cd_list():
    # TODO this testcase fails when tests are run in parallel

    obj = init_client()
    shell = obj.shell

    assert 'w' not in shell.prompt

    run_command('cd w', obj.shell)

    assert '0' not in shell.prompt

    # invalid index
    run_command('cd 1', obj.shell)
    assert 'earth' not in shell.prompt
    assert '1' not in shell.prompt

    # valid index
    run_command('cd 0', obj.shell)
    assert 'earth' in shell.prompt


def test_set_cd_aliasses():
    obj = init_client()
    shell = obj.shell

    parent = 'worlds'
    child = 'animals'

    assert parent not in shell.prompt
    assert child not in shell.prompt

    # this should fail silently
    run_command(child, obj.shell)
    assert child not in shell.prompt
    assert parent not in shell.prompt

    run_command(parent, obj.shell)
    assert parent in shell.prompt

    run_command('0', obj.shell)
    assert 'earth' in shell.prompt

    run_command(child, obj.shell)
    # the child-dir is translated into an index
    assert 'earth' in shell.prompt

    run_command('animals', obj.shell)
    assert 'animals' in shell.prompt


def test_crud_env_get():
    k = 'root'
    v = 'abc'

    obj = init_client()
    obj.shell.env[k] = v

    line = f'env {k}'
    result = catch_output(line, shell=obj.shell, strict=True)
    assert '| root | abc      |' in result


def test_crud_env_set():
    obj = init_client()
    k = 'a'
    v = '10'

    obj.shell.env[k] = v

    line = f'env {k}'
    assert v in catch_output(line, shell=obj.shell, strict=True)

    line = f'echo ${k}'
    assert v in catch_output(line, shell=obj.shell, strict=True)

    del obj.shell.env[k]

    with raises(KeyError):
        obj.shell.env[k]


def test_crud_env_expand():
    obj = init_client()
    k = 'root'
    v = '10'

    # set value using infix operator (`=`)
    line = f'{k} = {v}'
    run_command(line, shell=obj.shell, strict=True)

    line = f'echo ${k}'
    assert v in catch_output(line, shell=obj.shell, strict=True)


def test_cd_with_Options():
    o = init_client()
    o.repository.cd('worlds')
    assert o.repository.path == ['worlds']

    run_command('..', o.shell)
    assert o.repository.path == []

    run_command('-', o.shell)
    assert o.repository.path == ['worlds']


def test_shell_home():
    o = init_client(home=['worlds', 'earth'])

    assert o.repository.path == []
    assert o.repository.ls('animals') == [0, 1]

    o.repository.cd('/')
    assert o.repository.path == ['/']


def test_shell_globbing():
    o = init_client(home=['worlds', 'earth'])
    shell = o.shell

    assert catch_output('list an?mal?', shell=shell) == 'terrestrial\naquatic'
    assert catch_output('list a*', shell=shell) == 'terrestrial\naquatic'
    assert catch_output('list [!n]*', shell=shell) == 'terrestrial\naquatic'


def test_shell_invalid_globbing():
    o = init_client(home=['worlds', 'earth'])
    shell = o.shell

    assert catch_output('list [ter]', shell=shell) == ''

    run_command('cd animals', shell=shell)

    with raises(ShellError):
        run_command('list [ter]', shell=shell, strict=True)


def test_rest_client_users():
    shell, obj = init()

    fields = obj.ls()
    assert fields == ['users']

    users = obj.ls('users')
    assert 1 in users
    assert len(users) == 10


def test_rest_client_user():
    shell, obj = init()
    user = obj.ls(['users', '1'])
    assert 'id' in user
    assert 'name' in user
    assert 'email' in user

    user = obj.get(['users', '1'])
    assert user['id'] == 1
    assert '1' in user['name']


def test_rest_client_cd_user():
    shell, obj = init()

    obj.cd('users', '1')
    user = obj.get([])

    assert user['id'] == 1
    assert '1' in user['name']
    assert user['name'] in shell.shell.prompt
