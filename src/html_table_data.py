"""A datastructures that represent an HTML table with cells of variable height.
"""
from dataclasses import dataclass
from typing import Dict, List

from object_parser import JSONFactory


@dataclass
class Parameters:
    headings: Dict[str, str]


@dataclass
class Row:
    row: Dict[str, List[str]]

    @property
    def height(self):
        """The max. number of "stacked" cells.
        This can be used to infer the html rowspan property.
        """
        return max(len(col) for col in self.row.values())


@dataclass
class HTMLTableData:
    parameters: Parameters
    rows: List[Row]

    @property
    def max_row_height(self):
        return max(row.height for row in self.rows)

def parse_json(json: dict):
    return JSONFactory(HTMLTableData).build(json)


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
