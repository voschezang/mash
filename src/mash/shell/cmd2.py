from asyncio import CancelledError
import cmd
import logging
from pathlib import Path
import traceback

from mash import io_util
import cmd
from mash.io_util import log, read_file, shell_ready_signal, check_output
from mash.shell.errors import ShellError, ShellSyntaxError
import mash.shell.function as func

confirmation_mode = False
default_prompt = '$ '


class Cmd2(cmd.Cmd):
    """Extend cmd.Cmd with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrriden.

    Features:
    - Confirmation mode to allow a user to accept or decline commands.
    - Error handling.
    - I/O methods: cat, source, print, println, exit
    - String methods: echo, flatten
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

    def onecmd_raw(self, line: str, prev_result: str):
        line = f'{line} {prev_result}'
        return super().onecmd(line)

    def completenames(self, text, *ignored):
        """Conditionally override Cmd.completenames
        """
        if self.completenames_options:
            return [a for a in self.completenames_options if a.startswith(text)]

        return super().completenames(text, *ignored)

    def default(self, line: str):
        if self.ignore_invalid_syntax:
            return super().default(line)

        raise ShellSyntaxError(f'Unknown syntax: {line}')

    def none(self, _: str) -> str:
        """Do nothing. Similar to util.none.
        """
        return ''

    ############################################################################
    # Commands: do_*
    ############################################################################

    def do_shell(self, args):
        """System call.
        Alias for `!cmd`
        """
        logging.info(f'Cmd = !{args}')
        return check_output(args)

    def do_fail(self, msg: str):
        raise ShellError(f'Fail: {msg}')

    def do_exit(self, args):
        """exit [code]

        Wrapper for sys.exit(code) with default code: 0
        """
        if not args:
            args = 0

        exit(int(args))

    def do_E(self, args):
        """Show the last exception
        """
        traceback.print_exception(
            type(func.last_exception), func.last_exception, func.last_traceback)

    def do_print(self, args):
        """Write to stdout
        """
        logging.info(f'Cmd: print {args}')
        return args

    def do_println(self, args):
        """Write each word as a newline to stdout.
        """
        logging.info(f'Cmd: println {args}')
        return self.do_flatten(args)

    ############################################################################
    # Commands: do_* - File I/O
    ############################################################################

    def do_cat(self, filenames: str):
        """Concatenate and print files
        """
        return ''.join(cat_file(f) for f in filenames.split())

    def do_source(self, filenames: str):
        run_command(self.do_cat(filenames), self)

    ############################################################################
    # Commands: do_* - String Operations
    ############################################################################

    def do_echo(self, args):
        """Mimic Bash's print function.
        """
        logging.info(f'Cmd: echo {args}')
        return args

    def do_flatten(self, args: str) -> str:
        """Convert a space-separated string to a newline-separates string.
        """
        return '\n'.join(args.split(' '))

    def do_range(self, args: str) -> str:
        """range(start, stop, [step])
        """
        args = args.split(' ')
        args = (int(a) for a in args)
        return '\n'.join((str(i) for i in range(*args)))


################################################################################
# Run interface
################################################################################


def run_command(command: str, shell: Cmd2, strict=None):
    """Run a single command in using `shell`.

    Parameters
    ----------
        strict : bool
            Raise exceptions when encountering invalid syntax.
    """
    if strict is not None:
        shell.ignore_invalid_syntax = not strict

    for line in command.splitlines():
        if line:
            shell.onecmd(line)


def run_commands_from_file(filename: str, shell: Cmd2):
    command = read_file(filename)
    run_command(command, shell, strict=True)


def run_interactively(shell):
    io_util.interactive = True
    # TODO
    # shell.auto_save = True
    i = 0
    while True:
        i += 1
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            shell.intro = ''


def run(shell, commands, filename, repl=True):
    if commands or filename is not None:
        # compile mode
        if filename is not None:
            run_commands_from_file(filename, shell)

        if commands:
            run_command(commands, shell, strict=True)

    elif repl:
        run_interactively(shell)


def cat_file(filename: str) -> str:
    try:
        return Path(filename).read_text()
    except (FileNotFoundError, IsADirectoryError) as e:
        raise ShellError from e
