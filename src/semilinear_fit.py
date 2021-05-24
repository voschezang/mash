import numpy as np
import matplotlib.pyplot as plt
import sklearn.linear_model 
import sklearn.kernel_ridge
import sklearn.gaussian_process
import sklearn.gaussian_process.kernels

import plot
from plot import COLORS
from random_walk import random_linspace, smooth_noise, noise


def fit_bayesian(x, y, x_out=None, M=9, frequencies=[], **kwds) -> dict:
    X = feature_matrix(x, M, frequencies)
    # X = np.vander(x, M + 1)
    model = sklearn.linear_model.BayesianRidge()
    model.fit(X, y)
    # prediction, std = model.predict(np.vander(x_out, M + 1), return_std=True)
    prediction, std = model.predict(feature_matrix(x_out, M, frequencies), return_std=True)
    return prediction, std


def feature_matrix(x, degree=3, frequencies=[1,2,3]):
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


if __name__ == '__main__':
    # init
    plt.style.use('./sci.mplstyle')
    np.random.seed(123)


    # generate arbitrary data
    def signal(x): 
        harmonics = 0.05 * np.sin(x * 6.4) + 0.3 * np.sin(x * 2.234 + 1) + 0.2 * np.sin(x * 0.8)
        polynomial = 0.0193 * x ** 2 - 0.2 * x + 1
        # add peridoic noise 
        noise = np.random.normal(0, scale=0.2, size=x.size) * np.sin(x * 1.47) * 0.25
        return 0.5 * harmonics + polynomial + noise 

    # bayesian regression
    n = 25
    offset = 0.3
    x_random = offset + np.hstack([np.random.gamma(2, size=n//2), 7 + np.random.gamma(3, size=n//2)])
    x_random.sort()
    x_max = x_random.max() * 1.05 + offset
    x_linear = np.linspace(0, x_max, 1000)
    y = signal(x_random)

    # fig = plt.figure(figsize=(9,3))
    # ax = plt.gca()
    fig, axes = plt.subplots(1, 2, figsize=(9, 3))
    for i, ax in enumerate(axes):
        plt.sca(ax)

        if i == 0:
            mu, std = fit_bayesian(x_random, y, x_linear, M=7, frequencies=[0.8, 6.4])
            plt.title('Bayesian Regressian')
        else:
            # model = sklearn.kernel_ridge.KernelRidge()
            # note that using multiple linear kernels (e.g. dotproduct) allows for nonlinear models 
            kernel = sklearn.gaussian_process.kernels.DotProduct() \
                + sklearn.gaussian_process.kernels.DotProduct() \
                + sklearn.gaussian_process.kernels.DotProduct() \
                + sklearn.gaussian_process.kernels.WhiteKernel() \
                + sklearn.gaussian_process.kernels.RBF(0.1)
                # + sklearn.gaussian_process.kernels.Matern(0.2)
                # + sklearn.gaussian_process.kernels.ExpSineSquared()
            model = sklearn.gaussian_process.GaussianProcessRegressor(kernel=kernel)
            model.fit(x_random.reshape(-1,1), y)
            mu, std = model.predict(x_linear.reshape(-1,1), return_std=True)

            plt.title('Gaussian Process')

        factor = 1.645 # corresponding to C.I. of 90%
        std *= factor
        plt.plot(x_linear, mu, label=r'$\mu$', color='tab:orange')
        plt.fill_between(x_linear, mu - std, mu + std, label='90% C.I.', alpha=0.2, color='tab:orange')

        # plot original input over prediction
        plt.scatter(x_random, y, label='Original signal', s=9, alpha=0.8, color='tab:blue')

        plt.ylim(0, 2.3)
        plot.grid()
        plot.locator()

    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
    plt.tight_layout()
    plot.save_fig('img/bayesian_fits')

