
from mash.functional_shell import tokenizer
from mash.functional_shell.parser import parse


def parse_line(text: str):
    return parse(text).values[0]


def test_parse_cmd():
    text = 'ab cd'
    result = parse(text)
    result
