#!/usr/bin/python3
from dataclasses import _MISSING_TYPE
from pickle import dumps, loads
from typing import Callable,  Union
from copy import deepcopy

from mash.util import has_annotations, has_method, infer_inner_cls, is_Dict, is_Dict_or_List
from mash.filesystem.filesystem import FileSystem
from mash.filesystem.view import Data, Path, Key, View


Method = Union[Callable[[FileSystem, Key, Data, View], Data], str]

default_snapshot_filename = '.snapshot.pickle'


class Discoverable(FileSystem):
    def __init__(self, *args,
                 get_value_method: Method = None,
                 **kwds):
        self.get_value_method = get_value_method
        self.initial_values = {}

        super().__init__(*args, get_hook=self.discover, **kwds)

    def snapshot(self, filename=default_snapshot_filename) -> bytes:
        with open(filename, 'wb') as f:
            f.write(dumps((self.root, self.initial_values, self.home)))

    def load(self, filename=default_snapshot_filename):
        print('load', filename)
        with open(filename, 'rb') as f:
            root, self.initial_values, home = loads(f.read())

        self.__init__(root=root, home=home)

    def discover(self, k: Key, cwd: View = None):
        if cwd is None:
            cwd = self.cwd

        if k is None:
            if cwd.path:
                k = cwd.up()
            else:
                return

        k, initial_value = cwd.get(k)
        observed_value = self.observe(k, initial_value, cwd)
        self.save_observed_value(k, initial_value, observed_value, cwd)
        return k

    def undiscover(self, k: Key = None, cwd: View = None):
        if cwd is None:
            cwd = self.cwd

        if k is None:
            if cwd.path:
                k = cwd.up()
            else:
                return

        initial_values_key = infer_initial_value_key(k, cwd)
        if initial_values_key in self.initial_values:
            initial_value = self.initial_values[initial_values_key]
            # cwd.set(k, initial_value)
            self.set(k, initial_value, cwd)

    def reset(self, *path: str):
        if not path:
            self.undiscover()
            return

        cwd: View = self.cwd
        k, *parents = path

        for parent in parents:
            path.cd(parent)

        self.undiscover(k, cwd)

    def observe(self, k: Key, initial_value=None, cwd: View = None):
        if self.get_value_method:
            return self.get_value_method(self, k, initial_value, cwd)

        return initial_value

    def save_observed_value(self, k: Key, initial_value=None, observed_value=None, cwd: View = None):
        if observed_value == initial_value:
            return

        # TODO ensure repository.state and repository.prev are consistent; update traces
        cwd.set(k, observed_value)

        initial_values_key = infer_initial_value_key(k, cwd)
        if initial_values_key not in self.initial_values:
            self.initial_values[initial_values_key] = initial_value

    def show(self, *path: str):
        # TODO keys in path are not autocompleted
        if path == ((),):
            path = self.full_path[1:]
        else:
            path = self.full_path[1:] + list(path)

        data = self.observe_child_fields(path)

        if len(self.full_path) <= 1:
            return data

        p = '/'.join(path)
        if p in self.initial_values:
            cls = self.initial_values[p]
            if has_method(cls, 'show'):
                return cls.show(data)

        return data

    def observe_child_fields(self, path: Path):
        data = self.get(path, relative=False)

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

        return data


def observe(repository: FileSystem, k: Key, initial_value=None, cwd: View = None):
    data = initial_value

    # infer element types for Dict and List containers
    if is_Dict_or_List(data):
        container_cls = dict if is_Dict(data) else list
        cls = infer_inner_cls(data)
    else:
        container_cls = None
        cls = data

    if isinstance(cls, type):
        return discover_using_cls(cls, k, container_cls, repository.full_path)

    initial_values_key = '/'.join([str(v) for v in cwd.path + [k]])

    if initial_values_key and initial_values_key in repository.initial_values:
        obj = repository.initial_values[initial_values_key]
        cls = obj
        is_directory = is_Dict(cls)
        if is_Dict_or_List(cls):
            cls = infer_inner_cls(cls)

        if has_method(cls, 'refresh') and cls.refresh():
            # try again using a new initial value
            # TODO don't unnecessary override child values
            # e.g. instead limit updates to append
            # e.g. don't override data with initial_values
            new_data = observe(repository, k, obj, initial_values_key=None)

            if not is_directory:
                return new_data

            # add new values
            for k in new_data:
                # skip values that have not been changed
                # assume data[k] == new_data[k]
                if k not in data:
                    data[k] = new_data[k]

            # rm absent values
            for k in data:
                if k not in new_data:
                    del data[k]

    return data


def discover_using_cls(cls: type, k: Key, container_cls: type, full_path):
    path = full_path + [k]
    if container_cls is dict or container_cls is list:
        method = 'get_all'
    else:
        method = 'get_value'

    if has_method(cls, method):
        items = getattr(cls, method)(path)

        if container_cls is dict:
            return items
        elif container_cls is list:
            # assume that all keys are unique
            return {k: deepcopy(cls) for k in items}

        return items

    if has_annotations(cls):
        data = cls.__annotations__.copy()
        infer_defaults(cls, data)
        return data

    return cls()


def infer_defaults(cls: type, data: dict):
    if hasattr(cls, '__dataclass_fields__'):
        for k, v in cls.__dataclass_fields__.items():
            if not isinstance(v.default, _MISSING_TYPE):
                data[k] = v.default


def infer_initial_value_key(k: Key, cwd: View):
    # TODO ensure that keys cannot contain '/'
    # TODO handle edge cases of abs/rel/None paths
    return '/'.join([str(v) for v in cwd.path + [k]])
