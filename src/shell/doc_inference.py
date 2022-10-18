from typing import Dict


def infer_default_and_non_default_args(func):
    args = list(func.__code__.co_varnames)
    n_default_args = len(func.__defaults__) if func.__defaults__ else 0
    n_non_default_args = len(args) - n_default_args
    non_default_args = args[:n_non_default_args]
    default_args = args[n_non_default_args:]
    return non_default_args, default_args


def infer_args(func) -> list:
    non_default_args, default_args = infer_default_and_non_default_args(func)
    return non_default_args + [f'[{a}]' for a in default_args]


def infer_synopsis(func, variables=[]) -> str:
    if not variables:
        variables = infer_args(func)
    return ' '.join([func.__name__] + variables)


def infer_signature(func) -> dict:
    _, default_args = infer_default_and_non_default_args(func)

    def format(k):
        key = k
        if k in default_args:
            key = f'[{k}]'

        if k in func.__annotations__:
            v = func.__annotations__[k].__name__
            return key, f': {v}'

        return key, ''

    pairs = [format(var) for var in func.__code__.co_varnames]
    return {k: v for k, v in pairs}


def generate_parameter_docs(parameters) -> str:
    # explicitly define a tab to allow custom tab-widths
    tab = """
    """[1:]

    # transform dict to a multline string
    lines = (''.join(v) for v in parameters.items())
    parameters = f'\n{tab}{tab}'.join(lines)

    doc = f"""
    Parameters
    ----------
        {parameters}
    """

    # rm first newline
    return doc[1:]


def generate_docs(func, synopsis: str = None, args: Dict[str, str] = None, doc: str = None) -> str:
    if not hasattr(func, '__code__'):
        if synopsis is None and args is None:
            raise NotImplementedError('Cannot infer function signature')

    if args is None:
        args = infer_signature(func)
    if synopsis is None:
        synopsis = infer_synopsis(func, list(args.keys()))
    if doc is None:
        if func.__doc__:
            doc = func.__doc__
        elif args:
            doc = generate_parameter_docs(args)

    # only use doc when non-empty
    if doc:
        return synopsis + '\n\n' + doc
    return synopsis
