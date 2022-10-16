#!/usr/bin/python3
from typing import Any, Dict

from shell_with_crud import ShellWithCRUD
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
    obj = ShellWithCRUD(repository=repository)
    main(shell=obj.shell)
