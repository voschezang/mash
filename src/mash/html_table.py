from argparse import ArgumentParser
from functools import partial
from logging import info
import os
import yaml
import dominate
from dominate.tags import table, tbody, th, tr, td, style
from dominate.util import raw

from mash import io_util
from mash.io_util import has_argument
from mash.io_util import ArgparseWrapper, has_argument
from mash.html_table_data import HTMLTableData, example_yaml_data, parse_json


def parse_cell(text: str, rowspan=1):
    text = raw(text)
    if rowspan == 1:
        return partial(td, text)
    return partial(td, text, rowspan=rowspan)


def parse_column(column: dict, height: int):
    if len(column) > 1:
        if len(column) == height:
            rowspan = 1
        else:
            rowspan = height // len(column)

    else:
        rowspan = height

    return [parse_cell(cell, rowspan) for cell in column]


def parse_row(row: dict, headings: list, height=1):
    for heading in headings:

        if heading in row:
            cell = row[heading]
        else:
            cell = ''

        yield parse_column(cell, height)


def parse(data: dict):
    headings = data.parameters.headings
    for row in data.rows:
        yield list(parse_row(row.row, headings, row.height))


def render_table_head(doc, css):
    if css is None:
        return

    with doc.head:
        style(css)


def render_table_body(max_height, headings, with_width):
    with tr():
        for heading in headings:
            th(raw(heading))

    for row in with_width:
        with tbody():
            for i in range(max_height):
                with tr():
                    for col in row:
                        if len(col) > i:
                            col[i]()


def generate(data: dict, css=''):
    headings = data.parameters.headings.values()

    with_width = list(parse(data))

    return render(css, data.max_row_height, headings, with_width)


def render(css, max_height, headings, with_width):
    doc = dominate.document(title='table')
    render_table_head(doc, css)

    with doc:
        with table():
            render_table_body(max_height, headings, with_width)

    return doc


def add_cli_args(parser: ArgumentParser):
    css = f'{os.path.dirname(__file__)}/../css/table.css'
    if not has_argument(parser, 'file'):
        parser.add_argument('file', default='', nargs='?',
                            help='Table data files in .yaml format')
        parser.add_argument('--css', default=css,
                            help='Style sheet in .css format')


def main(filename: str, stylesheet: str = None, html=True, md=False):
    if stylesheet:
        css = open(stylesheet).read()
    else:
        css = ''

    if filename:
        f = open(f'{filename}.yaml').read()
    else:
        f = example_yaml_data

    json: dict = yaml.load(f, yaml.Loader)
    data: HTMLTableData = parse_json(json)
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
