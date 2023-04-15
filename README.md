![workflow-badge](https://github.com/voschezang/mash/actions/workflows/python-app.yml/badge.svg)
<a href="https://pypi.org/project/mash-shell" title="Python versions"><img src="https://img.shields.io/badge/python-3.8%20|%203.10%20|%203.11-blue"/></a>
<a href="https://pypi.org/project/mash-shell" title="PyPI"><img src="https://img.shields.io/badge/pypi-v0.2.0-blue"/></a>


**Docs**:
[MAIN](https://github.com/voschezang/mash/blob/main/README.md) 
| [SHELL.md](https://github.com/voschezang/mash/blob/main/SHELL.md)
| [REFERENCE.md](https://github.com/voschezang/mash/blob/main/SHELL_REFERENCE.md)

<img src="https://github.com/voschezang/mash/blob/main/img/dall-E/bosh-terminal-icon.png?raw=true" style="max-width: 5%" alt="A drawing of a terminal"></img>

# Mash | My Automation Shell

A *shell* that can be used to for automation and (REST) resource discovery. It can be used as a [cli](https://en.wikipedia.org/wiki/Command-line_interface), [repl](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop). It exposes a [complete](https://en.wikipedia.org/wiki/Turing_completeness) programming [language](SHELL_REFERENCE.md) with variables, functions, conditions and pipes. The language can be tailored towards [domain-specific](https://en.wikipedia.org/wiki/Domain-specific_language) applications and it has interoperability with Bash. In addition, this repository contains a library of  utilities.

Features:

- A **DSL** that can interpret user-defined commands: `shell.py`.
- A **file-browser**. Query both static datastructures and REST APIs: `examples/filesystem.py`,
- A **REST client** to browse APIs with a programmatic yet intuitive interface: `examples/discoverable_api.py`.
- An **object parser** which converts JSON data to Python classes: `object_parser.py`.
- An **OAS-generator** for Python classes: `oas.py`.
- A subshell wrapper, to redirect the output of shell scripts: `subshell.py`.
- A parallelization framework for load testing: `parallel.py`.

Links
- [Mash language reference](SHELL_REFERENCE.md)
- [PyPI](https://pypi.org/project/mash-shell)
- [github](https://github.com/voschezang/mash)

## Shell

<img src="https://github.com/voschezang/mash/blob/main/img/shell_dropdown.png?raw=true" style="max-height: 180px;" alt="Example of a shell with a dropdown completion menu"></img>


```sh
pip install mash-shell
python -m mash
```

See [`src/examples`](src/examples) for advances usage examples.

**Documentation**

- Implementation: [SHELL.md](https://github.com/voschezang/mash/blob/main/SHELL.md)
- Language: [REFERENCE.md](https://github.com/voschezang/mash/blob/main/SHELL_REFERENCE.md).

**Table of Contents**

- [Usage](#Usage)
    - [CLI](#CLI)
    - [Filesystem (CRUD Operations)](#Filesystem%20(CRUD%20Operations))
    - [Usage Examples](#Usage%20Examples)
- [Library & Tools](#Library%20&%20Tools)
    - [Parallelization Utilities](#Parallelization%20Utilities)
    - [Object Parser](#Object%20Parser)

# Usage

See [reference](SHELL_REFERENCE.md).

### CLI

```sh
▶ python -m mash -h
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

## Filesystem (CRUD Operations)

See `examples/filesystem.py` and `examples/discoverable.py`.

| Example             | Description                                                  |
| ------------------- | ------------------------------------------------------------ |
| `ls [PATH]`         | List the items in a directory. Use the current working directory by default. Alias: `list` |
| `cd`, `use [PATH]`  | Change the current working directory. Alias: `use`           |
| `get NAME`          | Retrieve a file.                                             |
| `set NAME VALUE`    | Modify a file.                                               |
| `new NAME [NAME..]` | Create new directories.                                      |
| `show [NAME]`       | Display detailed information about a directory.              |
| `cp`, `mv`, `rm`    | Modify files. I.e. copy, move, rename or remove files.       |
| `home [PATH]`       | Set home directory.                                          |
| `reset`             | Refresh cached values.                                       |

## Usage Examples

For real-world examples, see [lib](https://github.com/voschezang/mash/blob/main/src/lib/math.sh).

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

### Example 2: Commands

Run commands from a file with `python src/shell -f FILE` or `python -m src.shell -f FILE`.

```sh
# write to file
print A sentence. > out.txt 
!cat out.txt |> export x # save text from file
print $x

y <- shell expr 2 + 2 # store result in variable $y
print "result:" $y # prints "result: 4

shell expr 2 + 2 -> z # store result in variable $z
print "result:" $z # prints "result: 4
```

### Example 3: File System Simulation

Support both static and dynamic data.

#### With Static Data

See `examples/filesystem_example.py`. This simulates a REST resources with a directory hierarchy.
In addition, it provides fuzzy name completion.

```sh
$ python src/examples/shell_example.py tree
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
$ python src/examples/filesystem.py 'cd world; cd a; cd t; cd snakes; ll'
python
cobra
```

### With Dynamic Data

See `examples/discoverable.py`.

```sh
# list remote/auto-generated data
$ python src/examples/discoverable.py 'ls'
department_805, department_399

# refresh data, then save
$ py src/examples/discoverable.py 'ls ; save'
department_750, department_14

# reload data
$ python src/examples/discoverable.py 'ls'
department_750, department_14
```



# Library & Tools

## Setup

Using a `Makefile` for convenience.

```sh
make install
make test
```

## Parallelization Utilities

Some experiments with parallelization, concurrency and `asyncio` in Python.

### Test

Start a dummy server.

```sh
python3 src/server.py
```

Do a simple load test

```sh
python3 src/parallel.py -v
```

## Object Parser

- [src/object_parser/object_parser.py](object_parser.py) parses JSON data and instantiate Python objects.
- [src/object_parser/oas.py](oas.py) converts domain-models to OAS.

### Example

```sh
python src/object_parser_example.py
```

<img src="https://github.com/voschezang/data-science-templates/blob/main/img/generated_oas.png?raw=true" style="width: 400px" alt="OAS Example">

### REST API

Server

```sh
python src/object_parser_server.py
```

Client

```sh
curl -X 'POST' 'http://localhost:5000/v1/organizations' \
  -H 'Content-Type: application/json' \
  -d '{ "board": [ "string" ], "ceo": "string", "departments": [ { "manager": "string", "teams": [ { "manager": "string", "members": [ "string" ], "team_type": "A", "active": true, "capacity": 0, "value": 0 } ] } ] }'
```
