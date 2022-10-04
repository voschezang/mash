#!/usr/bin/python3
from functools import partial
from pprint import pformat
from typing import Any, Dict, List

from crud_base import BaseCRUD, Item, Option, Options
from shell import build, set_completions, set_functions
from util import find_prefix_matches, has_method, partial_simple

# example data with dicts and lists
Data = Dict[str, Any]
cd_aliasses = 'cd_aliasses'


class StaticCRUD(BaseCRUD):
    def __init__(self, repository={}, **kwds):
        super().__init__(pre_cd_hook=self.fix_directory_type, **kwds)
        self.repository = repository
        # TODO
        # # reset path
        # self.cd()

    def ls(self, obj=None) -> List[Item]:
        items = self._ls(obj)
        return self.wrap_list_items(items)

    def ll(self, obj=None, delimiter='\n') -> str:
        items = self.infer_item_names(self.ls(obj))
        return delimiter.join([str(item.name) for item in items])

    def tree(self, obj=None):
        items = self._ls(obj)
        return pformat(items, indent=2)

    def _ls(self, obj) -> Data:
        cwd = self.cwd
        if obj is None:
            # TODO fixme this may return a list instead of `Data`
            return cwd

        if self.autocomplete and obj not in cwd:
            obj = next(find_prefix_matches(obj, cwd.keys()))

        if obj in cwd:
            return cwd[obj]

        values = cwd.keys()
        msg = f'Error, {obj} is not in cwd ({values})'
        raise ValueError(msg)

    @property
    def cwd(self) -> Data:
        """Infer the current working directory
        """
        cwd = self.repository
        for directory in self.path:
            try:
                if isinstance(cwd, list):
                    directory = int(directory)
                cwd = cwd[directory]
            except (IndexError, KeyError):
                raise ValueError(f'Dir {directory} not in cwd ({cwd})')

        return cwd

    def fix_directory_type(self, dirs: List[str]):
        """
        if dirs is a list, convert args to indices
        if dirs is a dict, do nothing
        """
        if len(dirs) == 0:
            return dirs

        if Option.verify(dirs[0]):
            return dirs

        directory = dirs[0]
        if isinstance(self.cwd, list):
            if directory.isdigit():
                directory = int(directory)
            else:
                directory = self.infer_index(directory)

        return (directory,) + dirs[1:]


class ShellWithCRUD:
    def __init__(self, repository={}, crud: BaseCRUD = None, **kwds):
        if crud is None:
            self.crud = StaticCRUD(
                repository, post_cd_hook=self.update_prompt, **kwds)

        self.init_shell()

        # reset path
        self.crud.cd()

    def init_shell(self, *build_args, **build_kwds):
        cls = build(*build_args, instantiate=False, **build_kwds)
        self.set_shell_functions(cls)
        self.set_shell_completions(cls)

        self.shell = cls()
        self.shell.set_do_char_method(self.crud.cd, Options)

    def set_shell_functions(self, cls):
        # convert method to a function
        cd = partial_simple(self.crud.cd)

        set_functions({'cd': cd,
                       'ls': partial(self.crud.ll, delimiter=', '),
                       'll': self.crud.ll,
                       'tree': self.crud.tree},
                      cls)

    def set_shell_completions(self, cls):
        set_completions({'cd': self.crud.complete_cd}, cls)

    def unset_cd_aliases(self):
        """Remove all custom do_{dirname} methods from self.shell.
        """
        self.shell.remove_functions(cd_aliasses)

    def set_cd_aliases(self):
        """Add do_{dirname} methods to self.shell for each sub-directory.
        """
        self.unset_cd_aliases()

        dirs = [item.name for item in self.crud.ls()]
        self.shell.completenames_options = dirs

        for dirname in dirs:

            method_name = f'do_{dirname}'
            if has_method(self.shell, method_name):
                continue

            cd_dirname = partial(self.crud.cd, dirname)
            self.shell.add_functions({dirname: cd_dirname},
                                     group_key=cd_aliasses)

    def update_prompt(self):
        # TODO ensure that this method is run after an exception
        # e.g. after cd fails
        path = '/'.join([str(a) for a in self.crud.path])
        prompt = [item for item in (path, '$ ') if item]
        self.shell.prompt = ' '.join(prompt)

        self.set_cd_aliases()
