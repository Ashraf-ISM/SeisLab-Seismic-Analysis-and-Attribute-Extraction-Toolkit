"""
Unified seismic attribute computation module.

Input convention follows seismic sections shaped as:
    (n_samples, n_traces)

The class can also handle (n_traces, n_samples) by setting sample_axis=1.
All methods return an attribute section with the same shape as the input.
"""

import inspect

import numpy as np
from scipy.ndimage import (
    gaussian_filter,
    maximum_filter1d,
    minimum_filter1d,
    uniform_filter,
    uniform_filter1d,
)
from scipy.signal import hilbert


class SeismicAttributes:
    """Compute seismic attributes from 2D sections."""

    def __init__(self, sample_rate_ms=2.0, eps=1e-10):
        self.sample_rate_ms = float(sample_rate_ms or 2.0)
        self.dt_seconds = max(self.sample_rate_ms / 1000.0, 1e-9)
        self.eps = float(eps)

        self._dispatch = {
            "rms": self.rms_amplitude,
            "rms amplitude": self.rms_amplitude,
            "instantaneous amplitude": self.instantaneous_amplitude,
            "inst amp": self.instantaneous_amplitude,
            "inst amplitude": self.instantaneous_amplitude,
            "inst_amp": self.instantaneous_amplitude,
            "envelope": self.envelope,
            "instantaneous phase": self.instantaneous_phase,
            "inst phase": self.instantaneous_phase,
            "inst_phase": self.instantaneous_phase,
            "instantaneous frequency": self.instantaneous_frequency,
            "inst freq": self.instantaneous_frequency,
            "inst_frequency": self.instantaneous_frequency,
            "inst_freq": self.instantaneous_frequency,
            "maximum amplitude": self.maximum_amplitude,
            "max amplitude": self.maximum_amplitude,
            "minimum amplitude": self.minimum_amplitude,
            "min amplitude": self.minimum_amplitude,
            "dominant frequency": self.dominant_frequency,
            "sweetness": self.sweetness,
            "coherence": self.coherence,
            "variance": self.variance,
            "dip": self.dip,
            "azimuth": self.azimuth,
            "curvature": self.curvature,
        }

    def _normalize_name(self, name):
        return " ".join(str(name).replace("-", " ").replace("_", " ").split()).strip().lower()

    def _ensure_window(self, size, minimum=3):
        size = int(size)
        size = max(minimum, size)
        if size % 2 == 0:
            size += 1
        return size

    def _prepare_input(self, data, sample_axis):
        arr = np.asarray(data)
        if arr.ndim != 2:
            raise ValueError(f"Expected a 2D section, got shape {arr.shape}")

        input_dtype = arr.dtype
        arr = np.asarray(arr, dtype=np.float64)
        arr = np.nan_to_num(arr, copy=False)

        if sample_axis == 0:
            transposed = False
            internal = arr
        elif sample_axis == 1:
            transposed = True
            internal = arr.T
        else:
            raise ValueError("sample_axis must be 0 or 1")

        return internal, transposed, input_dtype

    def _restore_output(self, arr, transposed, input_dtype):
        out = arr.T if transposed else arr
        if np.issubdtype(input_dtype, np.floating):
            return out.astype(input_dtype, copy=False)
        return out.astype(np.float32, copy=False)

    def _analytic_signal(self, arr_st):
        return hilbert(arr_st, axis=0)

    def _instantaneous_amplitude_internal(self, arr_st):
        return np.abs(self._analytic_signal(arr_st))

    def _instantaneous_phase_internal(self, arr_st):
        return np.angle(self._analytic_signal(arr_st))

    def _instantaneous_frequency_internal(self, arr_st):
        phase = np.unwrap(self._instantaneous_phase_internal(arr_st), axis=0)
        freq = np.gradient(phase, self.dt_seconds, axis=0) / (2.0 * np.pi)
        return np.abs(freq)

    def _dominant_frequency_internal(self, arr_st, window_samples=11):
        analytic = self._analytic_signal(arr_st)
        x = np.real(analytic)
        y = np.imag(analytic)

        dx_dt = np.gradient(x, self.dt_seconds, axis=0)
        dy_dt = np.gradient(y, self.dt_seconds, axis=0)

        omega = np.sqrt(dx_dt * dx_dt + dy_dt * dy_dt) / (np.sqrt(x * x + y * y) + self.eps)
        dom_freq = np.abs(omega) / (2.0 * np.pi)

        smooth_w = self._ensure_window(window_samples, minimum=3)
        dom_freq = uniform_filter1d(dom_freq, size=smooth_w, axis=0, mode="nearest")
        return dom_freq

    def compute_attribute(self, data, attribute_name, sample_axis=0, **kwargs):
        """
        Dispatch to the selected attribute.

        Args:
            data: 2D seismic section.
            attribute_name: UI/alias name for attribute.
            sample_axis: axis index representing samples (0 or 1).
            **kwargs: optional method-specific parameters.
        """
        key = self._normalize_name(attribute_name)
        method = self._dispatch.get(key)
        if method is None:
            options = ", ".join(sorted(set(self._dispatch.keys())))
            raise ValueError(f"Unknown attribute '{attribute_name}'. Supported: {options}")

        signature = inspect.signature(method)
        call_kwargs = {k: v for k, v in kwargs.items() if k in signature.parameters}
        if "sample_axis" in signature.parameters:
            call_kwargs.setdefault("sample_axis", sample_axis)

        return method(data, **call_kwargs)

    # ------------------------------------------------------------------
    # Amplitude attributes
    # ------------------------------------------------------------------
    def rms_amplitude(self, data, window_samples=25, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        win = self._ensure_window(window_samples)
        rms = np.sqrt(uniform_filter1d(arr_st * arr_st, size=win, axis=0, mode="nearest"))
        return self._restore_output(rms, transposed, input_dtype)

    def envelope(self, data, sample_axis=0):
        return self.instantaneous_amplitude(data, sample_axis=sample_axis)

    def maximum_amplitude(self, data, window_samples=25, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        win = self._ensure_window(window_samples)
        out = maximum_filter1d(arr_st, size=win, axis=0, mode="nearest")
        return self._restore_output(out, transposed, input_dtype)

    def minimum_amplitude(self, data, window_samples=25, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        win = self._ensure_window(window_samples)
        out = minimum_filter1d(arr_st, size=win, axis=0, mode="nearest")
        return self._restore_output(out, transposed, input_dtype)

    # ------------------------------------------------------------------
    # Complex trace attributes (Hilbert transform)
    # ------------------------------------------------------------------
    def instantaneous_amplitude(self, data, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        out = self._instantaneous_amplitude_internal(arr_st)
        return self._restore_output(out, transposed, input_dtype)

    def instantaneous_phase(self, data, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        out = self._instantaneous_phase_internal(arr_st)
        return self._restore_output(out, transposed, input_dtype)

    def instantaneous_frequency(self, data, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        out = self._instantaneous_frequency_internal(arr_st)
        return self._restore_output(out, transposed, input_dtype)

    # ------------------------------------------------------------------
    # Frequency attributes
    # ------------------------------------------------------------------
    def dominant_frequency(self, data, window_samples=11, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        out = self._dominant_frequency_internal(arr_st, window_samples=window_samples)
        return self._restore_output(out, transposed, input_dtype)

    def sweetness(self, data, window_samples=11, freq_floor_hz=1.0, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        env = self._instantaneous_amplitude_internal(arr_st)
        dom_freq = self._dominant_frequency_internal(arr_st, window_samples=window_samples)
        out = env / np.sqrt(np.maximum(dom_freq, float(freq_floor_hz)))
        return self._restore_output(out, transposed, input_dtype)

    # ------------------------------------------------------------------
    # Structural attributes
    # ------------------------------------------------------------------
    def coherence(self, data, window_samples=9, window_traces=5, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        ws = self._ensure_window(window_samples)
        wt = self._ensure_window(window_traces)
        n = float(ws * wt)

        # Semblance-style coherence in local windows.
        sum_amp = uniform_filter(arr_st, size=(ws, wt), mode="nearest") * n
        sum_sq = uniform_filter(arr_st * arr_st, size=(ws, wt), mode="nearest") * n

        out = (sum_amp * sum_amp) / (n * sum_sq + self.eps)
        out = np.clip(out, 0.0, 1.0)
        return self._restore_output(out, transposed, input_dtype)

    def variance(self, data, window_samples=9, window_traces=5, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        ws = self._ensure_window(window_samples)
        wt = self._ensure_window(window_traces)
        mean = uniform_filter(arr_st, size=(ws, wt), mode="nearest")
        mean_sq = uniform_filter(arr_st * arr_st, size=(ws, wt), mode="nearest")
        out = np.maximum(mean_sq - mean * mean, 0.0)
        return self._restore_output(out, transposed, input_dtype)

    def dip(self, data, sigma_samples=1.5, sigma_traces=1.0, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        smooth = gaussian_filter(arr_st, sigma=(float(sigma_samples), float(sigma_traces)), mode="nearest")
        grad_t, grad_x = np.gradient(smooth, axis=(0, 1))
        slope = -grad_x / (np.abs(grad_t) + self.eps)
        out = np.degrees(np.arctan(slope))
        return self._restore_output(out, transposed, input_dtype)

    def azimuth(self, data, sigma_samples=1.5, sigma_traces=1.0, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        smooth = gaussian_filter(arr_st, sigma=(float(sigma_samples), float(sigma_traces)), mode="nearest")
        grad_t, grad_x = np.gradient(smooth, axis=(0, 1))
        out = (np.degrees(np.arctan2(grad_t, grad_x)) + 360.0) % 360.0
        return self._restore_output(out, transposed, input_dtype)

    def curvature(self, data, sigma_samples=1.5, sigma_traces=1.0, sample_axis=0):
        arr_st, transposed, input_dtype = self._prepare_input(data, sample_axis)
        smooth = gaussian_filter(arr_st, sigma=(float(sigma_samples), float(sigma_traces)), mode="nearest")

        f_t, f_x = np.gradient(smooth, axis=(0, 1))
        f_tt = np.gradient(f_t, axis=0)
        f_xx = np.gradient(f_x, axis=1)
        f_tx = np.gradient(f_t, axis=1)

        num = ((1.0 + f_t * f_t) * f_xx) - (2.0 * f_t * f_x * f_tx) + ((1.0 + f_x * f_x) * f_tt)
        den = np.power(1.0 + f_t * f_t + f_x * f_x, 1.5) + self.eps
        out = num / den
        return self._restore_output(out, transposed, input_dtype)
