# """
# SEG-Y Data Loader Module
# Handles loading and accessing SEG-Y seismic data
# """

# import numpy as np
# try:
#     import segyio
#     SEGYIO_AVAILABLE = True
# except ImportError:
#     SEGYIO_AVAILABLE = False
#     print("Warning: segyio not available. Using synthetic data for demonstration.")


# class SegyLoader:
#     """Class for loading and accessing SEG-Y seismic data."""
    
#     def __init__(self, filepath):
#         """
#         Initialize SEG-Y loader.
        
#         Args:
#             filepath: Path to SEG-Y file
#         """
#         self.filepath = filepath
#         self.segyfile = None
#         self.data = None
#         self.inlines = None
#         self.crosslines = None
#         self.sample_rate = None
#         self.n_samples = None
        
#     def load_data(self):
#         """Load SEG-Y file and extract metadata."""
#         if not SEGYIO_AVAILABLE:
#             # Create synthetic data for demonstration
#             self._create_synthetic_data()
#             return
            
#         try:
#             self.segyfile = segyio.open(self.filepath, ignore_geometry=True)
            
#             # Get trace data
#             self.data = segyio.tools.cube(self.segyfile)
            
#             # Get metadata
#             self.inlines = self.segyfile.ilines
#             self.crosslines = self.segyfile.xlines
#             self.sample_rate = segyio.tools.dt(self.segyfile) / 1000.0  # Convert to ms
#             self.n_samples = len(self.segyfile.samples)
            
#         except Exception as e:
#             raise Exception(f"Failed to load SEG-Y file: {str(e)}")
            
#     def _create_synthetic_data(self):
#         """Create synthetic seismic data for demonstration."""
#         # Create synthetic 3D seismic cube
#         n_inlines = 50
#         n_crosslines = 50
#         n_samples = 500
        
#         self.inlines = np.arange(n_inlines)
#         self.crosslines = np.arange(n_crosslines)
#         self.n_samples = n_samples
#         self.sample_rate = 2.0  # 2 ms
        
#         # Generate synthetic seismic data with realistic features
#         self.data = np.zeros((n_inlines, n_crosslines, n_samples))
        
#         for i in range(n_inlines):
#             for j in range(n_crosslines):
#                 # Create synthetic trace with events
#                 t = np.arange(n_samples)
                
#                 # Add several reflection events
#                 for event_time in [100, 200, 300, 400]:
#                     amplitude = np.random.uniform(0.5, 1.5)
#                     wavelet = amplitude * self._ricker_wavelet(t - event_time, 25)
#                     self.data[i, j, :] += wavelet
                    
#                 # Add some dip
#                 dip_shift = int((i + j) * 0.5)
#                 self.data[i, j, :] = np.roll(self.data[i, j, :], dip_shift)
                
#                 # Add noise
#                 noise = np.random.normal(0, 0.1, n_samples)
#                 self.data[i, j, :] += noise
                
#     def _ricker_wavelet(self, t, f):
#         """Generate Ricker wavelet."""
#         return (1 - 2 * (np.pi * f * t / 1000) ** 2) * np.exp(-(np.pi * f * t / 1000) ** 2)
        
#     def get_inline(self, inline_index):
#         """
#         Get inline section.
        
#         Args:
#             inline_index: Index of inline
            
#         Returns:
#             2D numpy array of seismic data
#         """
#         if self.data is None:
#             return None
            
#         if inline_index < 0 or inline_index >= len(self.inlines):
#             return None
            
#         return self.data[inline_index, :, :]
        
#     def get_crossline(self, crossline_index):
#         """
#         Get crossline section.
        
#         Args:
#             crossline_index: Index of crossline
            
#         Returns:
#             2D numpy array of seismic data
#         """
#         if self.data is None:
#             return None
            
#         if crossline_index < 0 or crossline_index >= len(self.crosslines):
#             return None
            
#         return self.data[:, crossline_index, :]
        
#     def get_timeslice(self, time_index):
#         """
#         Get time slice.
        
#         Args:
#             time_index: Index of time sample
            
#         Returns:
#             2D numpy array of seismic data
#         """
#         if self.data is None:
#             return None
            
#         if time_index < 0 or time_index >= self.n_samples:
#             return None
            
#         return self.data[:, :, time_index]
        
#     def get_trace(self, inline_index, crossline_index):
#         """
#         Get individual trace.
        
#         Args:
#             inline_index: Inline index
#             crossline_index: Crossline index
            
#         Returns:
#             1D numpy array of trace data
#         """
#         if self.data is None:
#             return None
            
#         return self.data[inline_index, crossline_index, :]
        
#     def get_info(self):
#         """
#         Get file information.
        
#         Returns:
#             Dictionary with file metadata
#         """
#         return {
#             'filepath': self.filepath,
#             'n_inlines': len(self.inlines) if self.inlines is not None else 0,
#             'n_crosslines': len(self.crosslines) if self.crosslines is not None else 0,
#             'n_samples': self.n_samples,
#             'sample_rate': self.sample_rate,
#             'inline_range': (self.inlines[0], self.inlines[-1]) if self.inlines is not None else (0, 0),
#             'crossline_range': (self.crosslines[0], self.crosslines[-1]) if self.crosslines is not None else (0, 0),
#         }
        
#     def close(self):
#         """Close SEG-Y file."""
#         if self.segyfile is not None:
#             self.segyfile.close()
            
#     def __del__(self):
#         """Destructor to ensure file is closed."""
#         self.close()
