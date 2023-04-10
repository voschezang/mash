from asyncio import CancelledError
import cmd
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import asdict
from itertools import repeat
from json import dumps, loads
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union
import logging
import shlex
import subprocess

from mash import io_util
from mash.filesystem.filesystem import FileSystem, cd
from mash.filesystem.scope import Scope, show
from mash.io_util import log, shell_ready_signal, print_shell_ready_signal, check_output
from mash.shell import delimiters
from mash.shell.delimiters import DEFINE_FUNCTION, FALSE, IF, TRUE
from mash.shell.errors import ShellError, ShellPipeError, ShellSyntaxError
from mash.shell.function import InlineFunction
from mash.shell.if_statement import Abort,  handle_prev_then_else_statements
from mash.shell.lex_parser import parse
from mash.shell.model import LAST_RESULTS, LAST_RESULTS_INDEX, ElseCondition, Indent, Lines, Map, Node, ReturnValue, Term, Terms
from mash.shell.parsing import filter_comments, quote_items, to_bool
from mash.util import has_method, identity, is_valid_method_name, quote_all


confirmation_mode = False
default_session_filename = '.shell_session.json'
default_prompt = '$ '

COMMENT = '#'
INNER_SCOPE = 'inner_scope'
RAW_LINE_INDENT = 'raw_line_indent'
ENV = 'env'

Command = Callable[[cmd.Cmd, str], str]
Types = Union[str, bool, int, float]


class Cmd(cmd.Cmd):
    """Extend CMD with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrriden.

    Features:
    - Confirmation mode to allow a user to accept or decline commands.
    - Error handling.
    """

    intro = 'Press ctrl-d to exit, ctrl-c to cancel, ? for help, ! for shell interop.\n' + \
        shell_ready_signal + '\n'

    prompt = default_prompt
    completenames_options = []

    def onecmd(self, lines: str) -> bool:
        """Parse and run `line`.
        Returns 0 on success and None otherwise
        """
        if lines == 'EOF':
            logging.debug('Aborting: received EOF')
            exit()

        try:
            lines = self.onecmd_prehook(lines)
            return self.onecmd_inner(lines)

        except ShellSyntaxError as e:
            if self.ignore_invalid_syntax:
                log(e)
            else:
                raise

        except CancelledError:
            pass

    def onecmd_inner(self, lines: str):
        return super().onecmd(lines)

    def onecmd_prehook(self, line):
        """Similar to cmd.precmd but executed before cmd.onecmd
        """
        if confirmation_mode:
            assert io_util.interactive
            log('Command:', line)
            if not io_util.confirm():
                raise CancelledError()

        return line

    def pipe_cmd_py(self, line: str, result: str):
        # append arguments
        line = f'{line} {result}'

        return super().onecmd(line)

    def completenames(self, text, *ignored):
        """Conditionally override Cmd.completenames
        """
        if self.completenames_options:
            return [a for a in self.completenames_options if a.startswith(text)]

        return super().completenames(text, *ignored)

    def none(self, _: str) -> str:
        """Do nothing. Similar to util.none.
        """
        return ''

    ############################################################################
    # Commands: do_*
    ############################################################################

    def do_shell(self, args):
        """System call
        """
        logging.info(f'Cmd = !{args}')
        return check_output(args)

    def do_fail(self, msg: str):
        raise ShellError(f'Fail: {msg}')


class BaseShell(Cmd):
    """Extend CMD with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrride.

    Features:
    - Parsing of multi-line and multi-segment commands.
        - Chain commands using pipes.
        - Interop between Python and e.g. Bash using pipes.
    - Parsing of single commands.
        - Set/unset variables, retrieve variable values.
    - Confirmation mode to allow a user to accept or decline commands.
    - Error handling.
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

        # internals
        self._char_methods = {}
        self._default_method = identity

    def init_current_scope(self):
        self.locals.set(IF, [])
        self.locals.set(ENV, {})

    @property
    def delimiters(self):
        """Return the most recent values of the delimiters.
        """
        items = delimiters.python + delimiters.bash
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

    def set_special_method(self, char: str, method: Command):
        if char in delimiters.all or char in '!?':
            raise ShellError(f'Char {char} is already in use.')

        self._char_methods[char] = method

    def run_special_method(self, k: str, *args):
        return self._char_methods[k](*args)

    def eval(self, args: List[str], quote=True) -> Types:
        """Evaluate / run `args` and return the result.
        """
        if quote:
            args = list(quote_items(args))

        args = list(filter_comments(args))

        if not args:
            return ''

        if not self.is_function(args[0]):
            args = ['echo'] + args

        k = '_eval_output'
        line = ' '.join(args)
        line = f'{line} -> {k}'

        with enter_new_scope(self):

            self.onecmd(line)

            # verify result
            if k not in self.env and not self._last_results:
                raise ShellError('eval() failed')

            result = self._retrieve_eval_result(k)

            if k in self.env:
                del self.env[k]

        return result

    def _retrieve_eval_result(self, k):
        if k in self.env:
            return self.env[k]

        elif self._last_results:
            return self._last_results.pop()

        raise RuntimeError('Cannot retrieve result')

    def _save_result(self, value):
        logging.debug(f'_save_result [{self._last_results_index}]: {value}')

        if len(self._last_results) < self._last_results_index:
            raise ShellError('Invalid state')
        if len(self._last_results) == self._last_results_index:
            self._last_results.append(None)

        self._last_results[self._last_results_index] = value

    def is_special_method(self, char: str) -> bool:
        """Check whether `char` is a special characters method. 
        """
        return char in self._char_methods

    def is_function(self, k: str) -> bool:
        """Check whether `k` is an existing function. 
        """
        return has_method(self, f'do_{k}') \
            or self.is_special_method(k) \
            or self.is_inline_function(k) \
            or k in '!?'

    def is_inline_function(self, k: str) -> bool:
        """Check whether `k` is an existing inline (user-defined) function. 
        """
        return k in self.env and isinstance(self.env[k], InlineFunction)

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

    def do_map(self, args=''):
        """Apply a function to every line.
        If `$` is present, then each line from stdin is inserted there.
        Otherwise each line is appended.

        Usage
        -----
        ```sh
        println a b |> map echo
        println a b |> map echo prefix $ suffix
        ```
        """
        log('Expected arguments')
        return ''

    def _do_foreach(self, ast: tuple, prev_results: str) -> Iterable:
        """Apply a function to every term or word.

        Usage
        ```sh
        echo a b |> foreach echo
        echo a b |> foreach echo prefix $ suffix
        ```
        """
        prev_results = '\n'.join(prev_results.split(' '))
        return Map.map(ast, prev_results, self, delimiter=' ')

    def foldr(self, commands: List[Term], prev_results: str, delimiter='\n'):
        items = parse(prev_results).values
        k, acc, *args = commands

        for item in items:
            command = Terms([k, acc] + args)
            acc = self.run_commands(command, item, run=True)

            if str(acc).strip() == '' and self._last_results:
                acc = self._last_results[-1]
                self.env[LAST_RESULTS] = []

        return acc

    def do_flatten(self, args: str) -> str:
        """Convert a space-separated string to a newline-separates string.
        """
        return '\n'.join(args.split(' '))

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
        return FALSE if to_bool(args) else TRUE

    ############################################################################
    # Overrides
    ############################################################################

    def onecmd_inner(self, lines: str):
        if not self.use_model:
            return super().onecmd_inner(lines)

        ast = parse(lines)
        if ast is None:
            raise ShellError('Invalid syntax: AST is empty')

        try:
            self.run_commands(ast, '', run=True)

        except ShellPipeError as e:
            if self.ignore_invalid_syntax:
                log(e)
                return

            raise ShellError(e)

        except subprocess.CalledProcessError as e:
            returncode, stderr = e.args
            log(f'Shell exited with {returncode}: {stderr}')

            if self.ignore_invalid_syntax:
                return

            raise ShellError(str(e))

    def run_commands(self, ast: Tuple, prev_result='', run=False):
        if isinstance(ast, Term):
            return ast.run(prev_result, shell=self, lazy=not run)

        elif isinstance(ast, str):
            return self.run_commands(Term(ast), prev_result, run=run)

        done = self._handle_define_function(ast)
        if done:
            return

        if not isinstance(ast, ElseCondition) and \
                not isinstance(ast, Indent) and \
                not isinstance(ast, Lines):
            try:
                handle_prev_then_else_statements(self)
            except Abort:
                return prev_result

        if isinstance(ast, Node):
            return ast.run(prev_result, shell=self, lazy=not run)
        else:
            raise NotImplementedError()

    def _handle_define_function(self, ast: Node) -> bool:
        if DEFINE_FUNCTION not in self.locals:
            return False

        # self._extend_inline_function_definition(line)
        f = self.locals[DEFINE_FUNCTION]

        if isinstance(ast, Indent):
            # TODO compare indent width
            width = ast.indent
            if ast.data is None:
                return True

            if f.line_indent is None:
                f.line_indent = width

            if width >= f.line_indent:
                self.locals[DEFINE_FUNCTION].inner.append(ast)
                return True

            self._finalize_define_function(f)

        elif not isinstance(ast, Lines):
            # TODO this will only be triggered after a non-Word command
            self._finalize_define_function(f)

        return False

    def _finalize_define_function(self, f):
        self.env[f.func_name] = f
        self.locals.rm(DEFINE_FUNCTION)
        self.prompt = default_prompt

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

    def default(self, line: str):
        # TODO move this
        if 1:
            head, *tail = line.split(' ')
            # TODO move InlineFunction logic to shell.model
            if head in self.env and isinstance(self.env[head], InlineFunction):
                f = self.env[head]
                try:
                    result = self.call_inline_function(f, *tail)
                except ShellError:
                    # reset local scope
                    self.reset_locals()
                    raise

                return result

        if self.ignore_invalid_syntax:
            return super().default(line)

        raise ShellSyntaxError(f'Unknown syntax: {line}')

    ############################################################################
    # Environment Variables
    ############################################################################

    def set_env_variable(self, k: str, *values: str):
        """Set the variable `k` to `values`
        """
        if not is_valid_method_name(k):
            raise ShellError(f'Invalid variable name format: {k}')

        log(f'set {k}')
        self.env[k] = ' '.join(values)
        return k

    def set_env_variables(self, keys: Union[str, List[str]], result: str):
        """Set the variables `keys` to the values in result.
        """
        if result is None:
            raise ShellError(f'Missing return value in assignment: {keys}')

        if isinstance(keys, str) or isinstance(keys, Term):
            keys = keys.split(' ')

        try:
            if len(result) == len(keys):
                self.env.update(items=zip(keys, result))
                return
        except TypeError:
            pass

        if len(keys) == 1:
            if isinstance(result, list):
                result = ' '.join(quote_all(result))
            self.env[keys[0]] = result
        elif isinstance(result, str) or isinstance(result, Term):
            lines = result.split('\n')
            terms = result.split(' ')
            if len(lines) == len(keys):
                self.env.update(items=zip(keys, lines))

            elif len(terms) == len(keys):
                self.env.update(items=zip(keys, terms))

            elif result == '':
                self.env.update(items=zip(keys, repeat('')))

        else:
            raise ShellError(
                f'Cannot assign values to all keys: {" ".join(keys)}')

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

    ############################################################################
    # Inline & Multiline Functions
    ############################################################################

    def call_inline_function(self, f: InlineFunction, *args: str):
        translations = {}

        if len(args) != len(f.args):
            msg = f'Invalid number of arguments: {len(f.args)} arguments expected.'
            if self.ignore_invalid_syntax:
                log(msg)
                return FALSE
            else:
                raise ShellError(msg)

        # translate variables in inline functions
        for i, k in enumerate(f.args):
            # quote item to preserve `\n`
            translations[k] = shlex.quote(args[i])

        with enter_new_scope(self):

            for i, k in enumerate(f.args):
                # quote item to preserve `\n`
                # self.env[k] = shlex.quote(args[i])
                self.env[k] = args[i]

            if f.inner == []:
                return self.run_commands(f.command, run=True)

            # TODO rm impossible state
            assert f.command == ''

            result = ''
            for ast in f.inner:
                result = self.run_commands(ast, prev_result=result,
                                           run=True)

                if isinstance(result, ReturnValue):
                    return result.data

            if isinstance(result, ReturnValue):
                return result.data

    def parse(self, results: str):
        return parse(results)


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


def scope() -> dict:
    return defaultdict(dict)


@contextmanager
def enter_new_scope(cls: BaseShell, scope_name=INNER_SCOPE):
    """Create a new scope, then change directory into that scope.
    Finally exit the new scope.
    """
    cls.locals.set(scope_name, scope())
    try:
        with cd(cls.locals, scope_name):
            cls.init_current_scope()
            yield
    finally:
        pass
