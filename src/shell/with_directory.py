#!/usr/bin/python3
from functools import partial
from directory import Directory, Options
from directory.discoverable import DiscoverableDirectory

from shell.shell import build, set_completions, set_functions
from util import find_fuzzy_matches, has_method, partial_simple

cd_aliasses = 'cd_aliasses'


class ShellWithDirectory:
    def __init__(self, data={}, repository: Directory = None, **kwds):
        if repository is None:
            repository = DiscoverableDirectory(
                data, post_cd_hook=self.update_prompt, **kwds)

        self.repository = repository

        self.init_shell()

        # reset path
        self.repository.cd()

    def init_shell(self, *build_args, **build_kwds):
        cls = build(*build_args, instantiate=False, **build_kwds)
        self.set_shell_functions(cls)
        self.set_shell_completions(cls)

        self.shell = cls()
        self.shell.set_do_char_method(self.repository.cd, Options)

    def set_shell_functions(self, cls):
        # convert methods to functions
        cd = partial_simple(self.repository.cd)
        ls = partial_simple(self.repository.ll, delimiter=', ')
        ll = partial_simple(self.repository.ll)
        tree = partial_simple(self.repository.tree)

        set_functions({'cd': cd,
                       'ls': ls,
                       'll': ll,
                       'tree': tree
                       }, cls)

    def set_shell_completions(self, cls):
        set_completions({'cd': self.complete_cd}, cls)

    def unset_cd_aliases(self):
        """Remove all custom do_{dirname} methods from self.shell.
        """
        self.shell.remove_functions(cd_aliasses)

    def set_cd_aliases(self):
        """Add do_{dirname} methods to self.shell for each sub-directory.
        """
        self.unset_cd_aliases()

        # dirs = [item.name for item in self.crud.ls()]
        dirs = self.repository.ls()
        self.shell.completenames_options = dirs

        for dirname in dirs:

            method_name = f'do_{dirname}'
            if has_method(self.shell, method_name):
                continue

            cd_dirname = partial(self.repository.cd, dirname)
            self.shell.add_functions({dirname: cd_dirname},
                                     group_key=cd_aliasses)

    def update_prompt(self):
        # TODO ensure that this method is run after an exception
        # e.g. after cd fails
        # try:
        #     self.crud.semantic_path

        path = '/'.join(self.repository.semantic_path)

        prompt = [item for item in (path, '$ ') if item]
        self.shell.prompt = ' '.join(prompt)

        self.set_cd_aliases()

    def complete_cd(self, text, line, begidx, endidx):
        """Filter the result of `ls` to match `text`.
        """
        candidates = self.repository.ll(delimiter=' ')
        return list(find_fuzzy_matches(text, candidates))
