#!/usr/bin/python3
from copy import copy, deepcopy
import logging
from pprint import pformat
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

from crud import CRUD, Item, Option, Path
from util import accumulate_list, find_prefix_matches, has_method, is_callable

# example data with dicts and lists
Data = Union[Dict[str, Any], list]
Method = Union[Callable, str]
Index = int
Key = [str, int]

cd_aliasses = 'cd_aliasses'


class StepTree(dict):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._trace: List[dict] = []

    def ls(self):
        return self.keys()

    def cd(self, key):
        self._trace.append(self.tree)
        self.tree = self.tree[key]

    def up(self):
        self.tree = self._trace.pop()


class Tree(dict):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.init_root()

    def init_root(self):
        self.tree = self

        self._trace: List[Tuple[Key, dict]] = []
        self._prev_trace = []

    def cwd(self) -> Path:
        return [k for k, _ in self._trace]

    @property
    def path(self):
        return self.cwd()

    def ls(self, *paths: Union[Path, str]) -> Iterable:
        if paths is None:
            yield from self.keys()
            return

        for path in paths:
            if isinstance(path, str):
                path = [path]

            yield from self.get(path)

    def get(self, path: Union[Path, str]):
        cwd = self.tree
        for k in path:
            cwd = cwd[k]
        return cwd

    def append(self, k, v):
        """Associate key k with value v and then change the working directory to k 
        """
        self.tree[k] = v
        self.cd(k)

    def cd(self, *path: Key):
        """
        cd a b c
        cd -
        """
        if path is None:
            return

        # cache current position
        origin = copy(self._trace)

        # change dirs
        for k in path:
            if Option.verify(k):
                self.handle_cd_option(Option(k))
            else:
                self._cd(k)

        # store origin
        self._prev_trace = origin

    def handle_cd_option(self, k):
        k = Option(k)
        if k == Option.switch:
            self._switch_traces()
            self._sync_traces()

        elif k == Option.up:
            self._up()
        return k

    def _up(self):
        _, self.tree = self._trace.pop()

    def _switch_traces(self):
        self._trace, self.prev_trace = self._prev_trace, self._trace

    def _sync_traces(self):
        _, self.tree = self._trace[-1]
        _, self.prev_tree = self._prev_trace[-1]

    def _cd(self, key: Key):
        self._trace.append((key, self.tree))
        self.tree = self.tree[key]

    def __repr__(self):
        return self.tree.__repr__()


class StaticCRUD(CRUD):
    def __init__(self, repository={},
                 get_values_method: Method = 'get_all',
                 get_value_method: Method = 'get_value', **kwds):
        super().__init__(pre_cd_hook=self.fix_directory_type, **kwds)

        self.get_values_method = get_values_method
        self.get_value_method = get_value_method

        self.tree = None
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

        if cache_repository and self.tree:
            self.tree.init_root()
            contents = self.tree
        else:
            contents = self.infer_data(self.repository, [])
            self.tree = Tree(**contents)

        for i, directory in enumerate(path):
            try:
                is_in_cache = cache_repository and \
                    directory in self.tree.ls() and \
                    isinstance(self.tree.get(directory), dict)
            except TypeError:
                raise ValueError(f'Value is not a directory: {self.tree}')

            if is_in_cache:
                contents = self.tree.get(directory)

            else:

                try:
                    if isinstance(contents, str):
                        raise ValueError(
                            'Value is not a directory: {contents}')

                    contents = get_item(contents, directory, self.autocomplete)

                except (IndexError, KeyError):
                    raise ValueError(
                        f'Item {directory} not in directory ({contents})')

                contents = self.infer_data(contents, path)

            if cache_repository:
                self.tree.append(directory, contents)

        return contents

    def infer_data(self, data: Union[Data, str], path: Path) -> Data:
        if is_callable(self.get_value_method):
            return self.get_value_method(data)

        cls = data
        is_container = False
        container_cls = None

        # infer element types for Dict and List containers
        if getattr(data, '_name', '') == 'Dict':
            cls = data.__args__[1]
            container_cls = dict
            is_container = True
        elif getattr(data, '_name', '') == 'List':
            cls = data.__args__[0]
            container_cls = list
            is_container = True

        if isinstance(cls, type):
            return self._get_values(cls, path, is_container, container_cls)

        return data

    def _get_values(self, cls: type, path: Path, is_container: bool, container_cls: type):
        method = self.get_values_method if is_container else self.get_value_method

        if has_method(cls, method):
            items = getattr(cls, method)(path)

            if container_cls is dict:
                return items
            elif container_cls is list:
                if hasattr(cls, '__annotations__'):
                    cls = cls.__annotations__

                # items = {i: v for i, v in enumerate(items)}

                # assume that all keys are unique
                return {k: deepcopy(cls) for k in items}

            return items

        if hasattr(cls, '__annotations__'):
            return cls.__annotations__

        return cls

    def infer_item_names(self, items: Data) -> List[Item]:
        if has_method(items, 'keys') and not isinstance(items, type):
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
                items = self.ls_absolute_inner(path)
                # TODO verify that item is not a list
                yield items[CRUD.NAME]
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
