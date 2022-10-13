#!/usr/bin/python3
from copy import deepcopy
import logging
from pprint import pformat
from typing import Any, Callable, Dict, List, Union

from crud import CRUD, Item, Option, Path
from util import accumulate_list, find_prefix_matches, has_method, is_callable

# example data with dicts and lists
Data = Union[Dict[str, Any], list]
Method = Union[Callable, str]

cd_aliasses = 'cd_aliasses'


class StaticCRUD(CRUD):
    def __init__(self, repository={},
                 get_all_method: Method = 'get_all',
                 get_value_method: Method = 'get_value', **kwds):
        super().__init__(pre_cd_hook=self.fix_directory_type, **kwds)

        self.get_all_method = get_all_method
        self.get_value_method = get_value_method

        self.root = None
        self.repository = repository

    def ls_absolute(self, path: Path = []) -> List[Item]:
        items: Data = self.ls_absolute_inner(path)

        if isinstance(items, str):
            return [Item(items, None)]

        return self.infer_item_names(items)

    def tree(self, obj=None):
        path = self.path
        if obj is not None:
            path = path + [obj]

        items = self.ls_with_defaults(obj)
        return pformat(items, indent=2)

    def ls_absolute_inner(self, path: Path = None) -> Data:
        self.filter_path(path)

        # maintain a tree that represents self.repostiory
        cache_repository = True

        if cache_repository and self.root:
            contents = self.root
        else:
            contents = self.infer_data(self.repository, [])
            self.root = contents

        tree = self.root

        for i, directory in enumerate(path):
            if cache_repository and directory in tree and isinstance(tree[directory], dict):
                contents = tree[directory]

                # update tree
                tree[path[i]] = contents
                # iterate tree
                tree = tree[path[i]]
                continue

            try:
                if isinstance(contents, str):
                    raise IndexError()

                contents = get_item(contents, directory, self.autocomplete)

            except (IndexError, KeyError):
                raise ValueError(
                    f'Item {directory} not in directory ({contents})')

            contents = self.infer_data(contents, path)

            if cache_repository:
                # update tree
                tree[directory] = contents
                # iterate tree
                tree = tree[directory]

        return contents

    def infer_data(self, data: Union[Data, str], path: Path) -> Data:
        use_dict = True
        cls = data
        method = self.get_value_method

        # infer element types for Dict and List containers
        if hasattr(data, '_name'):
            if getattr(data, '_name') == 'Dict':
                cls = data.__args__[1]
                method = self.get_all_method
            elif getattr(data, '_name') == 'List':
                cls = data.__args__[0]
                method = self.get_all_method
                use_dict = False

        if is_callable(self.get_value_method):
            return self.get_value_method(data)

        if not isinstance(cls, type):
            return data

        if has_method(cls, method):
            return self.get_items(cls, method, path, use_dict)

        elif hasattr(cls, '__annotations__'):
            return cls.__annotations__

        return data

    def get_items(self, cls: type, method: str, path: Path, use_dict: bool):
        items = getattr(cls, method)(path)

        if hasattr(cls, '__annotations__'):
            cls = cls.__annotations__

        if use_dict:
            # assume that all keys are unique
            items = {k: deepcopy(cls) for k in items}

        return items

    def infer_item_names(self, items: Data) -> List[Item]:
        if has_method(items, 'keys') and not isinstance(items, type):
            # print(items)
            try:
                items2 = [Item(k, v)
                          for k, v in items.items() if k != CRUD.NAME]
            except (TypeError, AttributeError):
                x = 1
                x = 1
            items = [Item(k, v) for k, v in items.items() if k != CRUD.NAME]

        elif isinstance(items, list):
            if items and hasattr(items[0], CRUD.NAME):
                pass
            elif items and CRUD.NAME in items[0]:
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


def get_item(contents: Data, directory: str, autocomplete: bool) -> Data:
    if isinstance(contents, list) and isinstance(directory, int):
        return contents[directory]

    # do a fuzzy search
    if autocomplete and directory not in contents:
        if isinstance(contents, dict):
            keys = contents.keys()
        else:
            # TODO rm this branch
            keys = [k.name for k in contents]

        directory = next(find_prefix_matches(str(directory), keys))

    # do an exact search
    if directory not in contents:
        values = contents.keys() if isinstance(contents, dict) else contents
        msg = f'Error, {directory} is not in cwd ({values})'
        raise ValueError(msg)

    if isinstance(contents, dict):
        return contents[directory]

    i = contents.index(directory)
    return contents[i]
