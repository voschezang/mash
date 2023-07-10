import socket
import ssl
from django.core.validators import URLValidator, validate_ipv4_address, validate_ipv6_address
from django.core.exceptions import ValidationError
from urllib.parse import urlparse, quote_plus


class VerificationException(Exception):
    pass


def resolve(hostname: str):
    try:
        return socket.gethostbyname(hostname)
    # except socket.gaierror as e:
    except socket.error:
        raise VerificationException(f'Failed to resolve hostname: {hostname}')

    raise NotImplementedError()


def connect(hostname, port=443, timeout=3):
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # TODO test TLS versions
                # TODO measure time
                print(ssock.version())
                ssock.do_handshake()
                print(ssock.version())
    except ConnectionRefusedError as e:
        raise VerificationException(
            f'Connection refused for: {hostname}:{port}')
    except socket.timeout as e:
        raise VerificationException(
            f'Connection Timeout for: {hostname}:{port}')
    except socket.gaiaerror as e:
        raise VerificationException(f'Unknown Error for: {hostname}:{port}')
    except Exception as e:
        raise VerificationException(f'Unknown Error for: {hostname}:{port}')


def parse_url(url: str, default_scheme='http'):
    """Return the scheme, domain, port and path or a url

    Parameters
    ----------
    The following inputs are supported:
    - https://example.com
    - www.example.com:80
    - 1.0.0.1:443

    Returns
    -------
    ParseResult(scheme='http', netloc='example.com:443', path='/path;parameters', params='',
            query='query', fragment='fragment')
    """
    url = quote_plus(url)
    if '://' not in url:
        url = default_scheme + '://' + url

    return urlparse(url)


def parse_hostname(hostname, default_protocol='http', default_port=80):
    if hostname == 'localhost':
        return hostname

    try:
        validate_ipv4_address(hostname)
        return hostname
    except ValidationError:
        pass

    try:
        validate_ipv6_address(hostname)
        return hostname
    except ValidationError:
        pass

    if default_protocol and not str.startswith(hostname.lower(), default_protocol):
        hostname = default_protocol + '://' + hostname

    try:
        validator = URLValidator(schemes=['http', 'https'])
        validator(hostname)
    except ValidationError:
        raise VerificationException('Invalid hostname')

    return infer_protocol_and_port_from_hostname(hostname, default_port)


def infer_protocol_and_port_from_hostname(hostname, default_port):
    port = default_port
    if '://' in hostname:
        protocol, hostname = hostname.split('://', maxsplit=1)

    if ':' in hostname:
        hostname, port = hostname.split(':', maxsplit=1)

    port = parse_port(port)

    return protocol, hostname, port


def parse_port(port: str):
    port = str(port)

    # remove path suffix
    if '/' in port:
        port, _ = port.split('/', maxsplit=1)

    if not str.isdigit(port):
        raise ValueError('Invalid port')

    port = int(port)
    if port < 0 or port > 65535:
        raise ValueError('Invalid port')
    return port


def resolve_then_connect(hostname, *args):
    try:
        resolve(hostname)
        connect(hostname, *args)

    except VerificationException as e:
        print(e)
        return False, ', '.join(e.args)

    return True, ''


def main(url: str):
    url = parse_url(url)

    port = None
    hostname = url.netloc
    if ':' in url.netloc:
        hostname, port = hostname.split(':')

    if port is None:
        return resolve_then_connect(hostname)
    return resolve_then_connect(hostname, port)


if __name__ == '__main__':
    hostname = 'www.python.org'
    success, msg = main(hostname)
    print(success, msg)
