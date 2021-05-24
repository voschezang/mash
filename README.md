# Template for Data Science

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
Note that the fit for noisy exponential signal on the right-most plot is poor.

<img src="img/polynomial_fits.png" style="max-width: 10%" alt="Plot of polynomial regression fits">

## Semi-linear Models

[src/semilinear_fit.py](src/semilinear_fit.py) fits various non-linear models.

1. Bayesian ridge regression, with polynomial and sinoid basis functions.
2. A Gaussian Process. 

Note that these models estimate both a mean and a standard deviation, which can be used to define a confidence interval (C.I.).

<img src="img/bayesian_fits.png" style="max-width: 10%" alt="Plot of bayesian regression fits">


# Setup
```
pip3 install -r requirements.txt
```

## Test
Pytest will automatically find the relevant test modules.
```
pytest
```

## Run
```
python3 src/random_walk.py
python3 src/linear_fit.py
```
