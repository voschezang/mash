#!/usr/bin/python3
if __name__ == '__main__':
    import _extend_path

from functools import lru_cache
from json import JSONDecodeError, loads
from urllib.parse import quote_plus, urlparse
import requests
from examples.rest_client import init_client

from mash.shell import ShellWithFileSystem
from mash.shell.shell import main
from mash.server import basepath


endpoint = 'https://dummy-api.com' + basepath[:-1]


def retrieve_data(_fs, key, url, cwd, *_args):
    if isinstance(url, str) and 'http' in url:

        path = cwd.path
        if 'repository' in path:
            i = path.index('repository')
            path = path[i+1:]
        elif key == 'repository':
            key = None

        if key:
            path.append(str(key))

        url = quote_plus(url, safe='://.?&')
        if path:
            url += '/' + '/'.join(path)
        else:
            url += '/'
        return get(url)

    return url


def get(url):
    data = init_client().get(urlparse(url).path)

    try:
        data = loads(data.data)
    except JSONDecodeError as e:
        print(e)

    if isinstance(data, list):
        return {k: endpoint for k in data}
    return data


if __name__ == '__main__':
    obj = ShellWithFileSystem(data={'repository': endpoint},
                              get_value_method=retrieve_data)
    obj.repository.ll()
    obj.repository.ll('repo')
    obj.repository.init_home('repo')

    user = obj.repository.get(['users', '2'])
    print(user)

    main(shell=obj.shell)
