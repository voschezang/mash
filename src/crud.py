#!/usr/bin/python3
from functools import partial
import logging
from pprint import pformat
from typing import Any, Dict, List

import crud_base
from crud_base import Item, Option, Options
from shell import build, set_completions, set_functions
from util import find_fuzzy_matches, find_prefix_matches, has_method, partial_no_args, partial_simple

# example data with dicts and lists
Data = Dict[str, Any]
cd_aliasses = 'cd_aliasses'


class CRUD(crud_base.BaseCRUD):
    def __init__(self, repository={}, **kwds):
        update = partial_no_args(update_prompt, self)
        super().__init__(cd_hooks=(self.fix_directory_type, update), **kwds)
        self.repository = repository

        self.init_shell()

        # reset path
        # TODO fix side-effects that require this hack
        self.cd()

    def init_shell(self, *build_args, **build_kwds):
        cls = build(*build_args, instantiate=False, **build_kwds)
        self.set_shell_functions(cls)
        self.set_shell_completions(cls)

        self.shell = cls()
        self.shell.set_do_char_method(self.cd, Options)

    def set_shell_functions(self, cls):
        # convert method to a function
        cd = partial_simple(self.cd)

        set_functions({'cd': cd,
                       'ls': partial(self.ll, delimiter=', '),
                       'll': self.ll,
                       'tree': self.tree},
                      cls)

    def set_shell_completions(self, cls):
        set_completions({'cd': self.complete_cd}, cls)

    def ls(self, obj=None) -> List[Item]:
        items = self._ls(obj)
        return self.wrap_list_items(items)

    def ll(self, obj=None, delimiter='\n') -> str:
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
        cwd = self.repository
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

        if Option.verify(dirs[0]):
            return dirs

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
        self.shell.remove_functions(cd_aliasses)

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

            cd_dirname = partial(self.cd, dirname)
            self.shell.add_functions({dirname: cd_dirname},
                                     group_key=cd_aliasses)

    def complete_cd(self, text, line, begidx, endidx):
        candidates = self.ll(delimiter=' ')
        return list(find_fuzzy_matches(text, candidates))


def update_prompt(crud: CRUD):
    # TODO ensure that this method is run after an exception
    # e.g. after cd fails
    path = '/'.join([str(a) for a in crud.path])
    prompt = [item for item in (path, '$ ') if item]
    crud.shell.prompt = ' '.join(prompt)

    crud.set_cd_aliases()
