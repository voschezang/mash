import matplotlib.pyplot as plt
import matplotlib.ticker as tck

COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']

def grid(discrete_x=False, ax=None):
    ax = plt.gca()
    ax.grid(which='major', linewidth=0.8, axis='y' if discrete_x else 'both')
    ax.grid(which='minor', linewidth=0.1, axis='y' if discrete_x else 'both', alpha=0.5)


def locator(x=True, y=True, z=False):
    ax = plt.gca()
    if x:
        ax.xaxis.set_major_locator(tck.AutoLocator())
        ax.xaxis.set_minor_locator(tck.AutoMinorLocator())
    if y:
        ax.yaxis.set_major_locator(tck.AutoLocator())
        ax.yaxis.set_minor_locator(tck.AutoMinorLocator())
    if z:
        ax.zaxis.set_major_locator(tck.AutoLocator())
        ax.zaxis.set_minor_locator(tck.AutoMinorLocator())

def save_fig(filename, ext='png', dpi='figure',
             transparent=True, bbox_inches='tight',
             **kwargs):
    fn = f'{filename}.{ext}'
    plt.savefig(fn, dpi=dpi,transparent=transparent,
                bbox_inches=bbox_inches, **kwargs)
    plt.show()
    return fn
