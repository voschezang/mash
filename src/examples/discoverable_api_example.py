#!/usr/bin/python3
import sys
if __name__ == '__main__':
    sys.path.append('src')

from functools import lru_cache
from urllib.parse import quote_plus
import requests

from shell.with_directory import ShellWithDirectory
from shell.shell import main


def retrieve_data(url, *args):
    if isinstance(url, str):

        url = quote_plus(url, safe='://.?&')
        if input(f'GET {url}\nContinue? Y/n: ').lower() in 'y ':
            return get(url, *args)
    return url


@lru_cache
def get(url, *args):
    print('url', url, list(args))
    result = requests.get(url)
    assert result.status_code == 200, (url, result.status_code, result.content)
    return result.json()


if __name__ == '__main__':
    obj = ShellWithDirectory(data={'repository': 'https://api.github.com/'},
                             get_value_method=retrieve_data)
    obj.repository.ll()
    obj.repository.ll('repo', 'events_url')

    main(shell=obj.shell)
