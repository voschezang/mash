import sys
if __name__ == '__main__':
    sys.path.append('src')

import numpy as np
import matplotlib.pyplot as plt

import plot
from data_science.random_walk import random_walk, geometric_random_walk

plt.style.use('./sci.mplstyle')
np.random.seed(123)


def always_true(x) -> bool:
    return 1


def discrete_derivative(x) -> bool:
    if x.shape[0] < 2:
        return 0
    return int(x[-1] > x[-2]) * 2 - 1


def first_order_generalization(x) -> bool:
    """Estimate future based on first order derivative.
    I.e. buy when value is increasing
    """
    return discrete_derivative(x)


def invert(x) -> bool:
    """Buy low sell high
    """
    return - discrete_derivative(x)


def apply_strategy(price, strategy):
    n = price.shape[0]
    debt = np.zeros(n)
    assets = np.zeros(n)
    for i in range(1, n):
        diff = strategy(price[:i]) * 0.01
        debt[i] = debt[i-1] - diff
        assets[i] = assets[i-1]
        if diff:
            assets[i] += price[i] / diff

    return assets, debt


def run(price, strategies=[]) -> dict:
    results = {k: np.zeros(n) for k in strategies}
    for s in strategies:
        assets, debt = apply_strategy(price, s)
        print(f'{assets[-1] - debt[-1]:.3f}', s)
        results[s] = assets, debt
    return results


if __name__ == '__main__':
    n = 100
    price = geometric_random_walk(n, 1).T[0] + np.linspace(0, 0.05, n) * 0
    plt.plot(price)

    strategies = [
        #     always_true,
        first_order_generalization,
        invert,
    ]
    results = run(price, strategies)

    plt.figure(figsize=(9, 6))
    plt.subplot(211)
    for i, s in enumerate(strategies):
        assets, debt = results[s]
        plt.plot(assets, plot.LINESTYLES[i], label=s.__name__)
    plt.legend(bbox_to_anchor=(1, .5))

    plt.subplot(212)
    for i, s in enumerate(strategies):
        assets, debt = results[s]
        plt.plot(debt, plot.LINESTYLES[i], label=s.__name__)
    plt.legend(bbox_to_anchor=(1, .5))

    plt.show()
