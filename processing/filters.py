"""
Signal Processing Filters
Bandpass, gain control, and normalization
"""

import numpy as np
from scipy.signal import butter, filtfilt


class BandpassFilter:
    """Bandpass filter for seismic data."""
    
    def __init__(self, lowcut, highcut, sample_rate, order=4):
        """
        Initialize bandpass filter.
        
        Args:
            lowcut: Low cut frequency (Hz)
            highcut: High cut frequency (Hz)
            sample_rate: Sampling rate (Hz)
            order: Filter order
        """
        self.lowcut = lowcut
        self.highcut = highcut
        self.sample_rate = sample_rate
        self.order = order
        
        # Design filter
        nyquist = 0.5 * sample_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        
        self.b, self.a = butter(order, [low, high], btype='band')
        
    def apply(self, data):
        """
        Apply bandpass filter to data.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            Filtered 2D numpy array
        """
        if data.ndim == 1:
            return filtfilt(self.b, self.a, data)
        else:
            result = np.zeros_like(data)
            for i in range(data.shape[0]):
                result[i, :] = filtfilt(self.b, self.a, data[i, :])
            return result


class GainControl:
    """Automatic and manual gain control."""
    
    def __init__(self, gain_type='agc', window_size=50):
        """
        Initialize gain control.
        
        Args:
            gain_type: Type of gain ('agc', 'linear', 'exponential')
            window_size: Window size for AGC
        """
        self.gain_type = gain_type.lower()
        self.window_size = window_size
        
    def apply(self, data):
        """
        Apply gain control to data.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            Gain-adjusted 2D numpy array
        """
        if self.gain_type == 'agc':
            return self._apply_agc(data)
        elif self.gain_type == 'linear':
            return self._apply_linear_gain(data)
        elif self.gain_type == 'exponential':
            return self._apply_exponential_gain(data)
        else:
            return data
            
    def _apply_agc(self, data):
        """Apply Automatic Gain Control."""
        if data.ndim == 1:
            return self._agc_trace(data)
        else:
            result = np.zeros_like(data)
            for i in range(data.shape[0]):
                result[i, :] = self._agc_trace(data[i, :])
            return result
            
    def _agc_trace(self, trace):
        """Apply AGC to single trace."""
        n_samples = len(trace)
        output = np.zeros_like(trace)
        
        half_window = self.window_size // 2
        
        for i in range(n_samples):
            start = max(0, i - half_window)
            end = min(n_samples, i + half_window + 1)
            
            window = trace[start:end]
            rms = np.sqrt(np.mean(window ** 2))
            
            if rms > 1e-10:
                output[i] = trace[i] / rms
            else:
                output[i] = trace[i]
                
        return output
        
    def _apply_linear_gain(self, data):
        """Apply linear gain (time variant)."""
        if data.ndim == 1:
            n_samples = len(data)
            gain = np.linspace(1.0, 2.0, n_samples)
            return data * gain
        else:
            n_samples = data.shape[1]
            gain = np.linspace(1.0, 2.0, n_samples)
            return data * gain[np.newaxis, :]
            
    def _apply_exponential_gain(self, data):
        """Apply exponential gain."""
        if data.ndim == 1:
            n_samples = len(data)
            gain = np.exp(np.linspace(0, 1, n_samples))
            return data * gain
        else:
            n_samples = data.shape[1]
            gain = np.exp(np.linspace(0, 1, n_samples))
            return data * gain[np.newaxis, :]


class TraceNormalization:
    """Trace normalization methods."""
    
    def __init__(self, method='max_absolute'):
        """
        Initialize trace normalization.
        
        Args:
            method: Normalization method ('max_absolute', 'rms', 'mean')
        """
        self.method = method.lower()
        
    def apply(self, data):
        """
        Apply normalization to data.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            Normalized 2D numpy array
        """
        if data.ndim == 1:
            return self._normalize_trace(data)
        else:
            result = np.zeros_like(data)
            for i in range(data.shape[0]):
                result[i, :] = self._normalize_trace(data[i, :])
            return result
            
    def _normalize_trace(self, trace):
        """Normalize single trace."""
        if self.method == 'max_absolute':
            max_val = np.max(np.abs(trace))
            if max_val > 1e-10:
                return trace / max_val
            else:
                return trace
                
        elif self.method == 'rms':
            rms = np.sqrt(np.mean(trace ** 2))
            if rms > 1e-10:
                return trace / rms
            else:
                return trace
                
        elif self.method == 'mean':
            mean = np.mean(np.abs(trace))
            if mean > 1e-10:
                return trace / mean
            else:
                return trace
                
        else:
            return trace


class SmoothingFilter:
    """Smoothing filter for seismic data."""
    
    def __init__(self, kernel_size=5):
        """
        Initialize smoothing filter.
        
        Args:
            kernel_size: Size of smoothing kernel
        """
        self.kernel_size = kernel_size
        
    def apply(self, data):
        """
        Apply smoothing filter.
        
        Args:
            data: 2D numpy array
            
        Returns:
            Smoothed 2D numpy array
        """
        from scipy.ndimage import uniform_filter
        
        return uniform_filter(data, size=self.kernel_size)
