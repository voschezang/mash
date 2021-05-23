# Template for Data Science

These scripts are not production-ready, rather they can be used as starting point for data-science related applications.

## Random walk

[Random walk](src/random_walk.py) generates datasets that behave like random walks.

<img src="img/random_walks.png" style="max-width: 10%" alt="Plot of Random Walks">

## Linear fit

[Linear fit](src/linear_fit.py) is an experiment that fits linear models to normalized input data, while assuming a specific function (e.g. quadratic or exponential).
This means that certain specific non-linear functions can be estimated.

<img src="img/linear_fits.png" style="max-width: 10%" alt="Plot of Linear fits">

# Setup
```
pip3 install -r requirements.txt
```

# Test
Pytest will automatically find the relevant test modules.
```
pytest
```

# Run
```
python3 src/random_walk.py
python3 src/linear_fit.py
```
