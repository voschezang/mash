#!/usr/bin/python3
from typing import Callable,  Union
from copy import deepcopy

from util import has_annotations, has_method, infer_inner_cls, is_Dict, is_Dict_or_List, is_callable
from filesystem import FileSystem
from filesystem.view import Path, Key, View


Method = Union[Callable, str]


class DiscoverableDirectory(FileSystem):
    def __init__(self, *args,
                 get_values_method: Method = 'get_all',
                 get_value_method: Method = 'get_value', **kwds):

        self.get_values_method = get_values_method
        self.get_value_method = get_value_method

        # An index of initial values.
        # Storing this information in a separate index prevents the need for self.root to be mutable
        # TODO ensure that this index is updated if keys in self.state are renamed
        self.initial_values = {}

        super().__init__(*args, get_hook=self.discover, **kwds)

    def discover(self, k: Key, cwd: View = None, original_path: Path = None):
        if cwd is None:
            cwd = self.state

        k, initial_value = cwd.get(k)
        data = self.infer_data(k, initial_value)

        if data != initial_value:
            cwd.tree[k] = data

            # TODO ensure that keys cannot contain '/'
            # TODO handle edge cases of abs/rel/None paths
            if original_path is None:
                p = '/'.join(cwd.path + [k])
            else:
                p = '/'.join(original_path)

            self.initial_values[p] = initial_value

        return k

    def show(self, path: Path = None):
        # TODO keys in path are not autocompleted
        if path is None:
            path = self.full_path[1:]
            print('p1', path)
        #     data = self.get(path, relative=False)
        else:
            path = self.full_path[1:] + list(path)
            # path = list(path)
        #     print('p2', path)
        #     data = self.get(path)
        data = self.get(path, relative=False)

        # TODO refactor; create function discover_children(depth: int)
        for k in list(data.keys()):
            child = self.get(path + [k], relative=False)
            if not has_method(child, 'keys'):
                continue

            for child_key in list(child.keys()):
                grand_child = self.get(path + [k, child_key], relative=False)

                if not has_method(grand_child, 'keys'):
                    continue

                for grand_child_key in list(grand_child.keys()):
                    self.get(
                        path + [k, child_key, grand_child_key], relative=False)

        if len(self.full_path) <= 1:
            return data

        p = '/'.join(path)
        if p in self.initial_values:
            cls = self.initial_values[p]
            if has_method(cls, 'show'):
                return cls.show(data)

        return data

    def infer_data(self, k: Key, initial_value=None):
        if initial_value is None:
            data = self.get([k])
        else:
            data = initial_value

        if is_callable(self.get_value_method):
            return self.get_value_method(data)

        # infer element types for Dict and List containers
        if is_Dict_or_List(data):
            container_cls = dict if is_Dict(data) else list
            cls = infer_inner_cls(data)
        else:
            container_cls = None
            cls = data

        if isinstance(cls, type):
            return self._get_values(cls, k, container_cls)

        return data

    def _get_values(self, cls: type, k: Key, container_cls: type):
        path = list(self.full_path) + [k]
        if container_cls is dict or container_cls is list:
            method = self.get_values_method
        else:
            method = self.get_value_method

        if has_method(cls, method):
            items = getattr(cls, method)(path)

            if container_cls is dict:
                return items
            elif container_cls is list:
                # assume that all keys are unique
                return {k: deepcopy(cls) for k in items}

            return items

        if has_annotations(cls):
            return cls.__annotations__.copy()

        return cls
