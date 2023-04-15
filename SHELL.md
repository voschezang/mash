# Implementation

## Overview

The `Shell` class is based on `cmd.Cmd`. It extends it with a custom grammer, user-definable variables, functions, pipes and more.

`Cmd2` extends [`cmd.Cmd`](https://docs.python.org/3.11/library/cmd.html) with a few basic methods. This can be used as an example as how to write a custom subclass for `Cmd` or `Shell`.

The main datastructure is `mash.filesystem`. It's inferface is inspired by unix filesystems. It is used to:

- Implement local/global variable scopes in `Shell`.
- Let a user browse REST-like resources (directories) with CRUD operations:
	- Discovery: `cd, ls, get, tree, show`.
    - Mutations: `new, set, mv, cp`.

### Modules

In [src.mash](https://github.com/voschezang/mash/tree/main/src/mash).

```sh
examples/ # examples written in Python
lib/ # shell scripts
    math.sh # elementary mathematical functions
mash/ # implementation written in Python 
  filesystem/ # CRUD operations for directories and REST resources
  object_parser/ # parse JSON objects
  shell/
    ast/ # The Abstract Syntax Tree (AST) and related logic
    grammer/ # parse raw text based on BNF grammer and build the AST
    internals/
    ShellWithFileSystem
    Shell # Extend Cmd2 with the language model
    Cmd2 # An extension of cmd.Cmd
cli.py # A CLI that combines Shell with quo.Prompt
```

## Classes

#### Language Model

The language model is based on an intermediate representation: an [Abstract Syntax Tree (AST)](https://en.wikipedia.org/wiki/Abstract_syntax_tree).

- Raw text is parsed using a model defined in a [context-free grammar](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form).
- This is used to build the tree.
- Each *node* in the AST is a class with it's own behaviour.

```python
class Node(str); # incl. Word, Variable, QuotedString
class Nodes(str);
class Lines(str);
```

#### Shell

In pseudocode:

```python
import cmd

class ShellWithFileSystem:
    shell: Shell
    repository: FileSystem # a directory or REST resource

class Shell(Cmd2):
    """Shell.
    Support multiline statements, pipes, conditions, variables and inline function definitions.
    Use a BNF-based grammer in `lex_parser.py` to construct an AST.
    """

class BaseShell(Cmd2):
    """Extend Cmd with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrriden.

    Features:
    - An environment with local and global variable scopes.
    - Save/load sessions.
    - Decotion with functions, both at runtime and compile time.
    """
    env: FileSystem # variable scopes

    def save_session();
    def load_session();
    def add_functions();
    def remove_functions();

class Cmd2(cmd.Cmd):
    """Extend cmd.Cmd with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrriden.

    Features:
    - Confirmation mode to allow a user to accept or decline commands.
    - Error handling.
    - I/O methods: cat, source, print, println, exit
    - String methods: echo, flatten
    """

    def cmdloop();
    def onecmd();
    def default();
```


#### Filesystem

A directory-like interface for dictionaries and lists.

```sh
filesystem/
    filesystem.FileSystem # A file system simulation that provides an interface to data.
    discoverable.py # A subclass that extends Directory with lazy data loading.
    view.View # A datastructure that provides a view of internal data.
```

