# Implementation

## Overview

See [shell subclasses](https://voschezang.github.io/mash-docs/pages/shell_classes.html). The main datastructure of `Shell`  is `mash.filesystem`. It's inferface is inspired by unix filesystems. It is used to:

- Implement local/global variable scopes in `Shell`.
- Let a user browse REST-like resources (directories) with CRUD operations:
  - Discovery: `cd, list, get, tree, show`.
  - Mutations: `new, set, mv, cp`.

### Module Tree

For more details, see the overview of the [Shell classes](https://voschezang.github.io/mash-docs/pages/shell_classes.html) overview, the [AST classes](https://voschezang.github.io/mash-docs/pages/ast.html) and the full [source code](https://github.com/voschezang/mash/tree/main/src).

```sh
src
├── examples # Examples written in Python
│
├── lib # Mash shell scripts
│   └── math.sh # Elementary mathematical functions
│
└── mash
    ├── filesystem # CRUD operations for directories and REST resources
    │   ├── filesystem.py
    │   └── view.py # A tree of dict's. Tree traversal is exposed through the methods `up` and `down`.
    │
    ├── object_parser # Parse JSON objects
    │   ├── factory.py
    │   └── oas.py
    │
    ├── shell
    │   ├── __init__.py
    │   ├── ast # The Abstract Syntax Tree (AST) and related logic
    │   │   └── # Node, Word, Lines
    │   ├── grammer # Parse raw text based on BNF grammer and build the AST
    │   └── ShellWithFileSystem, Shell, BaseShell, Cmd2
    │
    ├── subshell.py
    └── cli.py # A CLI that combines Shell with quo.Prompt
```

## Classes

### Language Model

The language model is based on an intermediate representation: an [Abstract Syntax Tree (AST)](https://en.wikipedia.org/wiki/Abstract_syntax_tree).

- Raw text is tokenized and parsed using a model defined in a [context-free grammar](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form).
- This is used to build the tree.
- Each *node* in the AST is a class with it's own behaviour.

```sh
Lines
└── Nodes
    └── Node
```

See [`shell.ast`](https://voschezang.github.io/mash-docs/pages/ast.html).

### Shell

### Filesystem

A directory-like interface for dictionaries and lists.

```sh
filesystem/
    filesystem.FileSystem # A file system simulation that provides an interface to data.
    discoverable.py # A subclass that extends filesystem with lazy data loading.
    view.View # A datastructure that provides a view of internal data.
    scope.Scope # Expose global and local variables in a directory tree.
```

## Shell with Filesystem

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
