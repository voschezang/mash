
#!/usr/bin/python3
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Callable, Dict, Tuple
from util import find_prefix_matches, is_callable, none


class CRUD(ABC):
    """CRUD operations that mimics a directory hierarchy.
    A directory (object) can consists folders and files (objects).
    """

    def __init__(self, path=[], autocomplete=True, cd_hooks: Tuple[Callable, Callable] = None):
        self.path = path
        self.autocomplete = autocomplete

        self.pre_cd_hook = none
        self.post_cd_hook = none

        if cd_hooks:
            for hook in cd_hooks:
                if hook and not is_callable(hook):
                    raise ValueError()

            pre, post = cd_hooks
            self.pre_cd_hook = pre
            self.post_cd_hook = post

    @abstractmethod
    def ls(self, obj: str) -> list:
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
        self.pre_cd_hook()

        available_dirs = self.ls()
        self.verify_cd_args(dirs, available_dirs)

        if len(dirs) > 0:
            directory = dirs[0]
            self._cd(directory, available_dirs)

        if len(dirs) > 1:
            self.cd(dirs[1:])

        self.post_cd_hook()

    def _cd(self, directory, available_dirs):
        """Inner version of `self.cd`
        """
        if directory is None or directory == '':
            return
        if directory == '.':
            return
        elif directory == '..':
            self.path.pop()
            return

        if directory not in available_dirs:
            old_value = directory
            directory = next(find_prefix_matches(
                directory, available_dirs))
            logging.debug(f'expandig {old_value} into {directory}')
            logging.info((f'cd {directory}'))

        self.path.append(directory)

    def verify_cd_args(self, dirs, allowed_dirs):
        if not dirs or dirs[0] == '':
            return

        directory = dirs[0]
        if directory in ['..'] or directory in allowed_dirs:
            return

        if self.autocomplete:
            if next(find_prefix_matches(directory, allowed_dirs)):
                return

        if directory not in allowed_dirs:
            print(f'cd: no such file or directory: {dirs[0]}')

        # Note that this assertion message won't relect all checks
        assert directory in allowed_dirs
