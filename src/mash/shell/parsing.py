from typing import Any, Iterable, List, Tuple
import shlex

from mash.io_util import log
from mash.shell.delimiters import FALSE, TRUE
from mash.shell.errors import ShellError
from mash.util import is_globbable, is_valid_method_name, match_words, removeprefix, split_sequence, glob


def infer_infix_args(op: str, *args: str) -> Tuple[Tuple[str], Tuple[str]]:
    if args[1] == op:
        lhs, _, *rhs = args
        lhs = (lhs,)
    else:
        i = args.index(op)
        lhs = args[:i]
        rhs = args[i:]
    return lhs, rhs


def parse_commands(line: str, delimiters: List[str], ignore_invalid_syntax: bool) -> Iterable[List[str]]:
    """Split up `line` into an iterable of single commands.
    """
    try:
        # split lines and handle quotes
        # e.g. convert 'echo "echo 1"' to ['echo', 'echo 1']
        terms = shlex.split(line, comments=True)

        # re-quote delimiters
        for i, term in enumerate(terms):
            # if other_delimiters:
            if term in delimiters or term == '=':
                if '"' + term + '"' in line or "'" + term + "'" in line:
                    terms[i] = f'"{terms[i]}"'
                elif '\\' + term in line:
                    terms[i] = f'\\{terms[i]}'

        # split `:`
        for i, term in enumerate(terms):
            if term.endswith(':'):
                # verify that the term wasn't quoted
                if '"' + term + '"' in line or "'" + term + "'" in line:
                    continue

                terms[i] = terms[i][:-1]
                terms.insert(i+1, ':')
                break

    except ValueError as e:
        msg = f'Invalid syntax: {e} for {str(line)[:10]} ..'
        if ignore_invalid_syntax:
            log(msg)
            return []

        raise ShellError(msg)

    if not terms:
        return []

    ################################################################################
    # handle lines that end with `;`
    # e.g. 'echo 1; echo 2;'
    # TODO this doesn't preserve ; when it was originally enclosed in quotes
    # terms = chain.from_iterable([split_tips(term.strip(), ';') for term in terms])
    ################################################################################

    # group terms based on delimiters
    results = split_sequence(terms, delimiters, return_delimiters=True)

    for line in results:
        unquote_delimiters(line, delimiters)
        yield line


def unquote_delimiters(terms: List[str], delimiters: List[str]) -> List[str]:
    for i, term in enumerate(terms):
        if term.startswith('\\'):
            suffix = removeprefix(term, '\\')
            if suffix in delimiters:
                terms[i] = suffix


def expand_variables(terms: List[str], env: dict,
                     completenames_options: List[str],
                     ignore_invalid_syntax: bool) -> Iterable[str]:
    """Replace variables with their values.
    E.g.
    ```sh
    a = 1
    print $a # gets converted to `print 1`
    ```
    """
    for v in terms:
        matches = match_words(v, prefix=r'\$')
        if matches:
            for match in matches:
                k = match[1:]
                if not is_valid_method_name(k):
                    # ignore this variable silently
                    continue

                error_msg = f'Variable `{match}` is not set'

                if k in env:
                    v = v.replace(match, to_string(env[k]))
                elif ignore_invalid_syntax:
                    log(error_msg)
                else:
                    raise ShellError(error_msg)

        if is_globbable(v):
            try:
                matches = glob(v, completenames_options, strict=True)
                yield ' '.join(matches)
                continue

            except ValueError as e:
                if ignore_invalid_syntax:
                    log(f'Invalid syntax: {e}')
                else:
                    raise ShellError(e)

        yield v


def to_string(value: Any) -> str:
    """Convert a variable to a string.
    """
    if isinstance(value, bool):
        value = TRUE if value else FALSE
    return str(value)


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


def filter_comments(terms: List[str]) -> List[str]:
    if '#' in terms:
        i = terms.index('#')
        terms = terms[:i]
    return terms
