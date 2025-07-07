
from argparse import ArgumentParser
import os

if __name__ == '__main__':
    import _extend_path  # noqa

from mash import io_util
from mash.io_util import has_argument
from mash.io_util import ArgparseWrapper, has_argument
from mash.webtools.html_table import main


def add_cli_args(parser: ArgumentParser):
    css = f'{os.path.dirname(__file__)}/css/table.css'
    if not has_argument(parser, 'file'):
        parser.add_argument('file', default='', nargs='?',
                            help='Table data files in .yaml format')
        parser.add_argument('--css', default=css,
                            help='Style sheet in .css format')


if __name__ == '__main__':
    with ArgparseWrapper() as parser:
        add_cli_args(parser)

    doc = main(io_util.parse_args.file,
               io_util.parse_args.css,
               md=True)
