#!/usr/bin/python3
from typing import Any, Dict

from crud import CRUD
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
    obj = CRUD(repository=repository)
    main(shell=obj.shell)
