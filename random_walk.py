import numpy as np
import matplotlib.pyplot as plt
plt.style.use('./sci.mplstyle')
np.random.seed(123)

def random_walk(n_timesteps=100, observations_per_timestep=10, eta=None, mu=100):
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
            Otherwise the default _uniform_ distribution is used.
        mu : initial mean            
    """
    if eta is None:
        # draw from normal distribution
        eta = np.random.normal(0, scale=0.01, 
                size=(n_timesteps, observations_per_timestep))
        
    # transform to random walk
    X = np.empty_like(eta)
    X[0, :] = mu    
    for i in range(1, eta.shape[0]):
        X[i] = X[i-1] + eta[i]
    return X


def geometric_random_walk(n_timesteps=100, observations_per_timestep=10, eta=None, mu=100, alpha=0.01):
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

if __name__ == '__main__':
    n_timesteps = 16
    observations_per_timestep = 100
    mu = 10
    data = {'harmonic': random_walk(n_timesteps, observations_per_timestep, mu=mu),
            'geometric': geometric_random_walk(n_timesteps, observations_per_timestep, mu=mu)
           }

    fix, axes = plt.subplots(1, len(data.keys()), figsize=(9, 5))
    for i, (k, X) in enumerate(data.items()):
        ax = axes[i]
        X_mean = X.mean(axis=1)
        X_std = X.std(axis=1)
        T = np.arange(X.shape[0])
        ax.plot(X_mean, label=r'$\mu$')
        ax.fill_between(T, X.min(axis=1), X.max(axis=1), alpha=0.1, label='range')
        ax.fill_between(T, X_mean - X_std, X_mean + X_std, alpha=0.3, label=r'$\mu \pm \sigma$')
        grid(ax=ax)
        ax.set_title(k.title())
        ax.set_ylim(mu * 0.95, mu * 1.1)
    plt.legend() # show only in last plot
    fn = save_fig('img/random_walks')
    print(f'saved to {fn}')
