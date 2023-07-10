#!/usr/bin/python3
"""Browse and query a dynamic REST API.
"""
if __name__ == '__main__':
    import _extend_path

from json import JSONDecodeError, loads
from urllib.parse import quote_plus, urlparse

from mash.io_util import log
from mash.server.routes.default import basepath
from mash.shell import ShellWithFileSystem
from mash.shell.shell import main

from examples.rest_client_explicit import init_client

http_resource = object()


def retrieve_data(_fs, key, url, cwd, *_args):
    endpoint = 'https://dummy-api.com' + basepath[:-1]
    if url is http_resource:
        path = _infer_path(str(key), cwd)
        url = _infer_url(endpoint, path)
        return get(url)
    return url


def _infer_url(url: str, path: str):
    url = quote_plus(url, safe='://.?&')
    if path:
        url += '/' + '/'.join(str(k) for k in path)
    else:
        url += '/'
    return url


def _infer_path(key, cwd):
    path = cwd.path
    if 'repository' in path:
        i = path.index('repository')
        path = path[i+1:]
    elif key == 'repository':
        key = None

    if key:
        path.append(str(key))
    return path


def get(url):
    global http_resource

    # query a mock server
    data = init_client().get(urlparse(url).path)
    if data.status_code != 200:
        return f'{data._status} ({data.status_code})'

    try:
        data = loads(data.data)
    except JSONDecodeError as e:
        log('JSONDecodeError:', e, data.data)
        return f'"{data.data.decode()}"'

    if isinstance(data, list):
        return {k: http_resource for k in data}
    return data


def init():
    shell = ShellWithFileSystem(data={'repository': http_resource},
                                get_value_method=retrieve_data)

    obj = shell.repository
    obj.init_home(['repository'])
    return shell, obj


if __name__ == '__main__':
    shell, obj = init()

    user = obj.get(['users', '2'])
    print(user)

    main(shell=shell.shell)
