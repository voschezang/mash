#!/usr/bin/python3
if __name__ == '__main__':
    import _extend_path

from typing import Any, Dict

from mash.shell import ShellWithFileSystem
from mash.shell.shell import main
from mash.util import constant

add_custom_commands = True

# example data with a mix of dicts and lists
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
    obj = ShellWithFileSystem(data=repository)

    if add_custom_commands:
        obj.init_shell(functions={'info': constant('This is a usage example')})

    main(shell=obj.shell)
