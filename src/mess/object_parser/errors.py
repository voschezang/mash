class SpecError(Exception):
    pass


class SpecErrors(SpecError):
    pass


class BuildError(SpecError):
    pass


class BuildErrors(SpecError):
    pass

class ErrorMessages:
    """A static class with can be subclassed
    """
    @staticmethod
    def invalid_key_format(cls, key: str):
        return f'Format of key: `{key}` was invalid  in {cls}'

    @staticmethod
    def missing_mandatory_key(cls, key: str) -> str:
        return f'Missing mandatory key: `{key}` in {cls}'

    @staticmethod
    def no_type_annotations(cls) -> str:
        return f'No fields specified to initialize (no type annotations in {cls})'

    @staticmethod
    def unexpected_key(cls, key):
        return f'Unexpected key `{key}` in {cls}'
