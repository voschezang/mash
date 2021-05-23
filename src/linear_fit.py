import numpy as np
import numpy.linalg
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import scipy.stats
import scipy.linalg
from  sklearn.linear_model import BayesianRidge
from sklearn.metrics import mean_squared_error as mse
from scipy.fft import fft, fftfreq

import plot
from plot import COLORS
from random_walk import random_walk, random_linspace, smooth_noise


def fit_transform_dataset(data, x_in, x_out, fit_transform_func, *args, **kwds) -> dict:
    fitted = {}
    for k, v in data.items():
        y = v.copy()
        prediction, significant = fit_transform_func(x_in, v.copy(), x_out, key=k, *args, **kwds)
        if significant:
            fitted[k] = prediction

    # discard parameter values as we're just interested in a pretty graph
    return fitted

def fit_linear_model_with_normalization(x, y, x_out=None, key='') -> dict:
    """ Linear regression after normalization the input.
    Supported functions that can normalized:
    - linear: `y = a x + b`
    - quadratic: `y = a x^2 + b`
    - exponential `y = a 2^x + b`
    
    A positive codomain is assumed. 

    Parameters
    ----------
        x,y : arrays containing input data 
        x_out : (optional) array containing the x-data for the prediction
            Defaults to x.
        key : string used to select the normalization function

    Returns
    -------
        prediction : array
        significant : bool
    """
    bias = y.min()
    if 'quadratic' in key:
        y = np.sqrt(y - bias + 1e-9)
    elif 'exponential' in key:
        # add offset s.t. f(0) = 1
        y = np.log2(y - bias + 1)

    a, b, _, p_value, eta = scipy.stats.linregress(x, y)
    signficiant = p_value < 0.001

    y = a * x_out + b
    if 'quadratic' in key:
        y = y ** 2 + bias
    elif 'exponential' in key:
        y = 2 ** y + bias

    return y, signficiant


def fit_polynomial(x, y, x_out=None, M=9, regularize=0, **kwds) -> dict:
    """ Polynomial regression.
    Similar to Least-squares, using an analytical solution, but not really linear anymore.
    The solution is the maximum-likelihood solution of an N-th order polynomial.

    Parameters
    ----------
        x,y : arrays containing input data 
        x_out : (optional) array containing the x-data for the prediction
            Defaults to x.
        M : order or degree of the polynomial
        regularize : non-negative float, this factor determines the amount of regularization

    Returns
    -------
        prediction : array
        significant : bool
    """
    if x_out is None:
        x_out = x

    # Vandermonde matrix: https://en.wikipedia.org/wiki/Vandermonde_matrix
    Phi = np.vander(x, M + 1)

    # fit
    # non-regularized solution: ```(Phi^T Phi)^{-1} Phi^T \vec{y}```
    # regularized solution: ```(aI + Phi^T Phi)^{-1} Phi^T \vec{y}``` where a is the regularization factor
    weights = np.matmul(np.linalg.inv(regularize * np.eye(M+1) + np.matmul(Phi.T, Phi)), np.matmul(Phi.T, y))

    # validate model on original input
    y_prediction = np.matmul(np.vander(x, M + 1), weights)
    # compute relative root mean squared error
    rel_rmse = np.sqrt(mse(y, y_prediction)) / y.mean()
    significant = rel_rmse <  0.1

    # make fine-grained prediction
    prediction = np.matmul(np.vander(x_out, M + 1), weights)
    return prediction, significant


def fit_bayesian(x, y, x_out=None, M=9, frequencies=[], **kwds) -> dict:
    X = feature_matrix(x, M, frequencies)
    # X = np.vander(x, M + 1)
    model = BayesianRidge()
    model.fit(X, y)
    # prediction, std = model.predict(np.vander(x_out, M + 1), return_std=True)
    prediction, std = model.predict(feature_matrix(x_out, M, frequencies), return_std=True)
    return prediction, std

def feature_matrix(x, degree=3, frequencies=[1,2,3]):
    # TODO find frequencies using a fourier tranform
    polynomial = np.vander(x, degree + 1)
    harmonic = np.sin(np.outer(x, frequencies))
    return np.hstack([polynomial, harmonic])


def plot_prediction(original=[], prediction=[]):
    """
    Parameters
    ----------
        original, prediction : list of dicts, with format:  [{name, series}]
    """
    fig, axes = plt.subplots(1, 2, figsize=(9, 3), gridspec_kw={'width_ratios': [2, 3]} )
    for i, ax in enumerate(axes):
        plt.sca(ax)
        data = original[i]

        # compute maxima of all series
        x_max = 7
        y_max = 1.05 * max(max(y for x_, y in zip(x, row) if x_ < x_max)
                           for row in data.values())

        for j, (k, v) in enumerate(data.items()):
            plt.plot(x, v, label=k.title(), alpha=0.3, color=COLORS[j], lw=3)
            if k in prediction[i]:
                plt.plot(x_linear, prediction[i][k], label=f'{k.title()} (fit)',
                         color=COLORS[j], lw=1)
                # plt.fill_between(x, lb, ub, alpha=0.1, color=COLORS[j])

            plt.xlim(1, x_max)
            plt.ylim(0, y_max)
            plot.grid()
            plot.locator()

    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")


def noise(n, std): 
    return random_walk(n, 1, mu=0, std=std)[:, 0]


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
    linear = 3.14 * x + 60
    quadratic = 0.81 * x ** 2 + 21
    exponential = 0.91 * 2 ** x + bias

    # generate random data
    alpha = 0.8
    dataset_1 = {
        'linear': linear + noise(n, alpha),
        'quadratic': quadratic + noise(n, alpha),
        'exponential': exponential + noise(n, alpha),
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

    # linear regression
    plot_prediction([dataset_1, dataset_2], [
        fit_transform_dataset(dataset_1, x, x_linear, fit_linear_model_with_normalization),
        fit_transform_dataset(dataset_2, x, x_linear, fit_linear_model_with_normalization)])

    plt.title('Linear Regression')
    plot.save_fig('img/linear_fits')

    # polynomial regression (regularized)
    plot_prediction([dataset_1, dataset_2], [
        fit_transform_dataset(dataset_1, x, x_linear, fit_polynomial, regularize=.1),
        fit_transform_dataset(dataset_2, x, x_linear, fit_polynomial, regularize=.1)])

    plt.title('Polynomial Regression')
    plot.save_fig('img/polynomial_fits')



    # generate data and apply fft to find frequencies
    def signal(x): 
        return np.sin(x * 3.234) + np.sin(x * 0.8) + 1.213 * x ** 2 - x + 3 + np.random.normal(0, scale=0, size=x.size)

    n = 100
    x_max = 5

    dx = 0.0124
    n_sample_points = 10
    x = np.arange(0, x_max, dx)
    sample_indices = np.random.choice(np.arange(x.size), n_sample_points, replace=False)
    padded_signal = np.zeros(x.size)
    padded_signal[sample_indices] = signal(x[sample_indices])
    z = fft(padded_signal)[:n//2]
    print(n, z.size, x.size)
    n_frequencies = 3
    peaks = sorted( zip( np.abs(z), fftfreq(z.size, dx)), reverse=True )
    frequencies = sorted([f for _, f in peaks if f >= 1e-6][:n_frequencies])
    print(frequencies)


    # bayesian regression
    x_linear = np.linspace(0, x_max * 1.25, n)
    x_random = random_linspace(0, x_max, n)
    y = signal(x_random)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3))
    for i, ax in enumerate(axes):
        plt.sca(ax)
        # y = [y1, y2][i]

        if i == 0:
            mu, std = fit_bayesian(x_random, y, x_linear, M=9)
        else:
            mu, std = fit_bayesian(x_random, y, x_linear, M=5, frequencies=frequencies)

        plt.plot(x_linear, mu, label=r'$\mu$', color='tab:orange')
        plt.fill_between(x_linear, mu - std, mu + std, label=r'$\sigma$', alpha=0.2, color='tab:orange')

        # plot original input over prediction
        plt.scatter(x_random, y, label='Original signal', s=12, alpha=0.9, color='tab:blue')

        if i == 1:
            # plot fft sample points
            plt.scatter(x[sample_indices], padded_signal[sample_indices], s=10, alpha=0.8, marker='x', color='0')
            plt.vlines(x[sample_indices], 0, padded_signal[sample_indices], linestyles='-', alpha=0.1, color='0')

        if i == 0:
            plt.ylim(0, 50)

        plot.grid()
        plot.locator()

    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
    plt.title('Bayesian Linear Regression')
    plot.save_fig('img/bayesian_fits')

