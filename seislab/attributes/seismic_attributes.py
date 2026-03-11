import inspect
import numpy as np
from scipy.signal import hilbert
from scipy.ndimage import (
    uniform_filter1d,
    uniform_filter,
    gaussian_filter,
    maximum_filter1d,
    minimum_filter1d
)


class SeismicAttributes:

    def __init__(self, sample_rate_ms=2.0):

        self.dt = sample_rate_ms / 1000.0
        self.eps = 1e-10

        self._dispatch = {
            "rms amplitude": self.rms_amplitude,
            "instantaneous amplitude": self.instantaneous_amplitude,
            "instantaneous phase": self.instantaneous_phase,
            "instantaneous frequency": self.instantaneous_frequency,
            "envelope": self.envelope,
            "maximum amplitude": self.maximum_amplitude,
            "minimum amplitude": self.minimum_amplitude,
            "dominant frequency": self.dominant_frequency,
            "sweetness": self.sweetness,
            "coherence": self.coherence,
            "variance": self.variance,
            "dip": self.dip,
            "azimuth": self.azimuth,
            "curvature": self.curvature
        }

    # -------------------------------------------------
    # MAIN ENTRY
    # -------------------------------------------------

    # def compute(self, data, attribute):

    #     attribute = attribute.lower().strip()

    #     if attribute not in self._dispatch:
    #         raise ValueError(f"Unknown attribute: {attribute}")

    #     func = self._dispatch[attribute]

    #     if data.ndim == 2:
    #         return func(data)

    #     elif data.ndim == 3:
    #         return self._compute_3d(data, func)

    #     else:
    #         raise ValueError("Data must be 2D or 3D")
        
    def compute_attribute(self, data, attribute_name, sample_axis=0, **kwargs):

        """
        GUI-compatible dispatcher for attribute computation.
        """

        key = attribute_name.lower().strip()

        if key not in self._dispatch:
            raise ValueError(f"Unknown attribute: {attribute_name}")

        func = self._dispatch[key]
        sig = inspect.signature(func)
        valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

        if data.ndim == 2:
            return func(data, **valid_kwargs)

        elif data.ndim == 3:
            return self._compute_3d(data, func, **valid_kwargs)

        else:
            raise ValueError("Input must be 2D or 3D seismic data")

    # -------------------------------------------------
    # HANDLE 3D CUBES
    # -------------------------------------------------

    # def _compute_3d(self, cube, func):

    #     samples, il, xl = cube.shape

    #     result = np.zeros_like(cube)

    #     for i in range(il):
    #         section = cube[:, i, :]
    #         result[:, i, :] = func(section)

    #     return result
    
    def _compute_3d(self, cube, func, **kwargs):

        samples, ilines, xlines = cube.shape
    
        result = np.zeros_like(cube)
    
        for i in range(ilines):
    
            section = cube[:, i, :]
    
            result[:, i, :] = func(section, **kwargs)
    
        return result

    # -------------------------------------------------
    # AMPLITUDE ATTRIBUTES
    # -------------------------------------------------

    def rms_amplitude(self, data, window=25):

        squared = data ** 2

        return np.sqrt(
            uniform_filter1d(squared, size=window, axis=0, mode="nearest")
        )

    def maximum_amplitude(self, data, window=25):

        return maximum_filter1d(data, size=window, axis=0)

    def minimum_amplitude(self, data, window=25):

        return minimum_filter1d(data, size=window, axis=0)

    # -------------------------------------------------
    # COMPLEX TRACE ATTRIBUTES
    # -------------------------------------------------

    def instantaneous_amplitude(self, data):

        analytic = hilbert(data, axis=0)

        return np.abs(analytic)

    def envelope(self, data):

        return self.instantaneous_amplitude(data)

    def instantaneous_phase(self, data):

        analytic = hilbert(data, axis=0)

        return np.angle(analytic)

    def instantaneous_frequency(self, data):

        analytic = hilbert(data, axis=0)

        phase = np.unwrap(np.angle(analytic), axis=0)

        freq = np.gradient(phase, axis=0) / (2*np.pi*self.dt)

        return np.abs(freq)

    # -------------------------------------------------
    # FREQUENCY ATTRIBUTES
    # -------------------------------------------------

    def dominant_frequency(self, data):

        analytic = hilbert(data, axis=0)

        real = np.real(analytic)
        imag = np.imag(analytic)

        dx = np.gradient(real, axis=0)
        dy = np.gradient(imag, axis=0)

        omega = np.sqrt(dx**2 + dy**2) / (
            np.sqrt(real**2 + imag**2) + self.eps
        )

        return omega / (2*np.pi)

    def sweetness(self, data):

        envelope = self.instantaneous_amplitude(data)

        freq = self.dominant_frequency(data)

        return envelope / np.sqrt(freq + self.eps)

    # -------------------------------------------------
    # STRUCTURAL ATTRIBUTES
    # -------------------------------------------------

    def coherence(self, data, ws=9, wt=5):

        sum_amp = uniform_filter(data, size=(ws, wt))
        sum_sq = uniform_filter(data**2, size=(ws, wt))

        coh = (sum_amp**2) / (sum_sq + self.eps)

        return np.clip(coh, 0, 1)

    def variance(self, data, ws=9, wt=5):

        mean = uniform_filter(data, size=(ws, wt))
        mean_sq = uniform_filter(data**2, size=(ws, wt))

        return mean_sq - mean**2

    def dip(self, data):

        smooth = gaussian_filter(data, sigma=(1.5,1))

        grad_t, grad_x = np.gradient(smooth)

        slope = -grad_x/(np.abs(grad_t)+self.eps)

        return np.degrees(np.arctan(slope))

    def azimuth(self, data):

        smooth = gaussian_filter(data, sigma=(1.5,1))

        grad_t, grad_x = np.gradient(smooth)

        az = np.degrees(np.arctan2(grad_t,grad_x))

        return (az+360)%360

    def curvature(self, data):

        smooth = gaussian_filter(data, sigma=(1.5,1))

        f_t,f_x = np.gradient(smooth)

        f_tt = np.gradient(f_t,axis=0)
        f_xx = np.gradient(f_x,axis=1)
        f_tx = np.gradient(f_t,axis=1)

        num = ((1+f_t**2)*f_xx) - (2*f_t*f_x*f_tx) + ((1+f_x**2)*f_tt)
        den = (1+f_t**2+f_x**2)**1.5 + self.eps

        return num/den
