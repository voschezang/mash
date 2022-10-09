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
        items = self.ls_absolute_inner(path)
        return self.infer_item_names(items)

    def ll(self, *path: str, delimiter='\n') -> str:
        if path:
            items = self.ls(path)
        else:
            items = self.ls()

        return delimiter.join([str(item.name) for item in items])

    def tree(self, obj=None):
        path = self.path
        if obj is not None:
            path = path + [obj]

        items = self.ls_with_defaults(obj)
        return pformat(items, indent=2)

    def ls_absolute_inner(self, path: Path = None) -> Data:
        self.filter_path(path)

        contents = self.repository

        for directory in path:
            contents = self.infer_data(path, contents)
            try:
                if isinstance(contents, list) and isinstance(directory, int):
                    # directory = int(directory)
                    contents = contents[directory]
                    continue

                # do a fuzzy serach
                if self.autocomplete and directory not in contents:
                    if isinstance(contents, dict):
                        keys = contents.keys()
                    else:
                        keys = [k[CRUD.NAME] for k in contents]

                    directory = next(find_prefix_matches(str(directory), keys))

                # do an exact search
                if directory not in contents:
                    values = contents.keys() if isinstance(contents, dict) else contents
                    msg = f'Error, {directory} is not in cwd ({values})'
                    raise ValueError(msg)

                if isinstance(contents, dict):
                    contents = contents[directory]
                else:
                    i = contents.find(directory)
                    contents = contents[i]
                continue

            except (IndexError, KeyError):
                raise ValueError(f'Dir {directory} not in cwd ({contents})')

        contents = self.infer_data(path, contents)
        return contents

    def infer_data(self, path: Path, data) -> Data:
        if isinstance(data, type):
            if has_method(data, 'get_all'):
                items = data.get_all(path)
                data = [Item(k, None) for k in items]
            else:
                data = data.__annotations__
        return data

    def infer_item_names(self, items: Data) -> List[Item]:
        if hasattr(items, 'keys'):
            items = [Item(k, v) for k, v in items.items() if k != CRUD.NAME]

        elif isinstance(items, list):
            if items and CRUD.NAME in items[0]:
                items = [Item(item[CRUD.NAME], item) for item in items]
            else:
                items = [Item(item, None) for item in items]

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
        cwd = self.ls_absolute_inner(self.path)
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
                item = self.ls_absolute_inner(path)
                # item = self.ls_inner(None, path)
                # TODO verify that item is not a list
                yield item[CRUD.NAME]
            else:
                yield value
