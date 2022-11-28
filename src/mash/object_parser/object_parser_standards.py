from dataclasses import dataclass
from typing import List


@dataclass
class A:
    x: int = 0
    y: int = 1
    z: int = 10


@dataclass
class B:
    left: A
    right: A
    top: A
    bottom: A


@dataclass
class C:
    a: A
    b: B
    x: int
    y: float
    z: List[A]


raw_data = ['abc' 'abc' 'abc',
            'aaa' 'bbb' 'ccc',
            'aab' 'aab' 'aab',
            'aba' 'bab' 'aba',
            'cab' 'acb' 'bac'
            ]

raw_data = ['aaa' 'bbb' 'ccc',
            'aab' 'bbc' 'ccb',
            'bab' 'bbb' 'ccc',
            ]

# lossless compression


def dictionary_mapping():
    # 1D map of common keys
    # i.e. a dictionairy coder
    # https://en.wikipedia.org/wiki/Dictionary_coder
    keys = ['abc', 'aaa', 'bbb', 'ccc'],
    values = [[0, 0, 0], [1, 2, 3]]
    for indices in values:
        yield [keys[i] for i in indices]


def differencing():
    # https://en.wikipedia.org/wiki/Data_differencing
    model = ['abc' 'abc' 'abc']
    mutations = ['',
                 'aaa' 'bbb' 'ccc',
                 '  b' '  b' '  c'
                 ]
    yield from [model + m for m in mutations]
