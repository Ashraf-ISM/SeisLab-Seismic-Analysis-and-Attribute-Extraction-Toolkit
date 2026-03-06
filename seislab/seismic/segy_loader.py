"""
Enhanced SEG-Y Data Loader Module
Professional SEG-Y handling with header inspection and geometry management
Based on industry-standard practices from segysak and segyio
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple, List
try:
    import segyio
    SEGYIO_AVAILABLE = True
except ImportError:
    SEGYIO_AVAILABLE = False
    print("Warning: segyio not available. Using synthetic data for demonstration.")


class SegyLoader:
    """Class for loading and accessing SEG-Y seismic data."""

    def __init__(self, filepath):
        """
        Initialize SEG-Y loader.

        Args:
            filepath: Path to SEG-Y file
        """
        self.filepath = filepath
        self.segyfile = None
        self.data = None
        self.inlines = None
        self.crosslines = None
        self.sample_rate = None
        self.n_samples = None

    def _safe_len(self, value):
        """Return len(value) when possible, otherwise 0."""
        try:
            return len(value)
        except TypeError:
            return 0

    def _reshape_traces_to_cube(self, traces):
        """
        Fallback reshape for geometry-less files:
        keep native trace ordering as (trace, 1, sample) to avoid fake geometry.
        """
        n_traces, n_samples = traces.shape
        return traces.reshape(n_traces, 1, n_samples)

    def _build_cube_from_headers(self, traces):
        """
        Try to build a true (inline, crossline, sample) cube from trace headers.
        Returns (cube, inlines, crosslines) or (None, None, None) when unavailable.
        """
        try:
            il_vals = np.asarray(
                self.segyfile.attributes(segyio.TraceField.INLINE_3D)[:],
                dtype=np.int64
            )
            xl_vals = np.asarray(
                self.segyfile.attributes(segyio.TraceField.CROSSLINE_3D)[:],
                dtype=np.int64
            )
        except Exception:
            return None, None, None

        if il_vals.size == 0 or xl_vals.size == 0 or il_vals.size != xl_vals.size:
            return None, None, None

        inlines = np.unique(il_vals)
        crosslines = np.unique(xl_vals)
        if inlines.size < 2 or crosslines.size < 2:
            return None, None, None

        n_traces, n_samples = traces.shape
        i_idx = np.searchsorted(inlines, il_vals)
        x_idx = np.searchsorted(crosslines, xl_vals)

        cube = np.zeros((inlines.size, crosslines.size, n_samples), dtype=np.float32)
        counts = np.zeros((inlines.size, crosslines.size), dtype=np.int32)

        for t in range(n_traces):
            i = i_idx[t]
            x = x_idx[t]
            cube[i, x, :] += traces[t, :]
            counts[i, x] += 1

        # Reject highly sparse/irregular grids (likely not a real 3D survey).
        coverage = np.count_nonzero(counts) / counts.size
        if coverage < 0.90:
            return None, None, None

        # Average duplicate bins.
        nonzero = counts > 0
        cube[nonzero, :] /= counts[nonzero, np.newaxis]

        return cube, inlines, crosslines

    def load_data(self):
        """Load SEG-Y file and extract metadata."""
        if not SEGYIO_AVAILABLE:
            # Create synthetic data for demonstration
            self._create_synthetic_data()
            return

        try:
            # Use inferred geometry when available.
            self.segyfile = segyio.open(self.filepath, strict=False)

            # Read raw traces first so we can always form a valid data volume.
            traces = np.asarray(self.segyfile.trace.raw[:])
            if traces.ndim != 2:
                raise ValueError(f"Unexpected trace array shape: {traces.shape}")

            n_traces, n_samples = traces.shape
            if n_traces == 0 or n_samples == 0:
                raise ValueError("SEG-Y file contains no trace samples")

            # Sampling metadata can be missing in some files.
            sample_rate_us = segyio.tools.dt(self.segyfile)
            self.sample_rate = (sample_rate_us / 1000.0) if sample_rate_us else 1.0

            samples = getattr(self.segyfile, "samples", None)
            self.n_samples = self._safe_len(samples) or n_samples

            # Try to use segyio cube when geometry is valid.
            cube = None
            try:
                cube = segyio.tools.cube(self.segyfile)
            except Exception:
                cube = None

            if cube is not None and cube.ndim == 3:
                self.data = cube
                self.inlines = np.asarray(self.segyfile.ilines)
                self.crosslines = np.asarray(self.segyfile.xlines)
            else:
                # Try to recover geometry from trace headers.
                header_cube, header_il, header_xl = self._build_cube_from_headers(traces)
                if header_cube is not None:
                    self.data = header_cube
                    self.inlines = header_il
                    self.crosslines = header_xl
                else:
                    self.data = self._reshape_traces_to_cube(traces)
                    self.inlines = np.arange(self.data.shape[0])
                    self.crosslines = np.arange(self.data.shape[1])

            if self._safe_len(self.inlines) == 0:
                self.inlines = np.arange(self.data.shape[0])
            if self._safe_len(self.crosslines) == 0:
                self.crosslines = np.arange(self.data.shape[1])

        except Exception as e:
            raise Exception(str(e))

    def _create_synthetic_data(self):
        """Create synthetic seismic data for demonstration."""
        # Create synthetic 3D seismic cube
        n_inlines = 50
        n_crosslines = 50
        n_samples = 500

        self.inlines = np.arange(n_inlines)
        self.crosslines = np.arange(n_crosslines)
        self.n_samples = n_samples
        self.sample_rate = 2.0  # 2 ms

        # Generate synthetic seismic data with realistic features
        self.data = np.zeros((n_inlines, n_crosslines, n_samples))

        for i in range(n_inlines):
            for j in range(n_crosslines):
                # Create synthetic trace with events
                t = np.arange(n_samples)

                # Add several reflection events
                for event_time in [100, 200, 300, 400]:
                    amplitude = np.random.uniform(0.5, 1.5)
                    wavelet = amplitude * self._ricker_wavelet(t - event_time, 25)
                    self.data[i, j, :] += wavelet

                # Add some dip
                dip_shift = int((i + j) * 0.5)
                self.data[i, j, :] = np.roll(self.data[i, j, :], dip_shift)

                # Add noise
                noise = np.random.normal(0, 0.1, n_samples)
                self.data[i, j, :] += noise

    def _ricker_wavelet(self, t, f):
        """Generate Ricker wavelet."""
        return (1 - 2 * (np.pi * f * t / 1000) ** 2) * np.exp(-(np.pi * f * t / 1000) ** 2)

    def get_inline(self, inline_index):
        """
        Get inline section.

        Args:
            inline_index: Index of inline

        Returns:
            2D numpy array of seismic data
        """
        if self.data is None:
            return None

        if inline_index < 0 or inline_index >= len(self.inlines):
            return None

        return self.data[inline_index, :, :]

    def get_crossline(self, crossline_index):
        """
        Get crossline section.

        Args:
            crossline_index: Index of crossline

        Returns:
            2D numpy array of seismic data
        """
        if self.data is None:
            return None

        if crossline_index < 0 or crossline_index >= len(self.crosslines):
            return None

        return self.data[:, crossline_index, :]

    def get_timeslice(self, time_index):
        """
        Get time slice.

        Args:
            time_index: Index of time sample

        Returns:
            2D numpy array of seismic data
        """
        if self.data is None:
            return None

        if time_index < 0 or time_index >= self.n_samples:
            return None

        return self.data[:, :, time_index]

    def get_trace(self, inline_index, crossline_index):
        """
        Get individual trace.

        Args:
            inline_index: Inline index
            crossline_index: Crossline index

        Returns:
            1D numpy array of trace data
        """
        if self.data is None:
            return None

        return self.data[inline_index, crossline_index, :]

    def get_info(self):
        """
        Get file information.

        Returns:
            Dictionary with file metadata
        """
        return {
            'filepath': self.filepath,
            'n_inlines': len(self.inlines) if self.inlines is not None else 0,
            'n_crosslines': len(self.crosslines) if self.crosslines is not None else 0,
            'n_samples': self.n_samples,
            'sample_rate': self.sample_rate,
            'inline_range': (self.inlines[0], self.inlines[-1]) if self.inlines is not None else (0, 0),
            'crossline_range': (self.crosslines[0], self.crosslines[-1]) if self.crosslines is not None else (0, 0),
        }

    def close(self):
        """Close SEG-Y file."""
        if self.segyfile is not None:
            self.segyfile.close()

    def __del__(self):
        """Destructor to ensure file is closed."""
        self.close()
