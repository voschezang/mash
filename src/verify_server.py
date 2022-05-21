import socket
import ssl


class VerificationException(Exception):
    pass


def resolve(hostname: str):
    try:
        return socket.gethostbyname(hostname)
    # except socket.gaierror as e:
    except socket.error as e:
        raise VerificationException(f'Failed to resolve hostname: {hostname}')

    raise NotImplementedError()


def connect(hostname, port=443, timeout=3):
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # TODO test TLS versions
                ssock.do_handshake()
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


def main(hostname, *args):
    try:
        resolve(hostname)
        connect(hostname, *args)
    except VerificationException as e:
        print(e)
        return False, ', '.join(e.args)

    return True, ''


if __name__ == '__main__':
    hostname = 'www.python.org'
    success, msg = main(hostname)
    print(success, msg)
