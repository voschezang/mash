import numpy as np
import matplotlib.pyplot as plt
import sklearn.linear_model 
import sklearn.kernel_ridge
import sklearn.gaussian_process
import sklearn.gaussian_process.kernels
from sklearn.metrics import mean_squared_error as mse

import plot
from plot import COLORS


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
    def signal(x, noise_amount=0.25): 
        harmonics = 0.05 * np.sin(x * 6.4) + 0.3 * np.sin(x * 2.234 + 1) + 0.2 * np.sin(x * 0.8)
        polynomial = 0.0193 * x ** 2 - 0.2 * x + 1
        # add peridoic noise 
        noise = np.random.normal(0, scale=0.2, size=x.size) * np.sin(x * 1.47)
        return 0.5 * harmonics + polynomial + noise_amount * noise 

    # bayesian regression
    n = 70
    offset = 0.3
    x_random = offset + np.hstack([np.random.gamma(2, size=n//2), 7 + np.random.gamma(3, size=n//2)])
    x_random.sort()
    x_max = x_random.max() * 1.1 + offset
    x_linear = np.linspace(0, x_max, 1000)
    y_true = signal(x_linear, noise_amount=0)
    y_observed = signal(x_random)

    titles = ['Bayesian Regression', 'Gaussian Process']
    colors = ['tab:olive', 'tab:pink']
    linestyles = ['--', ':']
    fig, axes = plt.subplots(1, 2, figsize=(9, 3))
    for i, ax in enumerate(axes):
        plt.sca(ax)
        plt.title(titles[i])

        if i == 0:
            y_prediction, std = fit_bayesian(x_random, y_observed, x_linear, M=7, frequencies=[0.8, 6.4])
        else:
            # note that combining multiple linear kernels (e.g. dotproduct) allows for nonlinear models 
            kernel = sklearn.gaussian_process.kernels.DotProduct() \
                + sklearn.gaussian_process.kernels.DotProduct() \
                + sklearn.gaussian_process.kernels.DotProduct() \
                + sklearn.gaussian_process.kernels.WhiteKernel() \
                + sklearn.gaussian_process.kernels.RBF(0.1)
            model = sklearn.gaussian_process.GaussianProcessRegressor(kernel=kernel)
            model.fit(x_random.reshape(-1,1), y_observed)
            y_prediction, std = model.predict(x_linear.reshape(-1,1), return_std=True)


        rel_rmse = np.sqrt(mse(y_true, y_prediction)) / y_true.sum()
        rel_mae = np.abs(y_true - y_prediction).sum() / y_true.sum()
        print(f'{titles[i]:<20} rel mae: {rel_mae:.4f} \trel rmse: {rel_rmse:6f}')

        label = f'Prediction (accuracy: {100 - rel_mae * 100:.1f}%)'
        plt.plot(x_linear, y_prediction, linestyles[i], label=label, color=colors[i])
        if i == 0:
            extra_handles, extra_labels = ax.get_legend_handles_labels()

        # plot confidence interval using predicted std
        std_factor = 1.645 # corresponding to C.I. of 90%
        std *= std_factor
        plt.fill_between(x_linear, y_prediction - std, y_prediction + std, label='90% C.I.', alpha=0.1, color='tab:brown')

        # plot original input over prediction
        plt.scatter(x_random, y_observed, label='Observation', s=3, alpha=0.7, color='tab:gray')

        # plt.ylim(0, 2.3)
        plt.ylim(0, 3)
        plot.grid()
        plot.locator()

    # change label ordering in legend to: observed, predictions, CI
    handles, labels = ax.get_legend_handles_labels()
    first_handle = handles.pop(-1)
    first_label = labels.pop(-1)
    plt.legend([first_handle] + extra_handles + handles,
               [first_label] + extra_labels + labels,
               bbox_to_anchor=(1, 1), loc="upper left")

    plt.tight_layout()
    plot.save_fig('img/bayesian_fits')

    # plot possible futures by sampling from the gaussian process itself
    plt.figure(figsize=(7,2))
    plt.title('Possible Futures')
    x = np.linspace(0, x_max * 2, 1000)
    n_samples = 10
    plt.plot(x, model.sample_y(x.reshape(-1,1), n_samples), alpha=0.2, label='sampled')
    plt.tight_layout()
    plot.save_fig('img/bayesian_fits_future')

