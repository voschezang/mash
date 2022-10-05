#!/usr/bin/python3
import logging
from pprint import pformat
from typing import Any, Dict, List, Union

from crud import CRUD, Item, Option
from util import accumulate_list, find_prefix_matches

# example data with dicts and lists
Data = Union[Dict[str, Any], list]
cd_aliasses = 'cd_aliasses'


class StaticCRUD(CRUD):
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

    def _ls(self, obj, path=None) -> Data:
        cwd = self.get_cwd(path)
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
        return self.get_cwd()

    def get_cwd(self, path=None) -> Data:
        """Infer the current working directory
        """
        cwd = self.repository

        if path is None:
            path = self.path

        for directory in path:
            try:
                if isinstance(cwd, list):
                    directory = int(directory)
                cwd = cwd[directory]
            except (IndexError, KeyError):
                raise ValueError(f'Dir {directory} not in cwd ({cwd})')

        return cwd

    def wrap_list_items(self, items: Data) -> List[Item]:
        if hasattr(items, 'keys'):
            items = [Item(k, v) for k, v in items.items()]

        elif isinstance(items, list):
            if items and 'name' in items[0]:
                items = [Item(item['name'], item) for item in items]
            else:
                items = [Item(str(i), item) for i, item in enumerate(items)]

        else:
            logging.warning(f'Error, NotImplementedError for {type(items)}')
            return []

        return items

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

    def format_path(self) -> str:
        return '/'.join(self._iter_path())

    def _iter_path(self):
        for path in accumulate_list(self.path):
            value = path[-1]
            if isinstance(value, int):
                i = value
                item = self._ls(None, path)
                yield item['name']
            else:
                yield value
