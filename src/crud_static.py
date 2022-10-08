#!/usr/bin/python3
import logging
from pprint import pformat
from typing import Any, Dict, List, Union

from crud import CRUD, CRUDError, Item, Option, Path
from util import accumulate_list, find_prefix_matches

# example data with dicts and lists
Data = Union[Dict[str, Any], list]
cd_aliasses = 'cd_aliasses'


class StaticCRUD(CRUD):
    def __init__(self, repository={}, **kwds):
        super().__init__(pre_cd_hook=self.fix_directory_type, **kwds)
        self.repository = repository

    def ls_absolute(self, path: Path = []) -> List[Item]:
        items = self._ls(path)
        return self.wrap_list_items(items)

    def ls_str(self, obj: str = None) -> List[Item]:
        items = self.ls_inner(obj)
        return self.wrap_list_items(items)

    def ll(self, obj=None, delimiter='\n') -> str:
        items = self.infer_item_names(self.ls_str(obj))
        return delimiter.join([str(item.name) for item in items])

    def tree(self, obj=None):
        items = self.ls_inner(obj)
        return pformat(items, indent=2)

    def ls_inner(self, obj: str = None, path=None) -> Data:
        if path is None:
            path = self.path

        if obj is not None:
            path = path + [obj]

        return self._ls(path)

    def _ls(self, path: Path = None) -> Data:
        obj = None
        if path:
            obj = path[-1]
            path = path[:-1]

        # TODO handle indices AND .name fields
        cwd = self.get_cwd(path)

        if obj is None:
            # TODO fixme this may return a list instead of `Data`
            return cwd

        if isinstance(obj, str) and obj.isdigit():
            raise ValueError('-')
        if isinstance(cwd, list) and isinstance(obj, int):
            return cwd[int(obj)]

        # do a fuzzy search
        if self.autocomplete and obj not in cwd:
            if isinstance(cwd, dict):
                keys = cwd.keys()
            else:
                keys = [k['name'] for k in cwd]

            obj = next(find_prefix_matches(str(obj), keys))

        # do an exact search
        if obj in cwd:
            if isinstance(cwd, dict):
                return cwd[obj]

            i = cwd.find(obj)
            return cwd[i]

        values = cwd.keys()
        msg = f'Error, {obj} is not in cwd ({values})'
        raise ValueError(msg)

    @property
    def cwd(self) -> Data:
        """Infer the current working directory
        """
        return self.get_cwd(self.path)

    def get_cwd(self, path: Path = []) -> Data:
        """Infer the current working directory
        """
        cwd = self.repository

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

        directory = str(dirs[0])
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
                item = self.ls_inner(None, path)
                yield item['name']
            else:
                yield value
