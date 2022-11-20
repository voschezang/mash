#!/usr/bin/python3
from pickle import dumps, loads
from typing import Callable,  Union
from copy import deepcopy

from util import has_annotations, has_method, infer_inner_cls, is_Dict, is_Dict_or_List, is_callable
from filesystem import FileSystem
from filesystem.view import Path, Key, View


Method = Union[Callable, str]

default_snapshot_filename = '.snapshot.pickle'


class Discoverable(FileSystem):
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

    def discover(self, k: Key, cwd: View = None):
        if k is None:
            if not cwd.path:
                # TODO use k = '/'
                return

            k = cwd.up()

        elif cwd is None:
            cwd = self.state

        k, initial_value = cwd.get(k)

        # TODO ensure that keys cannot contain '/'
        # TODO handle edge cases of abs/rel/None paths
        initial_values_key = '/'.join([str(v) for v in cwd.path + [k]])

        data = self.infer_data(k, initial_value, initial_values_key)

        if data != initial_value:
            # TODO ensure view.state and view.prev are consistent; update traces
            cwd.tree[k] = data

            if initial_values_key not in self.initial_values:
                self.initial_values[initial_values_key] = initial_value

        return k

    def show(self, path: Path = None):
        # TODO keys in path are not autocompleted
        if path is None:
            path = self.full_path[1:]
        else:
            path = self.full_path[1:] + list(path)

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
                    self.get(path + [k, child_key, grand_child_key],
                             relative=False)

        if len(self.full_path) <= 1:
            return data

        p = '/'.join(path)
        if p in self.initial_values:
            cls = self.initial_values[p]
            if has_method(cls, 'show'):
                return cls.show(data)

        return data

    def infer_data(self, k: Key, initial_value=None, initial_values_key: str = None):
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

        if initial_values_key and initial_values_key in self.initial_values:
            obj = self.initial_values[initial_values_key]
            cls = obj
            if is_Dict_or_List(cls):
                cls = infer_inner_cls(cls)

            if has_method(cls, 'refresh') and cls.refresh():
                # try again using a new initial value
                # TODO don't unnecessary override child values
                # e.g. instead limit updates to append
                # e.g. don't override data with initial_values
                return self.infer_data(k, obj, initial_values_key=None)

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

    def snapshot(self, filename=default_snapshot_filename) -> bytes:
        with open(filename, 'wb') as f:
            f.write(dumps((self.root, self.initial_values, self.home)))

    def load(self, filename=default_snapshot_filename):
        print('load', filename)
        with open(filename, 'rb') as f:
            root, self.initial_values, home = loads(f.read())

        self.__init__(root=root, home=home)
