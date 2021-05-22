import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import scipy.stats
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


def fit_linear_models_with_normalization(data={}):
    """ Linear regression after normalization the input.
    Supported functions that can normalized:
    - linear: `y = x`
    - quadratic: `y = x^2`
    - exponential `y = 2^x`
    
    Parameters
    ----------
        data : dict of format {name: series}
    """
    fitted = {}
    for k, v in data.items():
        y = v.copy()
        if 'quadratic' in k:
            y = np.sqrt(v)
        elif 'exponential' in k:
            y = np.log2(v)
        a, b, _, p_value, eta = scipy.stats.linregress(x, y)
        signficiant = p_value < 0.001
        if signficiant:
            eta *= 1
            z = np.array([x, x - eta, x + eta])
            y = a * z + b
            if 'quadratic' in k:
                y = y ** 2
            elif 'exponential' in k:
                y = 2 ** y
    
            fitted[k] = y
    return fitted


if __name__ == '__main__':
    # init
    plt.style.use('./sci.mplstyle')
    np.random.seed(113)

    # params
    n = 100
    x = np.linspace(1, 15, n)
    bias = 1
    linear = x * 3.14 + bias
    quadratic = x ** 2 + bias
    exponential = 2 ** x + bias
    
    # generate random data
    alpha = 0.8
    noise = lambda: random_walk(n, 1, mu=0, std=alpha)[:,0]
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

    # fit linear models
    prediction_1 = fit_linear_models_with_normalization(dataset_1)
    prediction_2 = fit_linear_models_with_normalization(dataset_2)

    # plot
    fig, axes = plt.subplots(1, 2, figsize=(9,3))
    for i, ax in enumerate(axes):
        plt.sca(ax)
        data = [dataset_1, dataset_2][i]
        fitted = [prediction_1, prediction_2][i]
        
        # compute maxima of all series
        x_max = 7
        y_max = 1.05 * max( max(y for x_, y in zip(x, row) if x_ < x_max)  for row in data.values() )
        
        for j, (k,v) in enumerate(data.items()):
            plt.plot(x, v, label=k.title(), color=COLORS[j])
            if k in fitted:
                y, lb, ub = fitted[k]
                plt.plot(x, y, '--', label=f'{k.title()} (fit)', alpha=0.5, color=COLORS[j])
                # plt.fill_between(x, lb, ub, alpha=0.1, color=COLORS[j])
            
            plt.xlim(1, x_max)
            plt.ylim(0, y_max)
            plot.grid()
            plot.locator()
    plt.legend(bbox_to_anchor=(1,1), loc="upper left")
    plot.save_fig('img/linear_fits')
