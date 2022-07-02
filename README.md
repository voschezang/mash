# Template for Data Science

This repository contains a number of computational models which can be used for data science.

# Examples

Below are examples of various models, ranging from simple linear models with analytical solutions to more complex models with numerical solutions.

## Random walk

[src/random_walk.py](src/random_walk.py) generates datasets that behave like random walks.

<img src="img/random_walks.png" style="max-width: 10%" alt="Plot of Random Walks">

## Linear Models

[src/linear_fit.py](src/linear_fit.py) fits linear models. The simplicity of the models reduces overfitting, but this is not explicitly tested.

1. A linear regression model using normalized input data, while assuming a specific function (e.g. quadratic or exponential).

<img src="img/linear_fits.png" style="max-width: 10%" alt="Plot of Linear fits">

2. Polynomial regression. A linear model (w.r.t. the parameters) that uses non-linear basis functions.
Note that the fit for the exponential signal on the right-most plot is poor.

<img src="img/polynomial_fits.png" style="max-width: 10%" alt="Plot of polynomial regression fits">

## Semi-linear Models

[src/semilinear_fit.py](src/semilinear_fit.py) fits various non-linear models.

1. Bayesian ridge regression, with polynomial and sinoid basis functions.
2. A Gaussian Process. 

Note that these models estimate both a mean and a standard deviation, which can be used to define a confidence interval (C.I.).

The accuracy is derived using relative mean absolute error.
It is an overestimation because the test-data overlaps with the training-data.

<img src="img/bayesian_fits.png" style="max-width: 10%" alt="Plot of Bayesian regression and Gaussian Processes">

Sampling from the Gaussian Process produces a collection of possible futures.

<img src="img/bayesian_fits_future.png" style="max-width: 10%" alt="Plot of Predicted Future Possibilities">


# Setup

Using a `Makefile` for convenience.
```
make install
make test
```

## Run
```
python3 src/random_walk.py
python3 src/linear_fit.py
python3 src/semilinear_fit.py
```

# Parallelization Utilities

Some experiments with parallelization, concurrency and `asyncio` in Python.

## Test

Start a dummy server.
```
python3 src/server.py
```

Do a simple load test
```
python3 src/parallel.py -v
```

# Object Parser

- [src/object_parser.py](src/object_parser.py) parses JSON data and instantiate Python objects.
- [src/oas.py](src/oas.py) converts domain-models to OAS.

## Exammple

```sh
python src/object_parser_example.py
```

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

# DSL Generator

A tool to generate a [Domain-specific Language](https://en.wikipedia.org/wiki/Domain-specific_language) (DSL).

## Usage

Define a mapping between commands and functions.  Both Python functions and System-calls are supported.

### Example

See `src/dsl_example.py`.

```sh
# py src/dsl_example.py
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