# Mash as a Domain-specific Language

Create a custom domain-specific language (DSL) with Mash.



## REST Client

Use the shell as a REST client. For example:

```py
from mash.filesystem.discoverable import observe
from mash.shell import ShellWithFileSystem
from mash.shell.shell import main

@dataclass
class User:
    """A REST resource of the endpoints `/users` and `/users/{id}`
    """
    email: str
    role: str

    @staticmethod
    def get_value(path: Path):
        # Retrieve external data and instantiate this class.

    @staticmethod
    def get_all(path: Path):
        # Return resource identifiers.

    @staticmethod
    def refresh() -> bool:
        # Return True to indicate that a resource should be refreshed.


if __name__ == '__main__':
    fs = ShellWithFileSystem({'repository': User},
                             get_value_method=observe)
    main(shell=shell.shell)
```

