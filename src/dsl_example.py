from dsl import Function, shell, main
from util import identity


def f(x: int): return x
def g(x: int, y=1): return x + y
def h(x: int, y: float, z): return x + y * z


def example(a: int, b, c: float = 3.):
    """An example of a function with a docstring

    Parameters
    ----------
        a: positive number
        b: object
    """
    return a


functions = {'f': f,
             'g': g,
             'h': h,
             'example': example,
             'echo': identity,
             'ls': Function(shell('ls'), args={'-latr': 'flags', '[file]': ''}),
             'cat': Function(shell('cat'), args={'file': ''}),
             'vi': Function(shell('vi'), args={'[file]': ''})}


if __name__ == '__main__':
    main(functions)
