
class ShellError(RuntimeError):
    pass


class ShellPipeError(RuntimeError):
    pass


class ShellSyntaxError(ShellError):
    pass
