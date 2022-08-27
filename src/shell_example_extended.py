#!/usr/bin/python3
from copy import deepcopy
from dataclasses import dataclass
from pprint import pformat
from typing import List

import crud
from crud import Item, Options
from shell import Shell, run, set_completions, set_functions
from util import DataClassHelper, decorate, AdjacencyList, find_prefix_matches, list_prefix_matches


# example data with dicts and lists
repository = {'worlds': [
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
    root: str
    attr1: int
    attr2: str

    curent_object = None

    # Dependencies can be modelled as a Direct Acyclic Graph
    # It is assumed that there are no circular dependencies
    # direct_dependencies: AdjacencyList
    direct_dependencies = {'attr2': ['attr1']}


class CRUD(crud.CRUD):
    def __init__(self, context, shell: Shell = None, **kwds):
        super().__init__(**kwds)
        self.init__context(context)
        self.shell = shell

        self.post_cd_hook = self.update_prompt

    def init__context(self, context):
        # add helper methodsw
        self.original_context = context
        self.context = decorate(deepcopy(context),
                                DataClassHelper(context))

    def ls(self, obj=None) -> List[Item]:
        items = self._ls(obj)
        return self.wrap_list_items(items)

    def ll(self, obj=None, delimiter='\n'):
        # items = self.ls(obj)
        items = self.infer_item_names(self.ls(obj))
        return delimiter.join([str(item.name) for item in items])

    def tree(self, obj=None):
        items = self._ls(obj)
        return pformat(repository, indent=2)

    def _ls(self, obj):
        cwd = self.infer_cwd()
        if obj is None:
            return cwd

        if self.autocomplete and obj not in cwd:
            obj = next(find_prefix_matches(obj, cwd.keys()))

        if obj in cwd:
            return cwd[obj]

        values = cwd.keys()
        msg = f'Error, {obj} is not in cwd ({values})'
        print(msg)
        raise ValueError(msg)

    def infer_cwd(self):
        """Infer the current working directory
        """
        # mock a repository
        global repository
        cwd = repository
        for directory in self.path:
            try:
                if isinstance(cwd, list):
                    directory = int(directory)
                cwd = cwd[directory]
            except (IndexError, KeyError):
                raise ValueError(f'Dir {directory} not in cwd ({cwd})')

        return cwd

    def wrap_list_items(self, items) -> List[Item]:
        if hasattr(items, 'keys'):
            items = [Item(k, v) for k, v in items.items()]

        elif isinstance(items, list):
            # if items and 'name' in items[0]:
            #     items = [Item(item['name'], item) for i, item in enumerate(items)]
            # else:
            items = [Item(str(i), item) for i, item in enumerate(items)]

        else:
            raise NotImplementedError()

        return items

    def infer_item_names(self, items) -> List[Item]:
        if items and isinstance(items[0].name, int) and 'name' in items[0].value:
            items = [Item(item.value['name'], item) for item in items]
        return items

    def update_prompt(self):
        if self.shell:
            path = '/'.join(self.path)
            prompt = [item for item in (path, '$ ') if item]
            self.shell.prompt = ' '.join(prompt)


obj = CRUD(ExampleContext)


def cd(*args):
    return obj.cd(*args)


def ls(*args):
    return [item.name for item in obj.ls(*args)]


def ll(*args):
    return obj.ll(*args)


def complete_cd(self, text, line, begidx, endidx):
    candidates = ls()
    return list(list_prefix_matches(text, candidates))


functions = {
    'cd': cd,
    'ls': ls,
    'll': ll,
    'tree': obj.tree
}
completions = {
    'cd': complete_cd
}

if __name__ == '__main__':
    set_functions(functions)
    set_completions(completions)

    obj.shell = Shell()
    obj.shell.set_do_char_method(obj.shell.do_cd, Options)

    run(obj.shell)
