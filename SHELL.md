# Shell

A tool to generate a [Domain-specific Language](https://en.wikipedia.org/wiki/Domain-specific_language) (DSL).  It can be used as a command line program or interactively as a subshell/repl.

<img src="img/shell_dropdown.png" style="max-width: 10%" alt="Example of a shell with a dropdown completion menu">

## Overview

By default, it provides piping and Bash-like functionality. It can be extended with custom functions.

## Setup

A client just has to define a mapping between commands and functions. The corresponding documentation is automatically generated from the docstrings and type annotations.

E.g.

```py
from shell import set_functions

# the mapping from command names to Python functions
functions = {'run': some_function}

# link the mapping
set_functions(functions)
```

Then a client can call for example:

```sh
./src/shell.py run $args 
```

## Usage

```sh
usage: shell.py [-hvsr][-f FILE] [--session SESSION] [cmd [cmd ...]]

If no positional arguments are given then an interactive subshell is started.

positional arguments:
  cmd                   A comma- or newline-separated list of commands

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose
  -s, --safe            Safe-mode. Ask for confirmation before executing commands.
  -f FILE, --file FILE  Read and run FILE as a commands
  -r, --reload          Reload last session
  --session SESSION     Use session SESSION
```

## Usage Examples

### Example 1

See `src/shell_example.py`. It shows how to use a user-definnable mapping of custom functions.
It uses the library `quo` to create a user-friendly subshell with autocompletion prompts.

```sh
# py src/shell.py echo hello, echo world
hello
world
```

```sh
# py src/shell_example.py
Welcome.  Type help or ? to list commands.

$ ?

Documented commands (type help <topic>):
========================================
e  example  f  g  h  help  ls  shell

$ help g
g x [y]

 Parameters
 ----------
  x: int
  y
```

### Example 2: Directory Simulation

See `src/crud_example.py`. This simulates a REST resources with a directory hierarchy.
In addition, it provides fuzzy name completion.

```sh
$ py src/crud_example.py tree
# example data with dicts and lists
repository = {'worlds': [
    {'name': 'earth',
     'animals': [
         {'name': 'terrestrial',
          'snakes': [{'name': 'python'},
                     {'name': 'cobra'}]},
         {'name': 'aquatic',
          'penquins': [{'name': 'tux'}]}
     ]}]}
```

```sh
# note the autocompletion
$ py src/shell_example_extended.py 'cd world; cd a; cd t; cd snakes; ll'
python
cobra
```

### Example 3: Commands

Run commands from a file with `python src/shell.py -f FILE`

```sh
# write to file
print A sentence. > out.txt 
!cat out.txt |> export x # save text from file
print $x

y <- shell expr 2 + 2 # store result in variable $y
print "result:" $y # prints "result: 4
```

## Implementation

Modules:

```sh
shell_base.BaseShell # a subclass of Cmd that overrides some methods
shell.Shell # extension of BaseShell
shell_function.ShellFunction # A wrapper for "normal" Python functions that includes error handling.
shell_example.py
crud.BaseCRUD # A directory simulation (an abstract base class)
crud.CRUD # Directory simulation
crud_example # An example with a directory-like repository
cli.py # a CLI that combines Shell with quo.Prompt
```
