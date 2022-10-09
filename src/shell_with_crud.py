#!/usr/bin/python3
from functools import partial

from crud import CRUD,  Options
from crud_static import StaticCRUD
from shell import build, set_completions, set_functions
from util import has_method, partial_simple

cd_aliasses = 'cd_aliasses'


class ShellWithCRUD:
    def __init__(self, repository={}, crud: CRUD = None, **kwds):
        if crud is None:
            crud = StaticCRUD(repository, post_cd_hook=self.update_prompt,
                              **kwds)

        self.crud = crud

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
        # convert methods to functions
        cd = partial_simple(self.crud.cd)
        ls = partial_simple(self.crud.ll, delimiter=', ')
        ll = partial_simple(self.crud.ll)
        tree = partial_simple(self.crud.tree)

        set_functions({'cd': cd,
                       'ls': ls,
                       'll': ll,
                       'tree': tree
                       }, cls)

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

        dirs = [item.name for item in self.crud.ls_str()]
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
        path = self.crud.format_path()

        prompt = [item for item in (path, '$ ') if item]
        self.shell.prompt = ' '.join(prompt)

        self.set_cd_aliases()
