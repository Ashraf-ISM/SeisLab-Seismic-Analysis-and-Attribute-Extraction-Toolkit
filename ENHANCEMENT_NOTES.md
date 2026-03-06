<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:020818,30:061428,70:0a2244,100:0d3060&height=280&section=header&text=SeisLab&fontSize=100&fontColor=38bdf8&fontAlignY=44&desc=Professional%20Seismic%20Analysis%20and%20SEG-Y%20Interpretation%20Toolkit&descSize=18&descAlignY=64&descColor=4a7a9b&animation=fadeIn&fontFamily=Trebuchet+MS" width="100%"/>

</div>

## Overview

This enhanced version of SeisLab incorporates professional visualization and SEG-Y handling techniques from industry-standard workflows, particularly drawing from `segysak` and `segyio` best practices demonstrated in the reference notebooks.

## Key Enhancements Based on Reference Code

### 1. Enhanced SEG-Y Data Handling

#### Professional Header Management
```python
# Comprehensive header extraction (from segysak pattern)
- EBCDIC text header reading
- Binary file header parsing
- Trace header scraping with configurable byte locations
- Automatic geometry detection
```

**Implemented Features:**
- **Text Header**: Full EBCDIC header extraction and display
- **Binary Header**: Complete binary file header with all standard fields
- **Trace Headers**: DataFrame-based trace header management with pandas
- **Coordinate Handling**: Proper scalar application for CDP coordinates
- **Geometry Detection**: Automatic inline/crossline range detection

#### Byte Location Configuration
```python
byte_locations = {
    'iline': 189,      # Inline number
    'xline': 193,      # Crossline number
    'cdp': 21,         # CDP number
    'cdp_x': 181,      # CDP X coordinate
    'cdp_y': 185,      # CDP Y coordinate
    'offset': 37,      # Source-receiver offset
    'scalar_coord': 71 # Coordinate scalar
}
```

### 2. Advanced Visualization Techniques

#### Multiple Display Modes
Based on professional seismic interpretation workflows:

**1. Amplitude Display**
- High-quality matplotlib rendering
- Professional colormaps (seismic, RdBu, gray, etc.)
- Symmetric color scaling for seismic data
- Configurable interpolation (bilinear, bicubic, gaussian, nearest)

**2. Wiggle Display**
- Classic wiggle trace plotting
- Configurable trace decimation for performance
- Automatic trace normalization
- Variable area fill option

**3. Wiggle + Variable Area (VA)**
- Combined wiggle with positive amplitude fill
- Standard in seismic interpretation
- Better horizon and event visualization

#### AGC Implementation
```python
def _apply_agc(data):
    """
    Automatic Gain Control
    Based on reference implementation patterns
    """
    # Running RMS window
    # Per-trace normalization
    # Preserves relative amplitude within window
```

### 3. Professional Data Loading Patterns

#### Chunked Processing
From the depth-domain conversion reference:

```python
# Memory-efficient trace loading
chunk_size = 5000  # traces per chunk
for start in range(0, total_traces, chunk_size):
    end = min(start + chunk_size, total_traces)
    # Process chunk
    print(f"Processed {end}/{total_traces} traces...")
```

**Benefits:**
- Handles large SEG-Y files (100k+ traces)
- Memory-efficient processing
- Progress feedback
- Scalable to survey-scale data

#### 3D Cube Management
```python
# Proper 3D cube organization
data_cube.shape = (n_inlines, n_crosslines, n_samples)

# Index mapping
inline_idx = np.where(inlines == iline_number)[0]
crossline_idx = np.where(crosslines == xline_number)[0]
```

### 4. Enhanced Synthetic Data

#### Realistic Seismic Features
```python
# Multiple reflection events
event_times = [80, 150, 250, 350, 420]
event_amplitudes = [1.2, 0.8, 1.5, 0.6, 1.0]
event_frequencies = [20, 25, 30, 22, 28]

# Structural dip
dip_x = int(i * 0.3)
dip_y = int(j * 0.2)

# Lateral amplitude variation
amplitude_var = 0.8 + 0.4 * np.sin(i/10) * np.cos(j/8)

# Realistic noise
noise = np.random.normal(0, 0.08, n_samples)
```

**Improvements:**
- Multiple realistic reflectors
- Structural dip simulation
- Amplitude variations
- Frequency-dependent wavelets
- Calibrated noise levels

### 5. Interactive Features

#### Cursor Tracking
```python
# Real-time amplitude readout
on_mouse_move(event):
    trace, sample = get_mouse_position(event)
    amplitude = data[trace, sample]
    display_cursor_info(trace, sample, amplitude)
```

#### Point Selection
```python
# Click to select point
on_canvas_click(event):
    emit signal: point_selected(trace, sample, amplitude)
    # Can be used for:
    # - Amplitude analysis
    # - Horizon picking
    # - Quality control
```

### 6. Export Capabilities

#### Trace Header Export
```python
# Export headers to CSV for external analysis
loader.export_trace_headers('headers.csv')

# DataFrame format allows:
# - QC in Excel/Python
# - Geometry validation
# - Coordinate mapping
```

#### Figure Export
```python
# High-resolution figure export
viewer.export_figure('section.png', dpi=300)

# Supports:
# - PNG, PDF, SVG
# - Publication quality
# - Customizable DPI
```

## Implementation Highlights

### 1. Professional Color Schemes

```python
COLORMAPS = {
    'seismic': 'RdBu_r',      # Classic seismic
    'gray': 'gray',            # Grayscale
    'RdBu_r': 'RdBu_r',       # Red-Blue reversed
    'RdGy': 'RdGy',           # Red-Gray
    'PuOr': 'PuOr',           # Purple-Orange
    'viridis': 'viridis',     # Perceptually uniform
    'plasma': 'plasma',        # High contrast
    'coolwarm': 'coolwarm',   # Cool-warm diverging
}
```

### 2. Aspect Ratio Control

```python
# Auto aspect (maintains data proportions)
ax.imshow(data, aspect='auto')

# Equal aspect (1:1 pixels)
ax.imshow(data, aspect='equal')

# Custom aspect ratio
ax.imshow(data, aspect=2.0)
```

### 3. Grid and Annotation

```python
# Professional grid styling
ax.grid(True, alpha=0.25, linestyle='--', 
        linewidth=0.5, color='#888888')

# Spine formatting
for spine in ax.spines.values():
    spine.set_edgecolor('#d0d0d0')
    spine.set_linewidth(1.5)
```

## Usage Examples from Reference Code

### Example 1: Load with Header Inspection

```python
from seismic.segy_loader import SegyLoader

# Load file
loader = SegyLoader('seismic_data.sgy')
loader.load_data()

# Inspect headers
print(loader.get_text_header())
print(loader.binary_header)

# Check geometry
print(f"Inlines: {loader.n_inlines}")
print(f"Crosslines: {loader.n_crosslines}")

# View trace headers
df = loader.get_trace_header_dataframe()
print(df.head())
```

### Example 2: Advanced Visualization

```python
from gui.segy_viewer import SeismicViewer

viewer = SeismicViewer()

# Display with AGC
viewer.agc_checkbox.setChecked(True)
viewer.display_section(data)

# Switch to wiggle display
viewer.mode_combo.setCurrentText('Wiggle + VA')

# Change colormap
viewer.cmap_combo.setCurrentText('RdBu_r')

# Export high-res figure
viewer.export_figure('output.png', dpi=300)
```

### Example 3: Chunked Processing

```python
# Process large file efficiently
loader = SegyLoader('large_survey.sgy')
loader.load_data()  # Uses chunked loading internally

# Access data
inline_data = loader.get_inline(100)
xline_data = loader.get_crossline(200)
timeslice = loader.get_timeslice(300)
```

## Performance Optimizations

### 1. Memory Management

```python
# Chunked loading prevents memory overflow
chunk_size = 5000  # configurable

# Progress feedback for long operations
print(f"Loaded {end}/{total_traces} traces...")
```

### 2. NumPy Vectorization

```python
# Vectorized AGC
agc_data = data / rms_values[:, np.newaxis]

# Vectorized amplitude scaling
scaled = data * gain_curve
```

### 3. Selective Trace Display

```python
# Wiggle decimation for performance
skip = max(1, n_traces // max_wiggles)
for i in range(0, n_traces, skip):
    plot_trace(i)
```

## Testing and Validation

### Synthetic Data Validation

```python
# Verify synthetic data quality
assert data.shape == (50, 50, 500)
assert np.abs(data).max() < 5.0
assert -1.0 < data.mean() < 1.0

# Check frequency content
from scipy.fft import fft
spectrum = np.abs(fft(data[25, 25, :]))
dominant_freq = np.argmax(spectrum)
assert 15 < dominant_freq < 35  # Expected range
```

### Header Consistency

```python
# Validate geometry
assert len(loader.inlines) == loader.n_inlines
assert len(loader.crosslines) == loader.n_crosslines

# Check trace count
expected_traces = n_inlines * n_crosslines
assert loader.segyfile.tracecount == expected_traces
```

## Integration with Reference Workflows

### Time-to-Depth Conversion Ready

The enhanced loader provides all necessary components for depth conversion workflows like the reference notebook:

```python
# Access geometry for depth conversion
il_coords = loader.inlines
xl_coords = loader.crosslines
sample_times = loader.samples

# Trace-by-trace access
for il in range(n_inlines):
    for xl in range(n_crosslines):
        trace = loader.get_trace(il, xl)
        # Apply depth conversion
        depth_trace = convert_time_to_depth(trace, velocity)
```

### Velocity Cube Integration

```python
# Compatible with velocity cube workflows
velocity_loader = SegyLoader('velocity.sgy')
seismic_loader = SegyLoader('seismic.sgy')

# Interpolate velocity to seismic grid
# Following reference notebook pattern
from scipy.interpolate import RegularGridInterpolator
vel_interp = RegularGridInterpolator(
    (il_idx, xl_idx, time_idx),
    velocity_cube
)
```

## Comparison with Reference Code

| Feature | Reference Notebooks | SeisLab Enhanced |
|---------|-------------------|------------------|
| Header Reading | ✓ segysak | ✓ segyio + custom |
| Geometry Detection | ✓ Automatic | ✓ Automatic |
| Chunked Loading | ✓ Yes | ✓ Yes |
| 3D Cube | ✓ xarray | ✓ NumPy |
| Visualization | ✓ matplotlib | ✓ matplotlib + Qt |
| AGC | ✓ Custom | ✓ Custom |
| Wiggle Display | ✓ Basic | ✓ Advanced |
| Interactive | ✗ Static | ✓ Real-time |
| Export | ✓ PNG | ✓ PNG/PDF/SVG |

## Future Enhancements

Based on reference patterns that could be added:

1. **xarray Integration**: Use xarray for labeled dimensions
2. **Velocity Analysis**: Interactive velocity picking
3. **Depth Conversion**: Time-to-depth transformation
4. **Well Integration**: Well log overlay
5. **Horizon Auto-picking**: ML-based horizon detection
6. **Spectral Analysis**: FFT and frequency decomposition
7. **Amplitude Analysis**: AVO/AVA analysis tools
8. **Export to SEG-Y**: Write modified data back

## Conclusion

SeisLab Enhanced incorporates industry-standard practices from professional seismic interpretation workflows, making it production-ready for real-world seismic data analysis. The implementation balances performance, usability, and professional standards demonstrated in the reference notebooks.

---

**Version**: 1.1 Enhanced
**Based on**: segysak, segyio, industry best practices
**Status**: Production Ready
