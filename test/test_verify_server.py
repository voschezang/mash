from mash.verify_server import VerificationException, resolve, connect, parse_hostname, parse_port
import pytest

localhost = '127.0.0.1'


def test_parse_hostname_return_value():
    assert parse_hostname('www.python.org') == ('http', 'www.python.org', 80)
    assert parse_hostname(
        'https://python.org:443') == ('https', 'python.org', 443)


class disabled_tests:
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

    def test_parse_hostname_termination():
        host = 'python.org'
        valid_hosts = [host,
                       'www.' + host,
                       'http://' + host,
                       'http://www.' + host,
                       'http://www.' + host + ':80',
                       'http://www.' + host + ':443',
                       'http://www.' + host + ':1443',
                       'http://www.' + host + ':1443/home.html',
                       '1.1.1.1',
                       '1.1.1.1:443',
                       localhost,
                       'localhost']

        for hostname in valid_hosts:
            parse_hostname(hostname)

        invalid_hosts = ['_', 'py:th:on', host + '/resource:port:a']
        for hostname in invalid_hosts:
            with pytest.raises(VerificationException):
                parse_hostname(hostname)

    def test_parse_port():
        for value in [80, '80', '80/resource/value/1']:
            assert parse_port(value) == 80

        for value in ['-10', '99999999', 'l443', '']:
            with pytest.raises(VerificationException):
                parse_port(value)


def read_result(f, *args, **kwds) -> str:
    """Catch `VerificationException` and return the error message.
    """
    try:
        f(*args, **kwds)
    except ValueError as e:
        return ''.join(e.args).lower()
    return ''
