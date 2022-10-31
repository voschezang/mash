#!/usr/bin/python3
from typing import Callable,  Union
from copy import deepcopy
from directory.view import Key, View

from util import has_annotations, has_method, infer_inner_cls, is_Dict, is_Dict_or_List, is_callable
from directory import Directory


Method = Union[Callable, str]


class DiscoverableDirectory(Directory):
    def __init__(self, *args,
                 get_values_method: Method = 'get_all',
                 get_value_method: Method = 'get_value', **kwds):

        self.get_values_method = get_values_method
        self.get_value_method = get_value_method

        super().__init__(*args, get_hook=self.discover, **kwds)

    def discover(self, k: Key, cwd: View = None):
        if cwd is None:
            cwd = self.state

        k, initial_value = cwd.get(k)
        data = self.infer_data(k, initial_value)

        if data != initial_value:
            cwd.tree[k] = data
        return k

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
        path = list(self.path) + [k]
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
