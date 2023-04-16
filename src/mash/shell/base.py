from collections import defaultdict
from dataclasses import asdict
from json import dumps, loads
from typing import Any, Callable, Dict, List
import logging

from mash.shell.cmd2 import Cmd2
from mash.filesystem.filesystem import FileSystem
from mash.filesystem.scope import Scope, show
from mash.io_util import log, print_shell_ready_signal
from mash.shell.grammer import delimiters
from mash.shell.grammer.delimiters import FALSE, IF, TRUE
from mash.shell.errors import ShellError
from mash.shell.function import LAST_RESULTS, LAST_RESULTS_INDEX, InlineFunction, scope
from mash.shell.function import ShellFunction as Function
from mash.shell.grammer.parsing import to_bool
from mash.util import has_method, identity


default_session_filename = '.shell_session.json'
default_function_group_key = '_'

ENV = 'env'
CHAR = 'char'

Command = Callable[[Cmd2, str], str]
FunctionGroup = Dict[str, Dict[str, Function]]


class BaseShell(Cmd2):
    """Extend Cmd with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrriden.

    Features:
    - An environment with local and global variable scopes.
    - Save/load sessions.
    - Decotion with functions, both at runtime and compile time.
    """

    def __init__(self, *args, env: Dict[str, Any] = None,
                 use_model=True,
                 save_session_prehook=identity,
                 load_session_posthook=identity, **kwds):
        """
        Parameters
        ----------
            env : dict
                Must be JSON serializable
        """
        super().__init__(*args, **kwds)
        self.use_model = use_model
        self.save_session_prehook = save_session_prehook
        self.load_session_posthook = load_session_posthook

        # fill this list to customize autocomplete behaviour
        self.completenames_options: List[Command] = []

        self._init_defaults(env)

        if self.auto_reload:
            self.try_load_session()

    def _init_defaults(self, env: Dict[str, Any]):
        self.ignore_invalid_syntax = True

        self.locals = FileSystem(scope())
        self.init_current_scope()

        self.env = Scope(self.locals, ENV)
        self.env[LAST_RESULTS] = []
        self.env[LAST_RESULTS_INDEX] = 0

        if env:
            for k, v in env.items():
                self.env[k] = v

        self.auto_save = False
        self.auto_reload = False

        self.function_groups: FunctionGroup = defaultdict(dict)

        # internals
        self._default_method = identity

    def init_current_scope(self):
        self.locals.set(IF, [])
        self.locals.set(ENV, {})

    @property
    def delimiters(self):
        """Return the most recent values of the delimiters.
        """
        items = delimiters.all.copy()
        items.remove('=')
        items.remove('#')
        return items

    @property
    def _last_if(self):
        return self.locals[IF][-1]

    @property
    def _last_results(self):
        return self.env[LAST_RESULTS]

    @property
    def _last_results_index(self):
        return self.env[LAST_RESULTS_INDEX]

    def _save_result(self, value):
        logging.debug(f'_save_result [{self._last_results_index}]: {value}')

        if len(self._last_results) < self._last_results_index:
            raise ShellError('Invalid state')
        if len(self._last_results) == self._last_results_index:
            self._last_results.append(None)

        self._last_results[self._last_results_index] = value

    def is_hidden_function(self, k: str) -> bool:
        """Check whether `k` is an existing function.
        """
        return any(k in keys for keys in self.function_groups.values())

    def is_special_function(self, k: str) -> bool:
        """Check whether `char` is a special characters method
        """
        return k in self.function_groups[CHAR]

    def is_function(self, k: str) -> bool:
        """Check whether `k` is an existing function. 
        """
        return has_method(self, f'do_{k}') \
            or self.is_hidden_function(k) \
            or self.is_inline_function(k) \
            or k in '!?'

    def is_inline_function(self, k: str) -> bool:
        """Check whether `k` is an existing inline (user-defined) function. 
        """
        return k in self.env and isinstance(self.env[k], InlineFunction)

    def run_commands(self, ast: str, prev_result='', run=False):
        raise NotImplementedError()

    ############################################################################
    # Commands: do_*
    ############################################################################

    def do_unset(self, args: str):
        """Unset keys
        `unset [KEY [KEY..]]
        """
        for k in args.split(' '):
            if k in self.env:
                del self.env[k]
            else:
                logging.warning('Invalid key')

        return ''

    def do_int(self, args: str) -> str:
        self._save_result(int(args))
        return ''

    def do_float(self, args: str) -> str:
        self._save_result(float(args))
        return ''

    def do_bool(self, args: str) -> str:
        self._save_result(args != FALSE)
        return ''

    def do_not(self, args: str) -> str:
        # TODO mv to shell.model
        return FALSE if to_bool(args) else TRUE

    def do_env(self, keys: str):
        """Retrieve environment variables.
        Return all variables if no key is given.
        """
        if not keys:
            return filter_private_keys(self.env.asdict())

        try:
            return {k: self.env[k] for k in keys.split()}
        except KeyError:
            log('Invalid key')

    def do_save(self, _):
        """Save the current session.
        """
        self.save_session()

    def do_reload(self, _):
        """Reload the current session.
        """
        self.try_load_session()

    def do_undo(self, _):
        """Undo the previous command
        """
        if not self.lastcmd:
            return

        f = self.lastcmd.split()[0]

        method = f'undo_{f}'
        if has_method(self, f'undo_{f}'):
            return getattr(self, method)()

        raise NotImplementedError()

    def last_method(self):
        """Find the method corresponding to the last command run in `shell`.
        It has the form: do_{cmd}

        Return a the last method if it exists and None otherwise.
        """
        # TODO integrate this into Shell and store the last succesful cmd

        if not self.lastcmd:
            return

        cmd = self.lastcmd.split()[0]
        return BaseShell.get_method(cmd)

    @staticmethod
    def get_method(method_suffix: str):
        method_name = f'do_{method_suffix}'
        if not has_method(BaseShell, method_name):
            return

        method = getattr(BaseShell, method_name)

        if isinstance(method, Function):
            return method.func

        return method

    def add_special_function(self, char: str, method: Command):
        # TODO merge this with self.add_functions
        if char in delimiters.all or char in '!?':
            raise ShellError(f'Char {char} is already in use.')

        self.add_functions({char: method}, CHAR)

    def run_special_function(self, k: str, args):
        return self.function_groups[CHAR][k](*args)

    def run_hidden_function(self, k: str, args):
        for group in self.function_groups.values():
            if k in group:
                return group[k](*args)

        raise ShellError(f'Unknown function: {k}')

    def add_functions(self, functions: Dict[str, Function], group_key=None):
        """Add functions to this instance at runtime.
        Use a key to select a group of functions
        """
        if group_key is None:
            group_key = default_function_group_key

        for key, func in functions.items():
            if hasattr(self, f'do_{key}'):
                logging.debug('Warning: overriding self.do_{key}')

            self.function_groups[group_key][key] = func

    def remove_functions(self, group_key=None):
        """Remove functions to this instance at runtime.
        Use a key to select a group of functions
        """
        if group_key is None:
            group_key = default_function_group_key

        if group_key in self.function_groups:
            del self.function_groups[group_key]

    ############################################################################
    # Overrides
    ############################################################################

    def postcmd(self, stop, _):
        """Display the shell_ready_signal to indicate termination to a parent process.
        """
        if self.auto_save and self.env:
            try:
                self.save_session()
            except OSError as e:
                log('Autosave: Cannot save session '
                    f'{default_session_filename}: {e}')

        print_shell_ready_signal()
        return stop

    ############################################################################
    # Persistency: Save/load sessions to disk
    ############################################################################

    def save_session(self, session=default_session_filename):
        self.save_session_prehook()

        if not self.env:
            logging.info('No env data to save')
            return

        self.reset_locals()
        env = filter_private_keys(self.locals[ENV])

        with open(session, 'w') as f:
            try:
                json = dumps(env)
            except TypeError:
                logging.debug('Cannot serialize self.env')
                try:
                    json = dumps(env)
                except TypeError as e:
                    logging.debug(e)
                    json = dumps(asdict(env))

            f.write(json)

    def reset_locals(self):
        self.locals.cd()

    def try_load_session(self, session=default_session_filename):
        self.load_session(session, strict=False)

    def load_session(self, session: str = None, strict=True):
        try:
            with open(session) as f:
                data = f.read()

        except OSError as e:
            if strict:
                raise ShellError(e)

            log(f'Session file not found: {session}: {e}')
            return

        if not data:
            logging.info('No env data found')
            return

        env = loads(data)

        self.reset_locals()
        log(f'Using session: {session}')
        print('Env')
        show(env, when=is_public)

        # TODO handle key conflicts
        self.env.update(env)

        self.load_session_posthook()


def is_public(key: str) -> bool:
    return not is_private(key)


def is_private(key: str) -> bool:
    return key.startswith('_')


def filter_private_keys(env: dict) -> dict:
    env = env.copy()
    for k in list(env.keys()):
        if is_private(k):
            del env[k]
    return env
