from dsl import Shell, set_functions, Function, shell


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
             'e': example,
             'example': example,
             'ls': Function(shell('ls'), args=['-latr'])}

if __name__ == '__main__':
    shell = Shell()
    set_functions(shell, functions)
    shell.cmdloop()
