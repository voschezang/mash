#!/usr/bin/python3
if __name__ == '__main__':
    import _extend_path

from functools import lru_cache
from urllib.parse import quote_plus
import requests

from mash.shell import ShellWithFileSystem
from mash.shell.shell import main


def retrieve_data(_fs, _key, url, *_args):
    if isinstance(url, str) and 'http' in url:

        url = quote_plus(url, safe='://.?&')
        return get(url)
    return url


@lru_cache
def get(url):
    print('url', url)
    result = requests.get(url)
    assert result.status_code == 200, (url, result.status_code, result.content)
    return result.json()


def init():
    url = 'https://graph.microsoft.com/v1.0'
    obj = ShellWithFileSystem(data={'repository': url},
                              get_value_method=retrieve_data)
    obj.repository.ll()
    obj.repository.ll('repo')
    obj.repository.init_home('repo')

    values = obj.repository.get(['value'])
    for value in values:
        if 'me' in value['name']:
            obj.repository.set(value['name'], url + '/' + value['url'])

    return obj


if __name__ == '__main__':
    obj = init()
    main(shell=obj.shell)
