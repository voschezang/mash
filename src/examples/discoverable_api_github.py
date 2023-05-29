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
        if input(f'GET {url}\nContinue? Y/n: ').lower() in 'y ':
            return get(url)
    return url


@lru_cache
def get(url):
    print('url', url)
    result = requests.get(url)
    assert result.status_code == 200, (url, result.status_code, result.content)
    return result.json()


if __name__ == '__main__':
    obj = ShellWithFileSystem(data={'repository': 'https://api.github.com/'},
                              get_value_method=retrieve_data)
    obj.repository.ll()
    obj.repository.ll('repo', 'events_url')
    obj.repository.init_home('repo')

    main(shell=obj.shell)
