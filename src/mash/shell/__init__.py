"""
See `shell <../pages/shell.html>`_
"""

# explicit API exposure
# "noqa" suppresses linting errors (flake8)
from mash.shell.errors import ShellError, ShellPipeError, ShellSyntaxError # noqa
from mash.shell.shell import Shell  # noqa
from mash.shell.function import ShellFunction # noqa
from mash.shell.with_filesystem import ShellWithFileSystem # noqa
