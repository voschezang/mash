import numpy as np
import matplotlib.pyplot as plt

def random_walk(n_timesteps=100, observations_per_timestep=10, eta=None, mu=0, std=0.01):
    """ Generate multiple uncorrelated random walks.
    ```X_t = X_{t-1} + \eta_t```
    where `X_0 = \mu`
    
    Parameters
    ----------
        n_timesteps : length of each random walk
        observations_per_timestep : number of uncorrelated walkers
        eta : a matrix of shape (n_timesteps, observations_per_timestep)
            This representing the deviations per timestep.
            Optional: override this to use a custom random distribution. 
            Otherwise the default _normal_ distribution is used.
        mu : initial mean            
        std : standard deviation of the normal distribution used for eta
    """
    if eta is None:
        # draw from normal distribution
        eta = np.random.normal(0, scale=std, 
                size=(n_timesteps, observations_per_timestep))
        
    # transform to random walk
    X = np.empty_like(eta)
    X[0, :] = mu    
    for i in range(1, eta.shape[0]):
        X[i] = X[i-1] + eta[i]
    return X


def geometric_random_walk(n_timesteps=100, observations_per_timestep=10, eta=None, mu=1, alpha=0.01):
    """ Generate multiple uncorrelated, geometric random walks.
    ```X_t = X_{t-1} + \eta_t```
    where `X_0 = \mu` and `eta_t \sim \mathcal{U}(\pm \alpha X_{t-1})`
    
    Parameters
    ----------
        n_timesteps : length of each random walk
        observations_per_timestep : number of uncorrelated walkers
        eta : a matrix of shape (n_timesteps, observations_per_timestep)
            This representing the deviations per timestep.
            Optional: override this to use a custom random distribution. 
            Otherwise the default _uniform_ distribution is used.
        mu : initial mean
        alpha : max absolute relative deviation per timestep per walker
    """
    if eta is None:
        # draw from normal distribution
        eta = np.random.uniform(-alpha, alpha, 
                size=(n_timesteps, observations_per_timestep))
        
    # transform to random walk
    X = np.empty_like(eta)
    X[0, :] = mu
    for i in range(1, eta.shape[0]):
        X[i] = X[i-1] + X[i-1] * eta[i]
    return X


def grid(discrete_x=False, ax=None):
    # TODO mv
    if ax is None:
        ax = plt.gca()
    ax.grid(which='major', linewidth=0.8, axis='y' if discrete_x else 'both')
    ax.grid(which='minor', linewidth=0.1, axis='y' if discrete_x else 'both', alpha=0.5)


def save_fig(filename, ext='png', dpi='figure',
             transparent=True, bbox_inches='tight',
             **kwargs):
    # TODO mv
    fn = f'{filename}.{ext}'
    plt.savefig(fn, dpi=dpi,transparent=transparent,
                bbox_inches=bbox_inches, **kwargs)
    plt.show()
    return fn
def plot_line_with_ranges(X=[], title='',
                          plot_range=True,
                          number_of_stds=1.,
                          label_mean=r'$\mu$',
                          label_range='Range',
                          label_std=None,
                          plot_legends=True,
                          ax=None):
    """ Plotting template for a single data-series

    Parameters
    ----------
        X : array or matrix containing the x-data (optional) and y-data
        plot_range : bool, whether to plot the range
        number_of_stds : number of standard deviations to consider
            If < 1 then no std is plotted
        label_* : the labels of the plotted objects
    """
    if ax is None:
        ax = plt.gca()

    if label_std is None:
        label_std = r'$\mu \pm ' + str(number_of_stds) + r'\sigma$'

    # cache
    mu = X.mean(axis=1)
    std = X.std(axis=1) * number_of_stds
    T = np.arange(X.shape[0])

    # plot
    plt.plot(mu, label=label_mean)
    ax.fill_between(T, X.min(axis=1), X.max(axis=1),
                    alpha=0.1, label=label_range)
    if number_of_stds > 0:
        ax.fill_between(T, mu - std, mu + std, alpha=0.3, label=label_std)

    # markup
    grid(ax=ax)
    ax.set_title(title)
    if plot_legends:
        ax.legend()


def plot_lines_with_ranges(data={}, figsize=(9, 5), markup_func=lambda ax: None, **kwargs):
    """ Plotting template for multiple data-series

    Parameters
    ----------
            data : dict of format `{key: matrix }`
                Where `matrix` contains the observations per timesteps.
            figsize : matplotlib.pyplot figsize
            markup_func : function to add custom markup per subplot
                It's input must be `plt.AxesSubplot`
    """
    fig, axes = plt.subplots(1, len(data.keys()), figsize=figsize)
    for i, (key, X) in enumerate(data.items()):
        ax = axes[i]
        plt.sca(ax)
        plot_line_with_ranges(X, key.title(), ax=ax, **kwargs)
        markup_func(ax)

    return fig

if __name__ == '__main__':
    plt.style.use('./sci.mplstyle')
    np.random.seed(113)
    n_timesteps = 16
    observations_per_timestep = 100
    mu = 10
    data = {'linear': random_walk(n_timesteps, observations_per_timestep, mu=mu),
            'geometric': geometric_random_walk(n_timesteps, observations_per_timestep, mu=mu)
           }

    markup_func = lambda ax: ax.set_ylim(mu * 0.95, mu * 1.1)
    plot_lines_with_ranges(data, markup_func=markup_func, number_of_stds=1.5)
    fn = save_fig('img/random_walks')
    print(f'saved to {fn}')
