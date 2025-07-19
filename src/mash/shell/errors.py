
class ShellError(RuntimeError):
    pass


class ShellTypeError(RuntimeError):
    pass


class ShellPipeError(RuntimeError):
    pass


class ShellSyntaxError(ShellError):
    pass
