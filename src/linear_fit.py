import numpy as np
import numpy.linalg
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import scipy.stats
import scipy.linalg
from random_walk import random_walk

import plot
from plot import COLORS


def smooth_noise(n=100, width=30, noise=None):
    width = np.round(width)
    if noise is None:
        noise = np.random.random(n + width)
    else:
        n = noise.shape[0]
    assert width < n, f'incompatible width ({width}) for n: {n}'
    convolution = np.convolve(noise, np.ones(width), 'valid') / width
    return convolution[:n]


def fit_linear_models_with_normalization(data={}, x=None, x_out=None) -> dict:
    """ Linear regression after normalization the input.
    Supported functions that can normalized:
    - linear: `y = a x + b`
    - quadratic: `y = a x^2 + b`
    - exponential `y = a 2^x + b`
    
    A positive codomain is assumed. 

    Parameters
    ----------
        data : dict of format {name: series}
        x : the input data for the 
    """
    fitted = {}
    if x is None:
        x = np.linspace(0, 1, 100)
    if x_out is None:
        x_out = x
    for k, v in data.items():
        y = v.copy()
        bias = y.min()
        if 'quadratic' in k:
            y = np.sqrt(v - bias + 1e-9)
        elif 'exponential' in k:
            # add offset s.t. f(0) = 1
            y = np.log2(v - bias + 1)

        a, b, _, p_value, eta = scipy.stats.linregress(x, y)
        signficiant = p_value < 0.001
        if signficiant:
            y = a * x_out + b
            if 'quadratic' in k:
                y = y ** 2 + bias
            elif 'exponential' in k:
                y = 2 ** y + bias

            fitted[k] = y

    # discard parameter values as we're just interested in a pretty graph
    return fitted


def random_linspace(start, stop, num):
    x = np.random.uniform(start, stop, num)
    x.sort()
    return x


if __name__ == '__main__':
    # init
    plt.style.use('./sci.mplstyle')
    np.random.seed(113)

    # generate data, add input and output noise (i.e. randomize x, y)
    n = 100
    x_linear = np.linspace(0, 15, n)
    x = random_linspace(0, 15, n)
    x[0] = 0
    bias = 5.12
    linear = 3.14 * x + bias
    quadratic = 0.81 * x ** 2 + bias
    exponential = 0.91 * 2 ** x + bias

    # generate random data
    alpha = 0.8
    def noise(): return random_walk(n, 1, mu=0, std=alpha)[:, 0]
    dataset_1 = {
        'linear': linear + noise(),
        'quadratic': quadratic + noise(),
        'exponential': exponential + noise(),
    }

    alpha = 4
    dataset_2 = {
        'linear': linear * (1 + alpha * smooth_noise(n, n // 10)),
        'quadratic': quadratic * (1 + alpha * smooth_noise(n, n // 10)),
        'exponential': exponential * (1 + alpha * smooth_noise(n, n // 10)),
    }

    # discard non-positive part
    for dataset in (dataset_1, dataset_2):
        for v in dataset.values():
            np.clip(v, 1e-9, None, out=v)

    # fit linear models
    prediction_1 = fit_linear_models_with_normalization(dataset_1, x, x_out=x_linear)
    prediction_2 = fit_linear_models_with_normalization(dataset_2, x, x_out=x_linear)

    # plot
    fig, axes = plt.subplots(1, 2, figsize=(9, 3))
    for i, ax in enumerate(axes):
        plt.sca(ax)
        data = [dataset_1, dataset_2][i]
        fitted = [prediction_1, prediction_2][i]

        # compute maxima of all series
        x_max = 7
        y_max = 1.05 * max(max(y for x_, y in zip(x, row) if x_ < x_max)
                           for row in data.values())

        for j, (k, v) in enumerate(data.items()):
            plt.plot(x, v, label=k.title(), alpha=0.3, color=COLORS[j], lw=3)
            if k in fitted:
                plt.plot(x_linear, fitted[k], label=f'{k.title()} (fit)',
                         color=COLORS[j], lw=1)
                # plt.fill_between(x, lb, ub, alpha=0.1, color=COLORS[j])

            plt.xlim(1, x_max)
            plt.ylim(0, y_max)
            plot.grid()
            plot.locator()
    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
    plot.save_fig('img/linear_fits')
