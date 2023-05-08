from logging import debug
import pandas as pd
import shlex
from typing import Any, Iterable, List, Tuple
from mash.filesystem.view import NAME

from mash.io_util import log
from mash.shell.grammer import literals
from mash.shell.grammer.literals import FALSE, TRUE
from mash.shell.errors import ShellError
from mash.util import is_globbable, is_valid_method_name, match_words, quote, quote_all, glob


def expand_variables(terms: List[str], env: dict,
                     completenames_options: List[str],
                     ignore_invalid_syntax: bool,
                     wildcard_value='$',
                     escape=False) -> Iterable[str]:
    """Replace variables with their values.
    E.g.
    ```sh
    a = 1
    print $a # gets converted to `print 1`
    ```
    """
    for v in terms:
        v = str(v)
        if v == '$':
            if escape:
                yield quote(wildcard_value, ignore=list('*$<>'))
            else:
                yield wildcard_value
            continue

        matches = match_words(v, prefix=r'\$')
        if matches:
            for match in matches:
                k = match[1:]
                if not is_valid_method_name(k):
                    # ignore this variable silently
                    continue

                error_msg = f'Variable `{match}` is not set'

                if k in env:
                    # TODO continue after finding a match
                    v = v.replace(match, to_string(env[k]))
                elif ignore_invalid_syntax:
                    debug(' '.join(str(s) for s in terms))
                    log(error_msg)
                else:
                    debug(' '.join(str(s) for s in terms))
                    raise ShellError(error_msg)

        if is_globbable(v):
            try:
                matches = glob(v, completenames_options, strict=True)
                if escape:
                    matches = quote_all(matches, ignore=['$*'])
                yield ' '.join(matches)
                continue

            except ValueError as e:
                if ignore_invalid_syntax:
                    log(f'Invalid syntax: {e}')
                else:
                    raise ShellError(e)

        if escape and matches:
            yield quote(v, ignore=list('*$<>'))
        else:
            yield v


def expand_variables_inline(line: str, env: dict,
                            completenames_options: List[str],
                            ignore_invalid_syntax: bool) -> str:
    """Expand $variables in `line`.
    """
    terms = line.split(' ')
    expanded_terms = expand_variables(terms, env,
                                      completenames_options,
                                      ignore_invalid_syntax)
    line = ' '.join(expanded_terms)
    return line


def to_string(value: Any) -> str:
    """Convert a variable to a string.
    """
    if isinstance(value, bool):
        value = TRUE if value else FALSE

    elif isinstance(value, list):
        value = list_to_string(value)

    elif isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if isinstance(v, dict):
                result[k] = dict_to_string(v)
            elif isinstance(v, list):
                result[k] = list_to_string(v)
            else:
                result[k] = str(v)

        df = pd.Series(result, name='values').to_frame()
        value = df.to_markdown()

    return str(value)


def dict_to_string(d: dict) -> str:
    return '{ ' + ','.join(d.keys()) + ' }'


def list_to_string(items: list) -> str:
    try:
        items = [str(item[NAME]) for item in items]
    except (TypeError, KeyError):
        items = range(len(items))

    return '[ ' + ','.join(items) + ' ]'


def to_bool(line: str) -> bool:
    if isinstance(line, bool):
        return line

    return line != FALSE and line is not None


def filter_comments(terms: List[str]) -> List[str]:
    if '#' in terms:
        i = terms.index('#')
        terms = terms[:i]
    return terms


def quote_items(items: List[str]) -> Iterable[str]:
    """Map shlex.quote() to all items.
    Do not modify python delimiters.
    """
    for arg in items:
        arg = str(arg)
        if arg in literals.python or arg in literals.comparators:
            yield arg
        else:
            yield shlex.quote(arg)


def indent_width(line: str) -> Tuple[str, str]:
    """Return a tuple that represents the length of the indentation in spaces and tabs.
    """
    n = len(line) - len(line.lstrip())
    prefix = line[:n]
    n_spaces = prefix.count(' ')
    n_tabs = prefix.count('\t')
    return n_spaces, n_tabs


def inline_indent_with(*indent_per_type) -> float:
    for i in indent_per_type:
        if i > 80:
            raise NotImplementedError(f'Indent too large: {i}')

    values = ''.join(f'{k:080}' for k in indent_per_type)
    return str('.' + ''.join(values))


def quote_return_value(value: str, delimiter='\n') -> str:
    ignore = list('*!?@<>+')
    if delimiter in ignore:
        ignore.remove(delimiter)
    return quote_all(value, ignore)
