#!/usr/bin/python3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Callable, List
from util import find_fuzzy_matches, find_prefix_matches, identity, none


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

    @staticmethod
    def verify(value):
        try:
            option = Option(value)
        except ValueError:
            # conversion failed means that `value` is not an Option
            return False
        return True


Options = [o.value for o in Option]
Path = List[str]


class CRUD(ABC):
    """CRUD operations that mimics a directory hierarchy.
    A directory (object) can consists folders and files (objects).
    """

    def __init__(self, path: Path = [], options: Enum = Option, autocomplete=True,
                 pre_cd_hook: Callable[[str], str] = identity, post_cd_hook=none):
        self.path: Path = path
        self.prev_path: Path = []
        self.autocomplete = autocomplete
        self.options = options

        self.pre_cd_hook = pre_cd_hook
        self.post_cd_hook = post_cd_hook

    @abstractmethod
    def ls(self, obj: str = None) -> List[Item]:
        """List all objects in a folder or all properties of an object
        """
        pass

    # @abstractmethod
    def ensure(self, key: str, value):
        """Ensure that the object with reference `key` is set to `value`
        """
        pass

    def cd(self, *dirs: str):
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
            self.cd(*dirs[1:])

        self.post_cd_hook()

    def _cd(self, directory, available_dirs):
        """Inner version of `self.cd`
        """
        if directory is None:
            directory = self.options.default.value

        if Option.verify(directory):
            option = Option(directory)
            self.handle_option(option)
            return

        if isinstance(directory, int):
            # TODO if data = array, but directory = str, then infer the index
            pass

        elif directory not in available_dirs:
            old_value = directory
            directory = next(find_prefix_matches(
                directory, available_dirs))
            logging.debug(f'expandig {old_value} into {directory}')
            logging.info((f'cd {directory}'))

        self.prev_path = self.path.copy()
        # append, but first copy to prevent side effects
        self.path = self.path + [directory]

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

    def wrap_list_items(self, items) -> List[Item]:
        if hasattr(items, 'keys'):
            items = [Item(k, v) for k, v in items.items()]

        elif isinstance(items, list):
            if items and 'name' in items[0]:
                items = [Item(item['name'], item) for item in items]
            else:
                items = [Item(str(i), item) for i, item in enumerate(items)]

        else:
            logging.warning(f'Error, NotImplementedError for {type(items)}')
            return []

        return items

    def infer_item_names(self, items) -> List[Item]:
        if items and isinstance(items[0].name, int) and 'name' in items[0].value:
            items = [Item(item.value['name'], item) for item in items]
        return items

    def infer_index(self, directory: str):
        names = [item.name for item in self.ls()]

        if directory not in names:
            logging.debug(f'Dir {directory} is not present in `ls()`')

        match = next(find_fuzzy_matches(directory, names))
        return names.index(match)

    def complete_cd(self, text, line, begidx, endidx):
        """Filter the result of `ls` to match `text`.
        """
        candidates = self.ll(delimiter=' ')
        return list(find_fuzzy_matches(text, candidates))
