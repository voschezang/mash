import numpy as np
import numpy.linalg
import matplotlib.pyplot as plt
import scipy.stats
from sklearn.metrics import mean_squared_error as mse

import plot
from plot import COLORS
from data_science.random_walk import random_linspace, smooth_noise, noise


def fit_transform_dataset(
        data, x_in, x_out, fit_transform_func, *args, **kwds) -> dict:
    """ Helper function to fit multiple data series.
    """
    fitted = {}
    for k, v in data.items():
        prediction, significant = fit_transform_func(
            x_in, v.copy(), x_out, key=k, *args, **kwds)
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
    Similar to least-squares, using an analytical solution, but using non-linear (polynomial) basis functions.
    The solution is the maximum-likelihood solution, obtained by equating the derivative of the log-likelihood to zero.
    It assumes that datapoints are independent w.r.t. the model.

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
    # regularized solution: ```(aI + Phi^T Phi)^{-1} Phi^T \vec{y}``` where a
    # is the regularization factor
    weights = np.matmul(
        np.linalg.inv(
            regularize *
            np.eye(
                M +
                1) +
            np.matmul(
                Phi.T,
                Phi)),
        np.matmul(
            Phi.T,
            y))

    # validate model on original input
    y_prediction = np.matmul(np.vander(x, M + 1), weights)
    # compute relative root mean squared error
    rel_rmse = np.sqrt(mse(y, y_prediction)) / y.mean()
    significant = rel_rmse < 0.1

    # make fine-grained prediction
    prediction = np.matmul(np.vander(x_out, M + 1), weights)
    return prediction, significant


def plot_prediction(original=[], prediction=[]):
    """
    Parameters
    ----------
        original, prediction : list of dicts, with format:  [{name, series}]
    """
    fig, axes = plt.subplots(
        1, 2, figsize=(
            9, 3), gridspec_kw={
            'width_ratios': [
                2, 3]})
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


if __name__ == '__main__':
    # init
    plt.style.use('./sci.mplstyle')
    np.random.seed(113)

    # generate data, add input and output noise (i.e. randomize x, y)
    n = 100
    x_linear = np.linspace(0, 15, n)
    x = random_linspace(0, 15, n)
    x[0] = 0
    linear = 3.14 * x + 0.1
    quadratic = 0.81 * x ** 2 + 20
    exponential = 0.91 * 2 ** x + 50

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
        fit_transform_dataset(
            dataset_1,
            x,
            x_linear,
            fit_linear_model_with_normalization),
        fit_transform_dataset(dataset_2, x, x_linear, fit_linear_model_with_normalization)])

    plt.suptitle('Linear Regression')
    plot.save_fig('img/linear_fits')

    # polynomial regression (regularized)
    plot_prediction([dataset_1, dataset_2], [
        fit_transform_dataset(
            dataset_1,
            x,
            x_linear,
            fit_polynomial,
            regularize=.1),
        fit_transform_dataset(dataset_2, x, x_linear, fit_polynomial, regularize=.1)])

    plt.suptitle('Polynomial Regression')
    plot.save_fig('img/polynomial_fits')
