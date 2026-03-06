"""
RMS Amplitude Attribute
Root Mean Square amplitude calculation
"""

import numpy as np


class RMSAmplitude:
    """Calculate RMS (Root Mean Square) amplitude attribute."""
    
    def __init__(self, window_size=25):
        """
        Initialize RMS amplitude calculator.
        
        Args:
            window_size: Size of moving window for RMS calculation
        """
        self.window_size = window_size
        
    def compute(self, data):
        """
        Compute RMS amplitude.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            2D numpy array of RMS amplitudes
        """
        if data.ndim == 1:
            # Single trace
            return self._compute_trace(data)
        else:
            # Multiple traces
            result = np.zeros_like(data)
            for i in range(data.shape[0]):
                result[i, :] = self._compute_trace(data[i, :])
            return result
            
    def _compute_trace(self, trace):
        """
        Compute RMS for a single trace.
        
        Args:
            trace: 1D numpy array
            
        Returns:
            1D numpy array of RMS values
        """
        n_samples = len(trace)
        rms = np.zeros(n_samples)
        
        half_window = self.window_size // 2
        
        for i in range(n_samples):
            # Define window
            start = max(0, i - half_window)
            end = min(n_samples, i + half_window + 1)
            
            # Compute RMS
            window_data = trace[start:end]
            rms[i] = np.sqrt(np.mean(window_data ** 2))
            
        return rms


class ReflectionStrength:
    """Calculate reflection strength attribute."""
    
    def compute(self, data):
        """
        Compute reflection strength (absolute amplitude).
        
        Args:
            data: 2D numpy array
            
        Returns:
            2D numpy array of reflection strength
        """
        return np.abs(data)


class Energy:
    """Calculate energy attribute."""
    
    def __init__(self, window_size=25):
        """
        Initialize energy calculator.
        
        Args:
            window_size: Size of moving window
        """
        self.window_size = window_size
        
    def compute(self, data):
        """
        Compute energy attribute.
        
        Args:
            data: 2D numpy array
            
        Returns:
            2D numpy array of energy values
        """
        if data.ndim == 1:
            return self._compute_trace(data)
        else:
            result = np.zeros_like(data)
            for i in range(data.shape[0]):
                result[i, :] = self._compute_trace(data[i, :])
            return result
            
    def _compute_trace(self, trace):
        """
        Compute energy for a single trace.
        
        Args:
            trace: 1D numpy array
            
        Returns:
            1D numpy array of energy values
        """
        n_samples = len(trace)
        energy = np.zeros(n_samples)
        
        half_window = self.window_size // 2
        
        for i in range(n_samples):
            start = max(0, i - half_window)
            end = min(n_samples, i + half_window + 1)
            
            window_data = trace[start:end]
            energy[i] = np.sum(window_data ** 2)
            
        return energy
