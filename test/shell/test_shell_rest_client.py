from examples.rest_client_explicit import init as init_explicit_client
from examples.rest_client_implicit import init as init_implicit_client
from src.mash.shell.cmd2 import run_command
from src.mash import io_util


def catch_output(line='', func=run_command, **func_kwds) -> str:
    return io_util.catch_output(line, func, **func_kwds)


def test_rest_client_users():
    for init in (init_explicit_client, init_implicit_client):
        shell, obj = init()

        fields = obj.ls()
        assert 'users' in fields

        users = obj.ls('users')
        assert 1001 in users
        assert len(users) == 10

        obj.cd('users')
        users = obj.ls()
        assert 1001 in users
        assert len(users) == 10


def test_rest_client_user_exlicit():
    shell, obj = init_explicit_client()
    user = obj.ls(['users', '100'])
    assert 'id' in user

    user = obj.get(['users', '1001'])
    assert user['id'] == 1001
    assert '1' in user['name']


def test_rest_client_user_implicit():
    shell, obj = init_implicit_client()

    user = obj.ls(['users', '1001'])
    assert 'name' in user
    assert 'email' in user

    user = obj.get(['users', '1001'])
    assert '1' in user['name']


def test_rest_client_cd_user_explicit():
    shell, obj = init_explicit_client()

    obj.cd('users', '1001')
    user = obj.get([])

    assert user['id'] == 1001
    assert '1' in user['name']
    assert user['name'] in shell.shell.prompt


def test_rest_client_cd_user_implicit():
    shell, obj = init_implicit_client()

    obj.cd('users', '1')
    user = obj.get([])

    assert user['name'] in shell.shell.prompt


def test_rest_client_get_fields_1():
    for init in (init_explicit_client, init_implicit_client):
        shell, obj = init()
        shell = shell.shell

        obj.cd('users')

        emails = catch_output('flatten 1001 1004 >>= get $ email', shell=shell)
        assert emails == 'name.1@company.com\nname.4@company.com'


def test_rest_client_get_fields_2():
    for init in (init_explicit_client, init_implicit_client):
        shell, obj = init()
        shell = shell.shell

        catch_output('get_email (user): get $user email', shell=shell)

        obj.cd('users')
        email = catch_output('get 1002 email', shell=shell)
        assert email == 'name.2@company.com'

        emails = catch_output('map get_email 1001 1004', shell=shell)
        assert emails == 'name.1@company.com\nname.4@company.com'
