from dataclasses import dataclass
from typing import Dict, List

from object_parser import JSONFactory


@dataclass
class Parameters:
    headings: Dict[str, str]


@dataclass
class Row:
    row: Dict[str, List[str]]


@dataclass
class HTMLTableData:
    parameters: Parameters
    rows: List[Row]


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
