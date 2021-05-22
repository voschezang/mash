import matplotlib.pyplot as plt
import matplotlib.ticker as tck

COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']
HATCHES = ('-', '+', 'x', '\\', '*', 'o', 'O', '.')
# dot-dash syntax (0, (width_i, space_i, width_j, space_j, ..))
dot1, dot2, dot3 = (1, 1), (1, 2), (1, 3)
dash1, dash2, dash3 = (2, 1), (3, 1), (4, 1)
LINESTYLES = ['-', '--', '-.', ':',
              (0,  dot1 + dot1 + dash3), (0, dash3 + dash2 + dash1 + dot1),
              (0, dot1 + dot3),
              (0, dot1 + dot3),
              '-', '--', '-.', ':']


def save_fig(filename, ext='png', dpi='figure',
             transparent=True, bbox_inches='tight',
             **kwargs):
    fn = f'{filename}.{ext}'
    plt.savefig(fn, dpi=dpi, transparent=transparent,
                bbox_inches=bbox_inches, **kwargs)
    plt.show()
    return fn


def grid(discrete_x=False, ax=None):
    ax = plt.gca()
    ax.grid(which='major', linewidth=0.8, axis='y' if discrete_x else 'both')
    ax.grid(which='minor', linewidth=0.1,
            axis='y' if discrete_x else 'both', alpha=0.5)


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


def formatter(unit=None, decimals=1, eng=True,
              x=True, y=True, z=False):
    """ Major formatter.
    Use unit (e.g. `m`) for Engineering notation, unit_non_eng (e.g. `$`) otherwise.
    """
    ax = plt.gca()
    locator(x=x, y=y, z=z)
    if eng:
        formatter = tck.EngFormatter(unit, decimals, sep=u"\N{THIN SPACE}")
    else:
        formatter = tck.FormatStrFormatter(f'%.{decimals}g {unit}')

    if x:
        ax.xaxis.set_major_formatter(formatter)
    if y:
        ax.yaxis.set_major_formatter(formatter)
    if z:
        ax.yaxis.set_major_formatter(formatter)


def bar(*args, zorder=2, width=0.6, **kwds):
    """Wrapper for matplotlib.pyplot.bar.
    Change default arguments related to the background and margins.
    """
    return plt.bar(*args, zorder=zorder, width=width, **kwds)
