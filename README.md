![workflow-badge](https://github.com/voschezang/mash/actions/workflows/python-app.yml/badge.svg)

# Overview

In addition, there are some utilities.

In `src`:

- An object parser which converts JSON data to Python classes: `object_parser.py`.
- An OAS-generator for Python classes: `oas.py`.
- A parallelization framework for load testing: `parallel.py`.
- A shell that can interpret a domain-specific language: `shell.py`.
- A subshell wrapper, to redirect the output of shell scripts: `subshell.py`.

# Shell

See [shell](SHELL.md) and [reference](SHELL_REFERENCE.md).

<img src="img/shell_dropdown.png" style="max-width: 10%" alt="Example of a shell with a dropdown completion menu">

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

## Exammple

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
