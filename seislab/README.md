<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:020818,50:0a1628,100:0c2340&height=220&section=header&text=SeisLab%20Enhanced&fontSize=70&fontColor=38bdf8&fontAlignY=40&desc=Professional%20Seismic%20Analysis%20%26%20SEG-Y%20Interpretation%20Toolkit&descAlignY=62&descColor=4a6a8a&animation=fadeIn&fontFamily=Trebuchet+MS" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![segyio](https://img.shields.io/badge/segyio-SEG--Y_I/O-0a3d62?style=for-the-badge)](https://github.com/equinor/segyio)
[![segysak](https://img.shields.io/badge/segysak-Reference-0369a1?style=for-the-badge)](https://github.com/trhallam/segysak)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com)
[![Version](https://img.shields.io/badge/Version-1.1_Enhanced-f0c040?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Status-Production_Ready-4ade80?style=for-the-badge)]()

<br/>

> *Industry-standard seismic interpretation incorporating professional workflows from `segysak` and `segyio` — built for real-world subsurface data analysis.*

<br/>

</div>

---

<br/>

## `01` &nbsp; Overview

**SeisLab Enhanced (v1.1)** is a production-ready seismic interpretation toolkit that integrates professional SEG-Y handling, advanced visualization, and industry-standard processing workflows. This release draws directly from `segysak` and `segyio` best practices, extending SeisLab into a full-featured environment capable of handling survey-scale seismic data.

Key improvements over the base version include chunked SEG-Y processing, multi-mode visualization, real-time cursor interaction, and high-resolution export — all within a native PyQt5 GUI.

<br/>

---

## `02` &nbsp; What's New in v1.1

<br/>

| Area | Enhancement |
|:---|:---|
| **SEG-Y I/O** | Full EBCDIC/binary header extraction, trace header DataFrames, coordinate scalar handling |
| **Visualization** | Amplitude, Wiggle, and Wiggle+VA display modes with AGC |
| **Performance** | Chunked loading (5 000 traces/chunk) for 100k+ trace surveys |
| **3D Data** | Inline, crossline, and timeslice extraction from organized cubes |
| **Interaction** | Real-time cursor tracking, point selection, amplitude readout |
| **Export** | PNG / PDF / SVG at configurable DPI; trace header CSV export |
| **Synthetic Data** | Multi-reflector models with structural dip and amplitude variation |

<br/>

---

## `03` &nbsp; SEG-Y Data Handling

<br/>

### Header Management

SeisLab Enhanced provides complete header introspection aligned with industry workflows:

- **Text Header** — Full EBCDIC header extraction and display
- **Binary Header** — All standard binary file header fields parsed
- **Trace Headers** — Pandas DataFrame-based management for QC and geometry validation
- **Coordinate Handling** — Proper CDP scalar application per SEG-Y standard
- **Geometry Detection** — Automatic inline / crossline range inference

<br/>

### Standard Byte Locations

```python
byte_locations = {
    'iline':        189,   # Inline number
    'xline':        193,   # Crossline number
    'cdp':           21,   # CDP number
    'cdp_x':        181,   # CDP X coordinate
    'cdp_y':        185,   # CDP Y coordinate
    'offset':        37,   # Source-receiver offset
    'scalar_coord':  71,   # Coordinate scalar
}
```

<br/>

### Chunked Loading for Large Surveys

```python
chunk_size = 5000  # traces per chunk

for start in range(0, total_traces, chunk_size):
    end = min(start + chunk_size, total_traces)
    # process chunk
    print(f"Loaded {end}/{total_traces} traces...")
```

> Handles surveys exceeding 100 000 traces with constant memory footprint and real-time progress feedback.

<br/>

### 3D Cube Organization

```python
# Organized cube shape
data_cube.shape = (n_inlines, n_crosslines, n_samples)

# Index-based access
inline_idx    = np.where(inlines     == iline_number)[0]
crossline_idx = np.where(crosslines  == xline_number)[0]
```

<br/>

---

## `04` &nbsp; Visualization

<br/>

### Display Modes

| Mode | Description | Best For |
|:---|:---|:---|
| **Amplitude** | High-quality image display with symmetric scaling | Regional mapping, attribute QC |
| **Wiggle** | Classic trace-by-trace wiggle plot with decimation | Detailed event analysis |
| **Wiggle + VA** | Wiggle with positive variable-area fill | Horizon interpretation, standard reporting |

<br/>

### Available Colormaps

```python
COLORMAPS = {
    'seismic'  : 'RdBu_r',    # Classic seismic diverging
    'gray'     : 'gray',       # Grayscale
    'RdBu_r'   : 'RdBu_r',    # Red-Blue reversed
    'RdGy'     : 'RdGy',       # Red-Gray
    'PuOr'     : 'PuOr',       # Purple-Orange
    'viridis'  : 'viridis',    # Perceptually uniform
    'plasma'   : 'plasma',     # High contrast
    'coolwarm' : 'coolwarm',   # Cool-warm diverging
}
```

<br/>

### Automatic Gain Control (AGC)

```python
def _apply_agc(data):
    """Running RMS window AGC — preserves relative amplitude within window."""
    # Per-trace normalization via running RMS
    # Window length configurable
    # Vectorized NumPy implementation
```

<br/>

### Professional Plot Styling

```python
# Grid
ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.5, color='#888888')

# Spines
for spine in ax.spines.values():
    spine.set_edgecolor('#d0d0d0')
    spine.set_linewidth(1.5)

# Aspect ratio options: 'auto' | 'equal' | float
ax.imshow(data, aspect='auto')
```

<br/>

---

## `05` &nbsp; Synthetic Data Model

<br/>

The built-in synthetic generator produces geologically realistic test data:

```python
# Multi-reflector model
event_times       = [80, 150, 250, 350, 420]        # sample indices
event_amplitudes  = [1.2, 0.8, 1.5, 0.6, 1.0]
event_frequencies = [20,  25,  30,  22,  28]         # Hz

# Structural dip
dip_x = int(i * 0.3)
dip_y = int(j * 0.2)

# Lateral amplitude variation
amplitude_var = 0.8 + 0.4 * np.sin(i / 10) * np.cos(j / 8)

# Calibrated Gaussian noise
noise = np.random.normal(0, 0.08, n_samples)
```

**Validation assertions:**

```python
assert data.shape == (50, 50, 500)
assert np.abs(data).max() < 5.0
assert -1.0 < data.mean() < 1.0
```

<br/>

---

## `06` &nbsp; Interactive Features

<br/>

### Real-Time Cursor Tracking

```python
def on_mouse_move(event):
    trace, sample = get_mouse_position(event)
    amplitude = data[trace, sample]
    display_cursor_info(trace, sample, amplitude)
```

### Point Selection

```python
def on_canvas_click(event):
    # Emits: point_selected(trace, sample, amplitude)
    # Applications: amplitude QC, horizon picking, well tie
```

<br/>

---

## `07` &nbsp; Usage Examples

<br/>

**Load a SEG-Y file and inspect headers**

```python
from seismic.segy_loader import SegyLoader

loader = SegyLoader('seismic_data.sgy')
loader.load_data()

print(loader.get_text_header())
print(loader.binary_header)
print(f"Inlines: {loader.n_inlines}  |  Crosslines: {loader.n_crosslines}")

df = loader.get_trace_header_dataframe()
print(df.head())
```

<br/>

**Advanced visualization with AGC**

```python
from gui.segy_viewer import SeismicViewer

viewer = SeismicViewer()
viewer.agc_checkbox.setChecked(True)
viewer.display_section(data)

viewer.mode_combo.setCurrentText('Wiggle + VA')
viewer.cmap_combo.setCurrentText('RdBu_r')
viewer.export_figure('section.png', dpi=300)
```

<br/>

**Chunked processing and slice extraction**

```python
loader = SegyLoader('large_survey.sgy')
loader.load_data()                         # chunked internally

inline_data = loader.get_inline(100)
xline_data  = loader.get_crossline(200)
timeslice   = loader.get_timeslice(300)
```

<br/>

**Depth conversion integration**

```python
from scipy.interpolate import RegularGridInterpolator

velocity_loader = SegyLoader('velocity.sgy')
seismic_loader  = SegyLoader('seismic.sgy')

vel_interp = RegularGridInterpolator(
    (il_idx, xl_idx, time_idx),
    velocity_cube
)

for il in range(n_inlines):
    for xl in range(n_crosslines):
        trace       = seismic_loader.get_trace(il, xl)
        depth_trace = convert_time_to_depth(trace, velocity)
```

<br/>

---

## `08` &nbsp; Performance

<br/>

| Technique | Implementation |
|:---|:---|
| **Chunked I/O** | 5 000 trace chunks — constant memory regardless of survey size |
| **Vectorized AGC** | `agc_data = data / rms_values[:, np.newaxis]` |
| **Wiggle Decimation** | `skip = max(1, n_traces // max_wiggles)` — adaptive for display performance |
| **NumPy Broadcasting** | All attribute computations fully vectorized |

<br/>

---

## `09` &nbsp; Feature Comparison

<br/>

| Feature | Reference Notebooks | SeisLab Enhanced |
|:---|:---:|:---:|
| Header Reading | ✅ segysak | ✅ segyio + custom |
| Geometry Detection | ✅ Automatic | ✅ Automatic |
| Chunked Loading | ✅ Yes | ✅ Yes |
| 3D Cube | ✅ xarray | ✅ NumPy |
| Visualization | ✅ matplotlib | ✅ matplotlib + Qt |
| AGC | ✅ Custom | ✅ Custom |
| Wiggle Display | ✅ Basic | ✅ Advanced |
| Real-Time Interaction | ❌ Static | ✅ Live cursor + click |
| Export | ✅ PNG | ✅ PNG / PDF / SVG |

<br/>

---

## `10` &nbsp; Roadmap

<br/>

```
  ✅  SEG-Y loader with full header support
  ✅  Multi-mode visualization (Amplitude / Wiggle / Wiggle+VA)
  ✅  AGC, colormaps, high-res export
  ✅  Chunked processing for large surveys
  ✅  Real-time interactive cursor and point selection

  🔲  xarray integration for labeled dimensions
  🔲  Interactive velocity analysis & picking
  🔲  Time-to-depth conversion module
  🔲  Well log overlay and correlation
  🔲  ML-based horizon auto-picking
  🔲  Spectral decomposition (FFT / CWT)
  🔲  AVO / AVA amplitude analysis
  🔲  SEG-Y write-back for modified data
```

<br/>

---

## `11` &nbsp; Author

<br/>

<div align="center">

### Md Ashraf

**M.Sc (Tech) Applied Geophysics**
*Indian Institute of Technology (ISM) Dhanbad*

<br/>

`Geophysical Data Analysis` &nbsp;·&nbsp; `Seismic Interpretation` &nbsp;·&nbsp; `Python for Subsurface Analytics` &nbsp;·&nbsp; `ML in Geoscience`

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-ashraf--iit--ism-181717?style=for-the-badge&logo=github)](https://github.com/ashraf-iit-ism)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit_Site-0a66c2?style=for-the-badge&logo=google-chrome&logoColor=white)](https://your-portfolio-link.com)

</div>

<br/>

---

## `12` &nbsp; License

Released under the **MIT License** — see [`LICENSE`](./LICENSE) for details.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0c2340,50:0a1628,100:020818&height=100&section=footer" width="100%"/>

<br/>

*Based on `segysak` · `segyio` · industry best practices*

</div>
