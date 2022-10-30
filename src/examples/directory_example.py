#!/usr/bin/python3
import sys
if __name__ == '__main__':
    sys.path.append('src')

from typing import Any, Dict

from shell.with_directory import ShellWithDirectory
from shell import main


# example data with dicts and lists
Data = Dict[str, Any]
repository: Data = {'worlds': [
    {'name': 'earth',
     'animals': [
         {'name': 'terrestrial',
          'snakes': [{'name': 'python'},
                     {'name': 'cobra'}]},
         {'name': 'aquatic',
          'penquins': [{'name': 'tux'}]}
     ]}]}


if __name__ == '__main__':
    obj = ShellWithDirectory(data=repository)
    main(shell=obj.shell)
