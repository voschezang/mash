if __name__ == '__main__':
    import _extend_path  # noqa

from mash.webtools.verify_server import main

if __name__ == '__main__':
    hostname = 'www.python.org'
    success, msg = main(hostname)
    print(success, msg)
