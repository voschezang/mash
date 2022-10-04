#!/usr/bin/python3
from functools import partial
from pprint import pformat
from typing import Any, Dict, List

from crud_base import BaseCRUD, Item, Option, Options
from shell import build, set_completions, set_functions
from util import find_prefix_matches, has_method, partial_simple

# example data with dicts and lists
Data = Dict[str, Any]
cd_aliasses = 'cd_aliasses'


class StaticCRUD(BaseCRUD):
    def __init__(self, repository={}, **kwds):
        super().__init__(pre_cd_hook=self.fix_directory_type, **kwds)
        self.repository = repository

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

    def fix_directory_type(self, dirs: List[str]):
        """
        if dirs is a list, convert args to indices
        if dirs is a dict, do nothing
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
