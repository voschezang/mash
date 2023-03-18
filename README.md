![workflow-badge](https://github.com/voschezang/mash/actions/workflows/python-app.yml/badge.svg)
<a href="https://pypi.org/project/mash-shell" title="Python versions"><img src="https://img.shields.io/badge/python-3.8%20|%203.10%20|%203.11-blue"/></a>
<a href="https://pypi.org/project/mash-shell" title="PyPI"><img src="https://img.shields.io/badge/pypi-v0.1.0-blue"/></a>


**Docs**:
[MAIN.md](https://github.com/voschezang/mash/blob/main/README.md) 
| [SHELL.md](https://github.com/voschezang/mash/blob/main/SHELL.md)
| [REFERENCE.md](https://github.com/voschezang/mash/blob/main/SHELL_REFERENCE.md)

<img src="https://github.com/voschezang/mash/blob/main/img/dall-E/bosh-terminal-icon.png?raw=true" style="max-width: 5%" alt="A drawing of a terminal"></img>

# Overview

A subshell and various utilities.

- A shell that can interpret a domain-specific language: `shell.py`.
- A client application for REST APIs with a programmatic yet intuitive interface.
- A subshell wrapper, to redirect the output of shell scripts: `subshell.py`.
- An object parser which converts JSON data to Python classes: `object_parser.py`.
- An OAS-generator for Python classes: `oas.py`.
- A parallelization framework for load testing: `parallel.py`.

Links
- [PyPI](https://pypi.org/project/mash-shell)
- [data-science-templates](https://github.com/voschezang/data-science-templates)

## Shell

See [SHELL.md](https://github.com/voschezang/mash/blob/main/SHELL.md) and [REFERENCE.md](https://github.com/voschezang/mash/blob/main/SHELL_REFERENCE.md).

<img src="https://github.com/voschezang/mash/blob/main/img/shell_dropdown.png?raw=true" style="max-width: 10%" alt="Example of a shell with a dropdown completion menu"></img>

## Usage

```sh
pip install mash-shell
python -m mash
```

See `src/examples` for advances usages.

# Setup

Using a `Makefile` for convenience.

```sh
make install
make test
```

# Parallelization Utilities

Some experiments with parallelization, concurrency and `asyncio` in Python.

## Test

Start a dummy server.

```sh
python3 src/server.py
```

Do a simple load test

```sh
python3 src/parallel.py -v
```

# Object Parser

- [src/object_parser/object_parser.py](object_parser.py) parses JSON data and instantiate Python objects.
- [src/object_parser/oas.py](oas.py) converts domain-models to OAS.

## Example

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
