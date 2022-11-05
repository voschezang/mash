from argparse import ArgumentParser
from dataclasses import dataclass
from functools import partial
from logging import info
import os
from typing import Dict, List
import yaml
import dominate
from dominate.tags import table, tbody, th, tr, td, style

import io_util
from io_util import has_argument
from io_util import ArgparseWrapper, has_argument

example_yaml_data = """
parameters:
    headings:
        first: First Heading
        last: Last Heading
rows:
    - row:
          first:
              - A value
          last:
              - Option B
              - Option C
    - row:
          first:
              - Another value
          last:
              - Option D
              - Option E
"""


def parse_cell(text: str, rowspan=1):
    if rowspan == 1:
        return partial(td, text)
    return partial(td, text, rowspan=rowspan)


def parse_column(column: dict, height: int):
    if len(column) > 1:
        height = 1

    return [parse_cell(cell, height) for cell in column]


def parse_row(row: dict, headings: list, height=1):
    for heading in headings:

        if heading in row:
            cell = row[heading]
        else:
            cell = ''

        yield parse_column(cell, height)


def parse(data: dict):
    headings = data['parameters']['headings']
    # TODO magic number
    height = 2
    for row in data['rows']:
        row = row['row']
        yield list(parse_row(row, headings, height))


def render_table_head(doc, css):
    if css is None:
        return

    with doc.head:
        style(css)


def render_table_body(height, headings, with_width):
    with tr():
        for heading in headings:
            th(heading)

    for row in with_width:
        with tbody():
            for i in range(height):
                with tr():
                    for col in row:
                        if len(col) > i:
                            col[i]()


def generate(data: dict, css=''):
    height = 2
    headings = data['parameters']['headings'].values()

    with_width = list(parse(data))

    return render(css, height, headings, with_width, doc)


def render(css, height, headings, with_width):
    doc = dominate.document(title='table')
    render_table_head(doc, css)

    with doc:
        with table():
            render_table_body(height, headings, with_width)

    return doc


def add_cli_args(parser: ArgumentParser):
    css = f'{os.path.dirname(__file__)}/../css/table.css'
    if not has_argument(parser, 'file'):
        parser.add_argument('file', default='', nargs='?',
                            help='Table data files in .yaml format')
        parser.add_argument('--css', default=css,
                            help='Style sheet in .css format')


def verify_table_data(data: dict):
    assert 'parameters' in data
    assert 'rows' in data

    assert 'headings' in data['parameters']

    for row in data['rows']:
        assert 'row' in row
        for heading in row['row'].keys():
            assert heading in data['parameters']['headings']


def main(filename: str, stylesheet: str = None, html=True, md=False):
    if stylesheet:
        css = open(stylesheet).read()
    else:
        css = ''

    if filename:
        f = open(f'{filename}.yaml').read()
    else:
        f = example_yaml_data

    data = yaml.load(f, yaml.Loader)

    verify_table_data(data)

    doc = generate(data, css)
    body = doc.body.children[1]

    if not filename:
        print(body)
        return doc

    if html:
        info(f'Writing to {filename}.html')
        open(f'{filename}.html', 'w').write(str(doc))

    if md:
        info(f'Writing to {filename}-table.md')
        open(f'{filename}-table.md', 'w').write(str(body))

    return doc


if __name__ == '__main__':
    with ArgparseWrapper() as parser:
        add_cli_args(parser)

    doc = main(io_util.parse_args.file,
               io_util.parse_args.css,
               md=True)
    # print(doc)
