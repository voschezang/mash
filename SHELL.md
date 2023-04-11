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
class ShellWithFileSystem:
	shell: Shell
  repository: FileSystem # a directory or REST resource

class Shell(Cmd)
	env: FileSystem # variable scopes
```



## Filesystem

A directory-like interface for dictionaries and lists.

```sh
filesystem/
    filesystem.FileSystem # A file system simulation that provides an interface to data.
    discoverable.py # A subclass that extends Directory with lazy data loading.
    view.View # A datastructure that provides a view of internal data.
```

