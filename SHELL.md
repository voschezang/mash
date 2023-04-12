# Implementation

Modules

```sh
# in src
examples/ # examples written in Python
lib/ # shell scripts
    math.sh # elementary mathematical functions
mash/ # implementation written in Python 
  filesystem/ # CRUD operations for directories and REST resources
  object_parser/ # parse JSON objects
  shell/
    ShellWithFileSystem
    Shell
    Cmd2 # An extension of cmd.Cmd
    lex_parser # BNF-based grammer
    model # AST-based logic
cli.py # A CLI that combines Shell with quo.Prompt
```

## Shell

The `Shell` class is based on `cmd.Cmd`. It extends it with a custom grammer, user-definable variables, functions, pipes and more.

`Cmd2` extends [`cmd.Cmd`](https://docs.python.org/3.11/library/cmd.html) with a few basic methods. This can be used as an example as how to write a custom subclass for `Cmd` or `Shell`.

The main datastructure is `mash.filesystem`. It's inferface is inspired by unix filesystems. It is used to:

- Implement local/global variable scopes in `Shell`.
- Let a user browse REST-like resources (directories) with CRUD operations:
	- Discovery: `cd, ls, get, tree, show`.
    - Mutations: `new, set, mv, cp`.


### Class Hierarchy

#### Simplified

```python
import cmd

class ShellWithFileSystem:
	shell: Shell
	repository: FileSystem # a directory or REST resource

class Shell(Cmd2):
    """Extend Cmd with various capabilities.
    This class is restricted to functionality that requires Cmd methods to be overrriden.

    Features:
    - An environment with local and global variable scopes.
    - Save/load sessions.
    - Decotion with functions, both at runtime and compile time.
    """
	env: FileSystem # variable scopes

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



## Filesystem

A directory-like interface for dictionaries and lists.

```sh
filesystem/
    filesystem.FileSystem # A file system simulation that provides an interface to data.
    discoverable.py # A subclass that extends Directory with lazy data loading.
    view.View # A datastructure that provides a view of internal data.
```

