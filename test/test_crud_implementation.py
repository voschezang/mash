import io_util
from shell import run_command
from crud_implementation import init


def catch_output(line='', func=run_command, **func_kwds) -> str:
    return io_util.catch_output(line, func, **func_kwds)


def test_crud_ls():
    obj = init()
    shell = obj.shell

    assert catch_output('ls worlds', shell=shell) == "['earth']"
    assert catch_output('ll worlds', shell=shell) == 'earth'

    # autocomplete prefix
    assert catch_output('ll wo', shell=shell) == 'earth'

    # fuzzy match prefix
    assert catch_output('ll wow', shell=shell) == 'earth'

    # non-existing resource name
    assert catch_output('ls abc', shell=shell) == ''


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


def test_crud_cd_list():
    # TODO this testcase fails when tests are run in parallel

    obj = init()
    shell = obj.shell
    assert '0' not in shell.prompt

    run_command('cd w', obj.shell)

    assert '0' not in shell.prompt
    assert '1' not in shell.prompt

    # invalid index
    run_command('cd 1', obj.shell)
    assert '1' not in shell.prompt

    # valid index
    run_command('cd 0', obj.shell)
    assert '0' in shell.prompt
