#!/usr/bin/python3
import logging
from pprint import pformat
from typing import Any, Dict, List, Union

from crud import CRUD, Item, Option, Path
from util import accumulate_list, find_prefix_matches, has_method

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
        cwd = self.repository
        # cwd = self.infer_data(path, cwd)
        for directory in path:
            try:
                if isinstance(cwd, list) and isinstance(directory, int):
                    # directory = int(directory)
                    cwd = cwd[directory]
                    continue

                # do a fuzzy serach
                if self.autocomplete and directory not in cwd:
                    if isinstance(cwd, dict):
                        keys = cwd.keys()
                    else:
                        keys = [k[CRUD.NAME] for k in cwd]

                    directory = next(find_prefix_matches(str(directory), keys))

                # do an exact search
                if directory not in cwd:
                    values = cwd.keys() if isinstance(cwd, dict) else cwd
                    msg = f'Error, {directory} is not in cwd ({values})'
                    raise ValueError(msg)

                if isinstance(cwd, dict):
                    cwd = cwd[directory]
                else:
                    i = cwd.find(directory)
                    cwd = cwd[i]
                continue

            except (IndexError, KeyError):
                raise ValueError(f'Dir {directory} not in cwd ({cwd})')

        # cwd = self.infer_data(path, cwd)
        return cwd

    def infer_data(self, path, cwd):
        if isinstance(cwd, type):
            if has_method(cwd, 'get_all'):
                cwd = cwd.get_all(path)
            else:
                cwd = cwd.__annotations__
        return cwd

    def wrap_list_items(self, items: Data) -> List[Item]:
        if hasattr(items, 'keys'):
            items = [Item(k, v) for k, v in items.items() if k != CRUD.NAME]

        elif isinstance(items, list):
            if items and CRUD.NAME in items[0]:
                items = [Item(item[CRUD.NAME], item) for item in items]
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
        cwd = self._ls(self.path)
        if isinstance(cwd, list):
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
                yield item[CRUD.NAME]
            else:
                yield value
