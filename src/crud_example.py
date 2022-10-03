#!/usr/bin/python3
from dataclasses import dataclass, fields
from typing import Any, Dict

from crud_base import Options
from crud import CRUD
from shell import build, main
from util import AdjacencyList, find_fuzzy_matches


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


def init(repository=repository) -> CRUD:
    # TODO investigate why calling this function "setup" causes side-effects

    obj = CRUD(repository=repository)

    def cd(*args):
        return obj.cd(*args)

    def ls(*args):
        return [item.name for item in obj.ls(*args)]

    def ll(*args):
        return obj.ll(*args)

    def complete_cd(self, text, line, begidx, endidx):
        candidates = ls()
        return list(find_fuzzy_matches(text, candidates))

    functions = {
        'cd': cd,
        'ls': ls,
        'll': ll,
        'tree': obj.tree
    }
    completions = {
        'cd': complete_cd
    }

    obj.shell = build(functions, completions)
    obj.shell.set_do_char_method(obj.shell.do_cd, Options)

    # reset path
    # TODO fix side-effects that require this hack
    obj.shell.do_cd()

    return obj


if __name__ == '__main__':
    obj = init(repository)
    main(shell=obj.shell)
