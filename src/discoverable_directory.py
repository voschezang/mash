#!/usr/bin/python3
from typing import Callable,  Union
from copy import deepcopy
from crud import Path
from directory_view import Key, View

from util import has_method, is_callable
from directory import Directory


Method = Union[Callable, str]


class DiscoverableDirectory(Directory):
    def __init__(self, *args,
                 get_values_method: Method = 'get_all',
                 get_value_method: Method = 'get_value', **kwds):
        super().__init__(*args,
                         get_hook=self.discover,
                         #  get_hook=self.discover_value,
                         **kwds)

        self.get_values_method = get_values_method
        self.get_value_method = get_value_method

    def discover(self, k: Key, cwd: View = None):
        if cwd is None:
            cwd = self.state

        k, initial_value = cwd.get(k)

        data = self.infer_data(k, initial_value)
        if data != initial_value:
            cwd.tree[k] = data
            # TODO improve name
            cwd.tree['initial_value_of_' + k] = initial_value
        return k

    def infer_data(self, k: Key, initial_value=None):
        if initial_value is None:
            data = self.get([k])
        else:
            data = initial_value

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
            return self._get_values(cls, k, is_container, container_cls)

        return data

    def _get_values(self, cls: type, k: Key, is_container: bool, container_cls: type):
        path = list(self.path) + [k]
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
