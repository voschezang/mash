from verify_server import VerificationException, resolve, connect
import pytest

localhost = '127.0.0.1'


def test_resolve():

    resolve('google.com')
    resolve('localhost')
    resolve(localhost)

    with pytest.raises(VerificationException):
        resolve('never.google.com')

    assert 'resolve' in read_result(resolve, 'http://google.com')
    assert 'resolve' in read_result(resolve, 'never.google.com')


def test_connect():
    hostname = 'www.python.org'

    connect(hostname)

    with pytest.raises(VerificationException):
        connect(hostname, 80)

    with pytest.raises(VerificationException):
        connect(localhost)

    assert 'connection timeout' in read_result(connect, hostname, 80)
    assert 'connection refused' in read_result(connect, localhost)


def read_result(f, *args, **kwds) -> str:
    """Catch `VerificationException` and return the error message.
    """
    try:
        f(*args, **kwds)
    except VerificationException as e:
        return ''.join(e.args).lower()
    return ''
