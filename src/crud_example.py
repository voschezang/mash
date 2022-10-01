#!/usr/bin/python3
from copy import deepcopy
from dataclasses import dataclass
from pprint import pformat
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


@dataclass
class ExampleContext:
    root: str = ''
    attr1: int = 1
    attr2: str = ''

    curent_object = None

    # Dependencies can be modelled as a Direct Acyclic Graph
    # It is assumed that there are no circular dependencies
    # direct_dependencies: AdjacencyList
    direct_dependencies = {'attr2': ['attr1']}

    # implement abc.MutableMapping in order to be compatible with Shell.env: dict
    # TODO refactor

    def __contains__(self, k):
        return hasattr(self, k)

    def __getitem__(self, k):
        try:
            try:
                return getattr(self, k)
            except TypeError:
                raise KeyError(k)

        except AttributeError as e:
            raise KeyError(e)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def __delitem__(self, k):
        del self.__dict__[k]


def init(repository=repository) -> CRUD:
    # TODO investigate why calling this function "setup" causes side-effects

    obj = CRUD(ExampleContext(), repository=repository)

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
    obj.shell.env = obj.context

    # reset path
    # TODO fix side-effects that require this hack
    obj.shell.do_cd()

    return obj


if __name__ == '__main__':
    obj = init(repository)
    main(shell=obj.shell)
