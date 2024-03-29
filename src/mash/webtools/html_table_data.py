"""A datastructures that represent an HTML table with cells of variable height.
"""
from dataclasses import dataclass
from typing import Dict, List
import mistletoe

from mash.object_parser.factory import build


HeadingKey = str


class Markdown(str):
    @staticmethod
    def parse_value(value):
        v = mistletoe.markdown(value)
        return mistletoe.markdown(value)


@dataclass
class Row:
    row: Dict[HeadingKey, List[Markdown]]

    @property
    def height(self):
        """The max. number of "stacked" cells.
        This can be used to infer the html rowspan property.
        """
        return max(len(col) for col in self.row.values())


@dataclass
class Parameters:
    headings: Dict[HeadingKey, Markdown]


@dataclass
class HTMLTableData:
    parameters: Parameters
    rows: List[Row]

    @property
    def max_row_height(self):
        return max(row.height for row in self.rows)


def parse_json(json: dict):
    return build(HTMLTableData, json)


example_yaml_data = """
parameters:
    headings:
        first: _First_ Heading
        last: _Last_ Heading
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
