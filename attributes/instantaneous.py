"""
Instantaneous Attributes
Computed using Hilbert Transform
"""

import numpy as np
from scipy.signal import hilbert


class InstantaneousAmplitude:
    """Calculate instantaneous amplitude (envelope) using Hilbert transform."""
    
    def compute(self, data):
        """
        Compute instantaneous amplitude.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            2D numpy array of instantaneous amplitudes
        """
        if data.ndim == 1:
            # Single trace
            analytic_signal = hilbert(data)
            return np.abs(analytic_signal)
        else:
            # Multiple traces
            result = np.zeros_like(data, dtype=float)
            for i in range(data.shape[0]):
                analytic_signal = hilbert(data[i, :])
                result[i, :] = np.abs(analytic_signal)
            return result


class InstantaneousPhase:
    """Calculate instantaneous phase using Hilbert transform."""
    
    def compute(self, data):
        """
        Compute instantaneous phase.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            2D numpy array of instantaneous phases (in radians)
        """
        if data.ndim == 1:
            # Single trace
            analytic_signal = hilbert(data)
            return np.angle(analytic_signal)
        else:
            # Multiple traces
            result = np.zeros_like(data, dtype=float)
            for i in range(data.shape[0]):
                analytic_signal = hilbert(data[i, :])
                result[i, :] = np.angle(analytic_signal)
            return result


class InstantaneousFrequency:
    """Calculate instantaneous frequency using Hilbert transform."""
    
    def __init__(self, sample_rate=2.0):
        """
        Initialize instantaneous frequency calculator.
        
        Args:
            sample_rate: Sample rate in milliseconds
        """
        self.sample_rate = sample_rate
        
    def compute(self, data):
        """
        Compute instantaneous frequency.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            2D numpy array of instantaneous frequencies (in Hz)
        """
        if data.ndim == 1:
            return self._compute_trace(data)
        else:
            result = np.zeros_like(data, dtype=float)
            for i in range(data.shape[0]):
                result[i, :] = self._compute_trace(data[i, :])
            return result
            
    def _compute_trace(self, trace):
        """
        Compute instantaneous frequency for a single trace.
        
        Args:
            trace: 1D numpy array
            
        Returns:
            1D numpy array of instantaneous frequencies
        """
        # Get analytic signal
        analytic_signal = hilbert(trace)
        
        # Get instantaneous phase
        phase = np.unwrap(np.angle(analytic_signal))
        
        # Compute frequency as derivative of phase
        freq = np.diff(phase) / (2.0 * np.pi * self.sample_rate / 1000.0)
        
        # Pad to match original length
        freq = np.concatenate(([freq[0]], freq))
        
        return freq


class Envelope:
    """Calculate envelope attribute (same as instantaneous amplitude)."""
    
    def compute(self, data):
        """
        Compute envelope.
        
        Args:
            data: 2D numpy array
            
        Returns:
            2D numpy array of envelope values
        """
        return InstantaneousAmplitude().compute(data)


class Coherence:
    """Calculate coherence attribute (simplified version)."""
    
    def __init__(self, window_size=9):
        """
        Initialize coherence calculator.
        
        Args:
            window_size: Window size for coherence calculation
        """
        self.window_size = window_size
        
    def compute(self, data):
        """
        Compute coherence attribute.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            2D numpy array of coherence values
        """
        n_traces, n_samples = data.shape
        coherence = np.zeros_like(data)
        
        half_window = self.window_size // 2
        
        for i in range(half_window, n_traces - half_window):
            for j in range(half_window, n_samples - half_window):
                # Get window
                window = data[i - half_window:i + half_window + 1,
                            j - half_window:j + half_window + 1]
                
                # Calculate cross-correlation based coherence
                center_trace = window[half_window, :]
                correlations = []
                
                for k in range(window.shape[0]):
                    if k != half_window:
                        trace = window[k, :]
                        corr = np.corrcoef(center_trace, trace)[0, 1]
                        correlations.append(abs(corr))
                
                coherence[i, j] = np.mean(correlations) if correlations else 0
                
        return coherence
