from pathlib import Path
from pytest import raises
from time import perf_counter

from mash.shell.errors import ShellError

from test_shell import catch_output


def test_pipe():
    assert catch_output('print 100 |> print 2') == '2 100'
    assert catch_output('echo "a@b" |> echo') == 'a@b'


def test_pipe_unix():
    # assert catch_output('print 100 | less') == '100'

    # with quotes
    assert catch_output('print "2; echo 12" | grep 2') == "'2; echo 12'"


def test_pipe_input():
    assert catch_output('print abc | grep abc') == 'abc'

    # fail in strict mode
    with raises(ShellError):
        catch_output('echo abc | grep def', strict=True)

    # fail silently without in strict mode
    assert catch_output('echo abc | grep def', strict=False) == ''


def test_pipe_to_file():
    text = 'abc'
    filename = '.pytest_tmp_out.txt'

    # clear file content
    f = Path(filename)
    f.unlink(True)

    result = catch_output(f'print {text} >- {filename}')
    assert result == ''

    # verify output file
    assert f.read_text().rstrip() == text

    f.unlink()


def test_pipe_to_file_with_interop():
    t = str(perf_counter())
    f = '.pytest_time'
    cmd = f'print {t} >- {f} ; cat {f}'

    assert catch_output(cmd).strip() == t, cmd

    Path(f).unlink()
