import numpy as np
import numpy.linalg
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import scipy.stats
import scipy.linalg
from  sklearn.linear_model import BayesianRidge
from sklearn.metrics import mean_squared_error as mse
from scipy.fft import fft, fftfreq, ifft

import plot
from plot import COLORS
from random_walk import random_walk, random_linspace, smooth_noise

TWO_PI = 2 * np.pi


if __name__ == '__main__':
    # generate arbitrary data and apply fft to find frequencies
    def signal(x): 
        return np.sin(x * 2.234) 

    x_max = 20
    dx = 0.123
    x = np.arange(0, x_max, dx)
    y = signal(x)
    n = x.size
    print('n', n)

    # full fft
    z = fft(y)
    frequencies = fftfreq(z.size, dx)
    full_reconstruction = np.mean([np.abs(z[i]) * np.cos(x * TWO_PI * frequencies[i] + np.angle(z[i]) )
        for i in range((z.size // 2)) ], axis=0)
    full_reconstruction = ifft(z).real

    # fft with aperiodic sampling 
    n_sample_points = 50
    n_frequencies = n // 2

    sample_indices = np.random.choice(np.arange(x.size), n_sample_points, replace=False)
    padded_signal = np.zeros(x.size)
    padded_signal[sample_indices] = y[sample_indices]

    z = fft(padded_signal)
    frequencies = fftfreq(z.size, dx)
    indices = np.argsort(np.abs(z)[:n_frequencies])
    z_clean = np.zeros_like(z)
    z_clean[indices] = z[indices]
    z_clean *= np.abs(z).sum() / np.abs(z_clean).sum()

    # peaks = sorted( zip( np.abs(z)[:n//2], np.angle(z)[:n//2], frequencies[:n//2] ), reverse=True )
    # amp, angle, freq = zip(*peaks[:n_frequencies])
    # reconstruction = np.mean([amp[i] * np.cos(x * TWO_PI * freq[i] + angle[i] )
    #     for i in range((n_frequencies)) ], axis=0)
    reconstruction = ifft(z_clean).real
    # reconstruction = ifft(z).real
    if n_frequencies < 5:
        print('top frequencies', frequencies[indices])


    plt.plot(x, y,  label='Original', alpha=0.2, lw=5, color='0')
    plt.plot(x, full_reconstruction,'--', label='Full Reconstruction')
    plt.plot(x, reconstruction,'--', label='Reconstruction')
    plt.scatter(x[sample_indices], padded_signal[sample_indices], s=12, alpha=0.9, color='0')
 
    plot.grid()
    plot.locator()
    plt.xlim(0, 6)
    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
    plt.title('FFT')
    plt.tight_layout()
    plot.save_fig('img/fft_fits')
