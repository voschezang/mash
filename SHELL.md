# Shell

A tool to generate a [Domain-specific Language](https://en.wikipedia.org/wiki/Domain-specific_language) (DSL).  It can be used as a command line program or interactively as a subshell/repl.

<img src="img/shell_dropdown.png" style="max-width: 10%" alt="Example of a shell with a dropdown completion menu">

A client just has to define a mapping between commands and functions. The corresponding documentation is automatically generated from the docstrings and type annotations.

E.g.
```py
functions = {'p': print,
             'sum': sum}
```


**Summary**

```
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

## Examples

### Example 1

See `src/shell_example.py`. It shows how to use a user-definnable mapping of custom functions.
It uses the library `quo` to create a user-friendly subshell with autocompletion prompts.

```sh
# py src/dsl_example.py echo hello, echo world
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

See `src/crud_implementation.py`. This simulates a REST resources with a directory hierarchy.
In addition, it provides fuzzy name completion.

```sh
$ py src/crud_implementation.py tree
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