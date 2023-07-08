"""An example of CSS properties, defined using dataclasses and enums.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import List


@dataclass
class Margin:
    bottom: float
    left: float
    right: float
    top: float


class BorderStyle(Enum):
    dotted = auto()
    dashed = auto()
    double = auto()


class RGBColor(Enum):
    red = auto()
    green = auto()
    blue = auto()


@dataclass
class Border:
    style: BorderStyle
    width: float
    color: RGBColor
    rounded: float


@dataclass
class Element:
    border: Border
    margin: Margin


@dataclass
class Document:
    header: Element
    body: List[Element]
    footer: Element
