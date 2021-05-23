# Template for Data Science

## Random walk

[Random walk](src/random_walk.py) generates datasets that behave like random walks.

<img src="img/random_walks.png" style="max-width: 10%" alt="Plot of Random Walks">

## Linear fit

[Linear fit](src/linear_fit.py) is an experiment that fits linear models to normalized input data, while assuming a specific function (e.g. quadratic or exponential).

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
