from functools import partial

from mash.filesystem.filesystem import FileSystem, OPTIONS, Option
from mash.filesystem.discoverable import Discoverable
from mash.filesystem.view import Path
from mash.shell.shell import build, set_completions, set_functions
from mash.util import find_fuzzy_matches, has_method, partial_simple

cd_aliasses = 'cd_aliasses'
path_delimiter = '/'


class ShellWithFileSystem:
    def __init__(self, data={}, repository: FileSystem = None, **kwds):
        if repository is None:
            self.repository = Discoverable(
                data, post_cd_hook=self.update_prompt, **kwds)

        self.init_shell()

        # reset path
        self.repository.cd()

    def init_shell(self, *build_args, **build_kwds):
        cls = build(*build_args, instantiate=False, **build_kwds)
        self._set_shell_functions(cls)
        self.set_shell_completions(cls)

        self.shell = cls(save_session_prehook=self.repository.snapshot,
                         load_session_posthook=self.repository.load)
        self.shell.set_do_char_method(self.repository.cd, OPTIONS)

    def _set_shell_functions(self, cls):
        # convert methods to functions
        cd = partial_simple(self.repository.cd)
        ls = partial_simple(self.repository.ll, delimiter=', ')
        ll = partial_simple(self.repository.ll)
        get = partial_simple(self.get)
        set = partial_simple(self.set)
        new = partial_simple(self.new)
        tree = partial_simple(self.repository.tree)
        pwd = partial_simple(self.pwd)
        home = partial_simple(self.init_home)
        cp = partial_simple(self.repository.cp)
        mv = partial_simple(self.repository.mv)
        rm = partial_simple(self.repository.rm)
        # show = partial_simple(self.show)
        show = partial_simple(self.repository.show)
        reset = partial_simple(self.repository.reset)

        set_functions({'cd': cd,
                       'use': cd,
                       'list': ls,
                       'ls': ls,
                       'll': ll,
                       'get': get,
                       'set': set,
                       'new': new,
                       'tree': tree,
                       'pwd': pwd,
                       'home': home,
                       'cp': cp,
                       'mv': mv,
                       'rm': rm,
                       'show': show,
                       'reset': reset,
                       }, cls)

    def pwd(self):
        return ' '.join(self.repository.full_path)

    def get(self, *path: str):
        return self.repository.get(path)

    def set(self, *args: str):
        k, *values = args

        if len(values) == 1:
            self.repository.set(k, values[0])
        elif len(values) > 1:
            self.repository.set(k, values)

    def new(self, *keys: str):
        for k in keys:
            self.set(k, {})

    def init_home(self, *path: Path):
        self.repository.init_home(path)

    def set_shell_completions(self, cls):
        set_completions({'cd': self.complete_cd,
                         'mv': self.complete_cd,
                         'cp': self.complete_cd,
                         'rm': self.complete_cd,
                         'get': self.complete_cd,
                         'tree': self.complete_cd,
                         'show': self.complete_cd,
                         }, cls)

    def unset_cd_aliases(self):
        """Remove all custom do_{dirname} methods from self.shell.
        """
        self.shell.remove_functions(cd_aliasses)

    def set_cd_aliases(self):
        """Add do_{dirname} methods to self.shell for each sub-directory.
        """
        self.unset_cd_aliases()

        dirs = self.repository.ls()
        self.shell.completenames_options = dirs

        for dirname in dirs:
            method_name = f'do_{dirname}'
            if not has_method(self.shell, method_name):
                self.add_cd_alias(dirname)

    def add_cd_alias(self, dirname: str):
        # create alias
        cd_dirname = partial(self.repository.cd, dirname)
        cd_dirname.__name__ = f'{self.repository.cd.__name__}({dirname})'

        self.shell.add_functions({dirname: cd_dirname},
                                 group_key=cd_aliasses)

    def update_prompt(self):
        # TODO ensure that this method is run after an exception
        # e.g. after cd fails

        # abort in case of incomplete initiatlization
        if not hasattr(self, 'repository'):
            return

        semantic_path = self.repository.semantic_path

        if path_delimiter == Option.root.value:
            # avoid double '//' in path
            if semantic_path and semantic_path[0] == Option.root.value:
                semantic_path[0] = ''

        path = path_delimiter.join(semantic_path)

        prompt = [item for item in (path, '$ ') if item]
        self.shell.prompt = ' '.join(prompt)

        self.set_cd_aliases()

    def complete_cd(self, text, line, begidx, endidx):
        """Filter the result of `ls` to match `text`.
        """
        candidates = self.repository.ls()
        results = list(find_fuzzy_matches(text, candidates))

        if len(results) > 1:
            if results[0].startswith(text) and not results[1].startswith(text):
                return results[:1]

        return results
