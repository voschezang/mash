from examples.rest_client_explicit import init as init_explicit_client
from examples.rest_client_implicit import init as init_implicit_client
from test_shell import catch_output


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


def test_rest_client_get_nested_fields():
    for init in (init_explicit_client, init_implicit_client):
        shell, obj = init()
        shell = shell.shell

        emails = catch_output('list users >>= get users $ email', shell=shell)
        assert 'name.0@company.com' in emails
        assert 'name.9@company.com' in emails


def test_rest_client_foreach():
    for init in (init_explicit_client, init_implicit_client):
        shell, obj = init()
        shell = shell.shell

        users = catch_output('foreach users', shell=shell)
        assert len(users.split('\n')) == 10
        assert 'users 1000' in users
        assert 'users 1009' in users

        emails = catch_output('foreach users email', shell=shell)
        assert 'name.0@company.com' in emails
        assert 'name.9@company.com' in emails

def test_rest_client_standard_set():
    for init in (init_explicit_client, init_implicit_client):
        shell, _ = init()
        shell = shell.shell

        result = catch_output(r'{users}', shell=shell)
        assert result == ''
        assert len(shell._last_results[0]) > 3
        result = catch_output(r'x <- {users}', shell=shell)
        assert result == ''
        result = catch_output(r'{users} >>= echo $.users.email', shell=shell)
        users = result.splitlines()
        assert len(users) == 10
        assert 'name.0@company.com' in users
        assert 'name.1@company.com' in users

def test_rest_client_filter_set():
    for init in (init_explicit_client, init_implicit_client):
        shell, _ = init()
        shell = shell.shell

        # TODO
        # result = catch_output('{users | .id < 1002} >>= get id', shell=shell)
        # TODO add assertions
        # assert '1000' in result
        # assert '1001' in result
        # assert '1002' not in result

def test_rest_client_outer_product():
    for init in (init_explicit_client, init_implicit_client):
        shell, _ = init()
        shell = shell.shell

        # TODO add assertions
        result = catch_output('{users documents } >>= get $1.id', shell=shell)
        result = catch_output('{users documents | users.id < 1002} >>= get $1.id', shell=shell)
        result = catch_output('{users documents | 1.id == 2.owner} >>= get $1.name $2.name', shell=shell)