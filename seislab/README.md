<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:020818,30:061428,70:0a2244,100:0d3060&height=280&section=header&text=SeisLab&fontSize=100&fontColor=38bdf8&fontAlignY=44&desc=Professional%20Seismic%20Analysis%20and%20SEG-Y%20Interpretation%20Toolkit&descSize=18&descAlignY=64&descColor=4a7a9b&animation=fadeIn&fontFamily=Trebuchet+MS" width="100%"/>

</div>

<div align="center">

<br/>

[![Python](https://img.shields.io/badge/Python_3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-GUI_Framework-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com)
[![NumPy](https://img.shields.io/badge/NumPy-Computation-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557c?style=for-the-badge)](https://matplotlib.org)
[![segyio](https://img.shields.io/badge/segyio-SEG--Y_I/O-0a3d62?style=for-the-badge)](https://github.com/equinor/segyio)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Handling-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)

<br/>

[![Version](https://img.shields.io/badge/Version-1.1_Enhanced-38bdf8?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Status-In_Development-f97316?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-f0c040?style=for-the-badge)](./LICENSE)
[![Institution](https://img.shields.io/badge/IIT_(ISM)-Dhanbad-8b0000?style=for-the-badge)]()

<br/>

```
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░  Seismic Visualization  ·  Attribute Extraction     ░
  ░  SEG-Y Handling  ·  Interactive Interpretation      ░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

> *Built from scratch as part of my Applied Geophysics journey at IIT (ISM) Dhanbad —*
> *incorporating industry-standard workflows from `segysak` and `segyio` best practices.*

<br/>

</div>

---

<br/>

## 📌 &nbsp; Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [SEG-Y Data Handling](#-seg-y-data-handling)
- [Visualization](#-visualization)
- [Synthetic Data](#-synthetic-data)
- [Interactive Features](#-interactive-features)
- [Export Capabilities](#-export-capabilities)
- [Performance](#-performance)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Roadmap](#-roadmap)
- [Author](#-author)

<br/>

---

## 🌍 &nbsp; Overview

**SeisLab Enhanced (v1.1)** is a Python-based seismic data visualization and analysis toolkit I am building as part of my studies in Applied Geophysics at **IIT (ISM) Dhanbad**. The project integrates professional SEG-Y handling techniques, multi-mode interactive visualization, and industry-standard seismic attribute computation — all within a native desktop GUI built on PyQt5.

This version draws directly from the workflows and best practices demonstrated in **`segysak`** and **`segyio`** reference implementations, adapting them into an interactive application environment.

The aim is to create a **lightweight but capable seismic interpretation environment** suitable for learning, research, and rapid seismic attribute analysis — and to grow it steadily into a production-grade tool.

<br/>

---

## ✨ &nbsp; Key Features

<br/>

<table>
<tr>
<td width="50%">

**🗂️ SEG-Y Data Handling**
- Full EBCDIC text header extraction
- Binary file header parsing
- Trace header DataFrames via Pandas
- Coordinate scalar application
- Auto inline/crossline geometry detection
- Chunked loading for large surveys

</td>
<td width="50%">

**📊 Seismic Visualization**
- Amplitude image display
- Classic wiggle trace plotting
- Wiggle + Variable Area (VA) mode
- 8 professional colormaps
- Automatic Gain Control (AGC)
- Configurable interpolation modes

</td>
</tr>
<tr>
<td width="50%">

**🧮 Attribute Extraction**
- RMS Amplitude
- Instantaneous Amplitude
- Instantaneous Phase
- Instantaneous Frequency

</td>
<td width="50%">

**🖱️ Interactive Tools**
- Real-time cursor amplitude readout
- Click-to-select point analysis
- Live statistics panel
- High-resolution figure export (PNG/PDF/SVG)

</td>
</tr>
</table>

<br/>

---

## 📡 &nbsp; SEG-Y Data Handling

<br/>

### Professional Header Management

SeisLab Enhanced provides complete SEG-Y header introspection aligned with industry workflows:

| Header Type | What is Extracted |
|:---|:---|
| **Text Header (EBCDIC)** | Full 3200-byte text header, human-readable display |
| **Binary Header** | All standard binary file header fields |
| **Trace Headers** | Pandas DataFrame for QC, geometry validation, coordinate mapping |
| **Coordinate Scalar** | Proper CDP scalar application per SEG-Y rev1 standard |
| **Geometry Detection** | Automatic inline and crossline range inference |

<br/>

### Standard Byte Location Configuration

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

These follow the SEG-Y revision 1 standard byte assignments and are configurable for non-standard surveys.

<br/>

### Chunked Loading for Large Surveys

For large seismic surveys (100 000+ traces), SeisLab uses a memory-efficient chunked loading strategy:

```python
chunk_size = 5000  # traces per chunk

for start in range(0, total_traces, chunk_size):
    end = min(start + chunk_size, total_traces)
    # process current chunk
    print(f"Loaded {end}/{total_traces} traces...")
```

**Why this matters:**
- Prevents memory overflow on large SEG-Y files
- Provides real-time progress feedback
- Scales to survey-scale 3D datasets

<br/>

### 3D Cube Organization

```python
# Organized 3D array
data_cube.shape = (n_inlines, n_crosslines, n_samples)

# Efficient index mapping
inline_idx    = np.where(inlines    == iline_number)[0]
crossline_idx = np.where(crosslines == xline_number)[0]
```

This structure enables fast extraction of inlines, crosslines, and timeslices without loading the full cube into memory repeatedly.

<br/>

---

## 📊 &nbsp; Visualization

<br/>

### Three Display Modes

**1. Amplitude Display**

The default mode renders seismic data as a 2D image with symmetric color scaling, ideal for regional analysis and attribute QC.

- High-quality matplotlib rendering
- Symmetric clip scaling for seismic data
- Configurable interpolation: `bilinear`, `bicubic`, `gaussian`, `nearest`

**2. Wiggle Display**

Classic trace-by-trace wiggle plot familiar to every geophysicist.

- Configurable trace decimation for display performance
- Automatic per-trace normalization
- Clean baseline rendering

**3. Wiggle + Variable Area (VA)**

The industry-standard display combining wiggle traces with positive amplitude fill — best for horizon interpretation and section reporting.

- Positive lobe fill clearly shows reflection polarity
- Better event continuity visualization
- Standard for publication-quality sections

<br/>

### Available Colormaps

```python
COLORMAPS = {
    'seismic'  : 'RdBu_r',    # Classic seismic diverging   — exploration standard
    'gray'     : 'gray',       # Grayscale                   — impedance / inversion
    'RdBu_r'   : 'RdBu_r',    # Red-Blue reversed           — amplitude analysis
    'RdGy'     : 'RdGy',       # Red-Gray                    — structural interpretation
    'PuOr'     : 'PuOr',       # Purple-Orange               — attribute display
    'viridis'  : 'viridis',    # Perceptually uniform        — accessible / print-safe
    'plasma'   : 'plasma',     # High contrast               — detailed event analysis
    'coolwarm' : 'coolwarm',   # Cool-warm diverging         — AVO / amplitude maps
}
```

<br/>

### Automatic Gain Control (AGC)

```python
def _apply_agc(data):
    """
    Running RMS window AGC.
    Normalizes trace amplitude on a sliding window basis.
    Preserves relative amplitude variations within the window
    while equalizing overall trace energy.
    """
    # Per-trace running RMS normalization
    # Window length configurable
    # Fully vectorized NumPy implementation
```

AGC is essential for visualizing deep reflectors that would otherwise be invisible beneath shallow high-amplitude events.

<br/>

### Professional Plot Styling

```python
# Subtle professional grid
ax.grid(True, alpha=0.25, linestyle='--', linewidth=0.5, color='#888888')

# Clean spine formatting
for spine in ax.spines.values():
    spine.set_edgecolor('#d0d0d0')
    spine.set_linewidth(1.5)

# Aspect ratio options
ax.imshow(data, aspect='auto')    # Maintains data proportions
ax.imshow(data, aspect='equal')   # 1:1 pixel mapping
ax.imshow(data, aspect=2.0)       # Custom vertical exaggeration
```

<br/>

---

## 🧪 &nbsp; Synthetic Data Model

<br/>

For testing and development without real seismic data, SeisLab includes a realistic synthetic seismic generator:

```python
# Multiple geological reflectors
event_times       = [80, 150, 250, 350, 420]      # sample indices
event_amplitudes  = [1.2, 0.8, 1.5, 0.6, 1.0]    # relative amplitudes
event_frequencies = [20,  25,  30,  22,  28]       # dominant frequency (Hz)

# Structural dip — simulates dipping reflectors
dip_x = int(i * 0.3)
dip_y = int(j * 0.2)

# Lateral amplitude variation — simulates DHI / fluid effects
amplitude_var = 0.8 + 0.4 * np.sin(i / 10) * np.cos(j / 8)

# Calibrated Gaussian noise
noise = np.random.normal(0, 0.08, n_samples)
```

**What makes this synthetic data realistic:**
- Multiple independent reflectors at geologically plausible intervals
- Structural dip simulates real subsurface geometry
- Lateral amplitude variation mimics DHI (direct hydrocarbon indicators)
- Frequency-dependent wavelets reflect typical bandwidth variation with depth
- Low-level Gaussian noise matches real field data noise floors

<br/>

**Validation:**

```python
assert data.shape      == (50, 50, 500)
assert np.abs(data).max() < 5.0
assert -1.0 < data.mean() < 1.0

# Frequency content check
from scipy.fft import fft
spectrum      = np.abs(fft(data[25, 25, :]))
dominant_freq = np.argmax(spectrum)
assert 15 < dominant_freq < 35   # Expected bandwidth range
```

<br/>

---

## 🖱️ &nbsp; Interactive Features

<br/>

### Real-Time Cursor Tracking

As the mouse moves over the seismic section, the application tracks position and displays live trace and amplitude information:

```python
def on_mouse_move(event):
    trace, sample = get_mouse_position(event)
    amplitude     = data[trace, sample]
    display_cursor_info(trace, sample, amplitude)
```

This mirrors the interactive behaviour of commercial seismic interpretation platforms.

<br/>

### Point Selection

Clicking on any point in the seismic section emits a signal that can be connected to downstream analysis tools:

```python
def on_canvas_click(event):
    # Emits: point_selected(trace, sample, amplitude)
    # Downstream uses:
    #   — Amplitude extraction at a specific location
    #   — Manual horizon picking
    #   — Quality control flagging
```

<br/>

---

## 💾 &nbsp; Export Capabilities

<br/>

### Trace Header Export

```python
# Export all trace headers to CSV for external QC
loader.export_trace_headers('headers.csv')

# The resulting DataFrame allows:
#   — Geometry validation in Excel or Python
#   — Coordinate mapping and QC
#   — Integration with GIS tools
```

<br/>

### Figure Export

```python
# Export seismic section at publication quality
viewer.export_figure('section.png', dpi=300)

# Supported formats:
#   PNG  — presentations and reports
#   PDF  — vector quality for publications
#   SVG  — scalable for web or further editing
```

<br/>

---

## ⚡ &nbsp; Performance

<br/>

| Technique | Implementation | Benefit |
|:---|:---|:---|
| **Chunked I/O** | 5 000 trace chunks | Constant memory for any survey size |
| **Vectorized AGC** | `data / rms_values[:, np.newaxis]` | Fast NumPy broadcasting, no Python loops |
| **Wiggle Decimation** | `skip = max(1, n_traces // max_wiggles)` | Smooth display regardless of trace count |
| **Vectorized Scaling** | `scaled = data * gain_curve` | Full array operations, no iteration |

<br/>

---

## 💡 &nbsp; Usage Examples

<br/>

**Load a SEG-Y file and inspect all headers**

```python
from seismic.segy_loader import SegyLoader

loader = SegyLoader('seismic_data.sgy')
loader.load_data()

# Text and binary headers
print(loader.get_text_header())
print(loader.binary_header)

# Survey geometry
print(f"Inlines    : {loader.n_inlines}")
print(f"Crosslines : {loader.n_crosslines}")

# Trace headers as DataFrame
df = loader.get_trace_header_dataframe()
print(df.head())
```

<br/>

**Visualize with AGC and export**

```python
from gui.segy_viewer import SeismicViewer

viewer = SeismicViewer()

viewer.agc_checkbox.setChecked(True)       # Enable AGC
viewer.display_section(data)

viewer.mode_combo.setCurrentText('Wiggle + VA')   # Switch display mode
viewer.cmap_combo.setCurrentText('RdBu_r')        # Set colormap

viewer.export_figure('section.png', dpi=300)      # Export
```

<br/>

**Chunked processing and slice extraction**

```python
loader = SegyLoader('large_survey.sgy')
loader.load_data()                          # chunked internally

inline_data = loader.get_inline(100)        # Extract inline 100
xline_data  = loader.get_crossline(200)     # Extract crossline 200
timeslice   = loader.get_timeslice(300)     # Extract time slice at 300 ms
```

<br/>

**Depth conversion integration**

```python
from scipy.interpolate import RegularGridInterpolator

seismic_loader  = SegyLoader('seismic.sgy')
velocity_loader = SegyLoader('velocity.sgy')

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

## 📂 &nbsp; Project Structure

```
SeisLab/
│
├── 📄  main.py                       ← Application entry point
│
├── 📂  gui/
│   ├── main_window.py                ← Primary window and layout
│   ├── seismic_viewer.py             ← Seismic display widget (all 3 modes)
│   └── stats_tab.py                  ← Live statistics and attribute panels
│
├── 📂  seismic/
│   ├── segy_loader.py                ← SEG-Y ingestion, header extraction
│   └── attributes.py                 ← RMS, Instantaneous amplitude/phase/freq
│
├── 📂  core/
│   ├── synthetic.py                  ← Realistic synthetic data generator
│   └── utils.py                      ← Shared utilities
│
├── 📂  assets/
│   └── seislab.png                   ← Application icon
│
└── 📄  README.md
```

<br/>

---

## 🚀 &nbsp; Getting Started

<br/>

**1 — Clone the repository**

```bash
git clone https://github.com/ashraf-iit-ism/seislab.git
cd seislab
```

**2 — Install dependencies**

```bash
pip install numpy pandas matplotlib pyqt5 segyio scipy
```

**3 — Optional: GPU acceleration**

```bash
pip install cupy-cuda12x
```

**4 — Run SeisLab**

```bash
python main.py
```

<br/>

---

## 🗺️ &nbsp; Roadmap

<br/>

```
  ✅  PyQt5 desktop GUI with modular tab layout
  ✅  Seismic attribute computation (RMS, Instantaneous amp/phase/freq)
  ✅  Three visualization modes (Amplitude / Wiggle / Wiggle+VA)
  ✅  AGC and 8 professional colormaps
  ✅  SEG-Y header extraction (EBCDIC, binary, trace headers)
  ✅  Chunked loading for large surveys
  ✅  Synthetic data generator with realistic geology
  ✅  Real-time cursor tracking and point selection
  ✅  Export to PNG / PDF / SVG

  🔧  SEG-Y full data loader (in progress)
  🔧  3D cube inline / crossline / timeslice navigation (in progress)

  🔲  2D seismic section viewer with zoom and pan
  🔲  Seismic attribute map generation
  🔲  Well log integration and overlay
  🔲  Spectral decomposition (FFT / CWT)
  🔲  Time-to-depth conversion module
  🔲  AVO / AVA amplitude analysis
  🔲  xarray integration for labeled dimensions
  🔲  ML-based horizon auto-picking
  🔲  SEG-Y write-back for modified data
  🔲  GPU acceleration via CuPy
```

<br/>

---

## 📊 &nbsp; Feature Comparison

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
| Export Formats | ✅ PNG | ✅ PNG / PDF / SVG |

<br/>

---

## 👤 &nbsp; Author

<br/>

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=rect&color=0:061428,100:0a2244&height=3&width=60%" />

<br/><br/>

### Md Ashraf

**M.Sc (Tech) Applied Geophysics**
*Indian Institute of Technology (ISM) Dhanbad*

<br/>

![Geophysics](https://img.shields.io/badge/Geophysical_Data_Analysis-0a2244?style=flat-square)
![Seismic](https://img.shields.io/badge/Seismic_Interpretation-0a3d62?style=flat-square)
![Python](https://img.shields.io/badge/Python_for_Subsurface_Analytics-0d3060?style=flat-square)
![ML](https://img.shields.io/badge/ML_in_Geoscience-0a2244?style=flat-square)

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-ashraf--iit--ism-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Ashraf-ISM)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit_Site-0a66c2?style=for-the-badge&logo=google-chrome&logoColor=white)](https://ash-geophysics.netlify.app/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077b5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ashraf-iit-ism)

</div>

<br/>

---

## 📄 &nbsp; License

This project is released under the **MIT License** — see [`LICENSE`](./LICENSE) for full terms.

---

## 🙏 &nbsp; Acknowledgements

SeisLab Enhanced is built on top of the excellent work done by the open-source geophysics community. Key references and inspirations:

- **[segyio](https://github.com/equinor/segyio)** — Equinor's industry-grade SEG-Y I/O library
- **[segysak](https://github.com/trhallam/segysak)** — Professional SEG-Y Swiss Army Knife, whose notebook workflows heavily informed this implementation
- The open geoscience community for making exploration workflows accessible to students and researchers worldwide

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d3060,40:0a2244,100:020818&height=120&section=footer" width="100%"/>

<br/>

*Built from scratch · Learning in public · Powered by open geoscience*
<br/>
`IIT (ISM) Dhanbad` &nbsp;·&nbsp; `Applied Geophysics` &nbsp;·&nbsp; `v1.1 Enhanced`

</div>
