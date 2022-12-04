from collections import defaultdict
from io import TextIOBase
import select
import subprocess
import sys
import time
import logging

from mash.io_util import shell_ready_signal, has_output
import mash.shell.progress_bar as progress_bar

is_activated = defaultdict(bool)


def main(args):
    for stdout, stderr in run(args):
        if stderr:
            print('&2:', stderr)
        if stdout:
            if stdout.strip() != shell_ready_signal:
                print('&1:', stdout)


def run(args, timeout=0.3):
    """Run `args` in a subprocess.

    Behaviour
    ----------
    The output is lazy, but can be listed:
        list(run(args))

    Real time interaction is handled line by line.
        The subprocess stdout is returned by default.
        The subprocess stind is accessible through a prompt, but only after `util.shell_ready_signal` is encountered.

    Parameters
    ----------
    args: list
        arguments for subprocess.Popen
    timeout: float
        timeout between
    """
    # Use subprocess to allow stdout to be used directly
    process = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    poll = select.poll()
    poll.register(process.stdout, select.POLLIN)

    # allow the process to start before trying to parse the result
    time.sleep(0.1)

    stdout = ''
    while True:

        stderr = read_output(process.stderr)
        stdout = read_output(process.stdout, block=True)
        yield stdout, stderr

        if verify_promt_is_ready(stdout):
            handle_user_input(process)
            continue

        if stdout or stderr:
            continue

        result = process.poll()
        if result is None:
            # TODO this branch is never executed, hence `timeout` is unused
            progress_bar.show()
            time.sleep(timeout)
            assert False

        stdout, stderr = process.communicate()
        yield stdout.decode(), stderr.decode()

        if result != 0:
            raise RuntimeError(f'Subprocess exited with status: {result}')
        return


def read_output(stream: TextIOBase, timeout=0, block=False):
    """Read and print a line from `stream`.
    """

    global is_activated
    if not is_activated[stream]:
        is_activated[stream] = has_output(stream)

    if not is_activated[stream]:
        return ''

    if not has_output(stream) and not block:
        return ''

    # Don't use use Popen.communicate because it would wait for EOF
    return stream.readline().decode()


def verify_promt_is_ready(signal):
    return signal.strip() == shell_ready_signal


def handle_user_input(process):
    # TODO make this prompt user-friendly
    # TODO use library `readline``
    try:
        stdin = input('$ ')
    except KeyboardInterrupt as e:
        # clear terminal
        print()

        logging.info(e)
        exit(130)

    logging.debug(f'User-input: "{stdin}"')
    process.stdin.write(stdin.encode() + b'\n')
    process.stdin.flush()


if __name__ == '__main__':
    # TODO add proper CLI

    if not sys.argv[1:]:
        fn = sys.modules[__name__].__file__
        logging.warning(f'Usage: {fn} CMD')
        sys.exit(3)

    main(sys.argv[1:])
