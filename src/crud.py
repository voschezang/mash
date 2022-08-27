#!/usr/bin/python3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Callable, List, Tuple, Union
from util import find_prefix_matches, identity, is_callable, none


@dataclass
class Item:
    name: str
    value: object


class Option(Enum):
    default = ''
    root = ''
    home = '~'
    switch = '-'
    stay = '.'
    up = '..'


Options = [o.value for o in Option]


class CRUD(ABC):
    """CRUD operations that mimics a directory hierarchy.
    A directory (object) can consists folders and files (objects).
    """

    def __init__(self, path=[], options: Enum = Option, autocomplete=True,
                 cd_hooks: Tuple[Callable, Callable] = None):
        self.path = path
        self.prev_path = []
        self.autocomplete = autocomplete
        self.options = options

        self.pre_cd_hook = identity
        self.post_cd_hook = none

        if cd_hooks:
            for hook in cd_hooks:
                if hook and not is_callable(hook):
                    raise ValueError()

            pre, post = cd_hooks
            self.pre_cd_hook = pre
            self.post_cd_hook = post

    @abstractmethod
    def ls(self, obj: str) -> List[Item]:
        """List all properties of an object
        """
        pass

    # @abstractmethod
    def ensure(self, key: str, value):
        """Ensure that the object with reference `key` is set to `value`
        """
        pass

    def cd(self, *dirs):
        """Change the current working environment.
        E.g. cd(a,b,c) == cd a/b/c
        """
        dirs = self.pre_cd_hook(dirs)

        # handle empty args
        if dirs == ():
            dirs = (self.options.default.value,)

        available_dirs = [item.name for item in self.ls()]

        self.verify_cd_args(dirs, available_dirs)

        if len(dirs) > 0:
            directory = dirs[0]
            self._cd(directory, available_dirs)

        if len(dirs) > 1:
            # dirs = dirs[1:]
            # dirs = self.pre_cd_hook(dirs)
            self.cd(*dirs[1:])

        self.post_cd_hook()

    def _cd(self, directory, available_dirs):
        """Inner version of `self.cd`
        """
        if directory is None:
            directory = self.options.default.value

        try:
            option = Option(directory)
            self.handle_option(option)
            return
        except ValueError:
            pass

        # TODO if data = array, but directory = str, then infer the index

        if isinstance(directory, int):
            pass

        elif directory not in available_dirs:
            old_value = directory
            directory = next(find_prefix_matches(
                directory, available_dirs))
            logging.debug(f'expandig {old_value} into {directory}')
            logging.info((f'cd {directory}'))

        self.prev_path = self.path.copy()
        self.path.append(directory)

    def verify_cd_args(self, dirs, allowed_dirs):
        if not dirs or dirs[0] == '':
            return

        directory = dirs[0]

        if isinstance(dirs[0], int):
            assert dirs[0] < len(allowed_dirs)
            return

        if directory in allowed_dirs:
            return

        for option in self.options:
            if directory == option.value:
                return

        if self.autocomplete:
            if next(find_prefix_matches(directory, allowed_dirs)):
                return

        if directory not in allowed_dirs:
            print(f'cd: no such file or directory: {dirs[0]}')

        # Note that this assertion message won't relect all checks
        assert directory in allowed_dirs

    def handle_option(self, option: Enum):
        """Implementations of the standard chdir optionns

        E.g.
        ```sh
        cd .
        cd ..
        cd -
        cd ~
        ```
        """
        if option == self.options.home:
            option = self.options.root

        if option == self.options.root:
            self.prev_path = self.path.copy()
            self.path = []

        elif option == self.options.up:
            self.prev_path = self.path.copy()
            try:
                self.path.pop()
            except IndexError:
                pass

        elif option == self.options.switch:
            self.path, self.prev_path = self.prev_path, self.path

        # otherwise, pass
