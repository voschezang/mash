#!/usr/bin/python3
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
import logging
from pprint import pformat
from typing import Any, Dict, List

import crud
from crud import Item, Option, Options
from shell import Shell, run, set_completions, set_functions
from util import DataClassHelper, call, decorate, AdjacencyList, find_fuzzy_matches, find_prefix_matches, has_method


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


class CRUD(crud.CRUD):
    def __init__(self, context: dataclass, shell: Shell = None, **kwds):
        super().__init__(**kwds)
        self.init__context(context)
        self.shell = shell

        self.pre_cd_hook = self.fix_directory_type
        self.post_cd_hook = self.update_prompt

    def init__context(self, context: dataclass):
        # add helper methods
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
        return pformat(items, indent=2)

    def _ls(self, obj) -> Data:
        cwd = self.cwd
        if obj is None:
            # TODO fixme this may return a list instead of `Data`
            return cwd

        if self.autocomplete and obj not in cwd:
            obj = next(find_prefix_matches(obj, cwd.keys()))

        if obj in cwd:
            return cwd[obj]

        values = cwd.keys()
        msg = f'Error, {obj} is not in cwd ({values})'
        raise ValueError(msg)

    @property
    def cwd(self) -> Data:
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
            if items and 'name' in items[0]:
                items = [Item(item['name'], item)
                         for i, item in enumerate(items)]
            else:
                items = [Item(str(i), item) for i, item in enumerate(items)]

        else:
            logging.warning(f'Error, NotImplementedError for {type(items)}')
            return []

        return items

    def infer_item_names(self, items) -> List[Item]:
        if items and isinstance(items[0].name, int) and 'name' in items[0].value:
            items = [Item(item.value['name'], item) for item in items]
        return items

    def fix_directory_type(self, dirs: List[str]):
        """
        if cwd is a list, convert args to indices
        if cwd is a dict, do nothing
        """
        if len(dirs) == 0:
            return dirs

        try:
            option = Option(dirs[0])
            # never convert options
            return dirs
        except ValueError:
            pass

        directory = dirs[0]
        if isinstance(self.cwd, list):
            if directory.isdigit():
                directory = int(directory)
            else:
                directory = self.infer_index(directory)

        return (directory,) + dirs[1:]

    def infer_index(self, directory: str):
        names = [item.name for item in self.ls()]

        if directory not in names:
            logging.debug(f'Dir {directory} is not present in `ls()`')

        match = next(find_fuzzy_matches(directory, names))
        return names.index(match)

    def unset_cd_aliases(self):
        """Remove all custom do_{dirname} methods from self.shell.
        """
        self.shell.remove_functions('cd_aliasses')

    def set_cd_aliases(self):
        """Add do_{dirname} methods to self.shell for each sub-directory.
        """
        self.unset_cd_aliases()

        dirs = [item.name for item in self.ls()]
        self.shell.completenames_options = dirs

        for dirname in dirs:

            method_name = f'do_{dirname}'
            if has_method(self.shell, method_name):
                continue

            # TODO remove the double usage of `partial`
            cd = partial(call, partial(self.cd, dirname))

            self.shell.add_functions({dirname: cd}, group_key='cd_aliasses')

    def update_prompt(self):
        # TODO ensure that this method is run after an exception
        # e.g. after cd fails
        if self.shell:
            path = '/'.join([str(a) for a in self.path])
            prompt = [item for item in (path, '$ ') if item]
            self.shell.prompt = ' '.join(prompt)

        self.set_cd_aliases()


def init() -> CRUD:
    # TODO investigate why calling this function "setup" causes side-effects

    obj = CRUD(ExampleContext())

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

    cls = deepcopy(Shell)
    set_functions(functions, cls)
    set_completions(completions, cls)

    obj.shell = cls()
    obj.shell.set_do_char_method(obj.shell.do_cd, Options)

    # reset path
    # TODO fix side-effects that require this hack
    obj.shell.do_cd()

    return obj


if __name__ == '__main__':
    obj = init()
    run(obj.shell)
