# SeisLab - Professional Seismic Analysis & Attribute Extraction

![SeisLab](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

A professional desktop GUI application for seismic data analysis, visualization, and interpretation. Built with modern software engineering practices and clean object-oriented architecture.

## Features

### 🎯 Core Functionality

- **SEG-Y Data Loading**: Import and parse industry-standard SEG-Y seismic data
- **Interactive Visualization**: High-quality seismic section displays with customizable colormaps
- **Attribute Extraction**: Compute advanced seismic attributes
- **Signal Processing**: Apply professional-grade filters and gain controls
- **Machine Learning**: Unsupervised facies classification
- **Interpretation Tools**: Interactive horizon picking and analysis

### 📊 Supported Attributes

#### Basic Attributes
- RMS Amplitude
- Reflection Strength
- Energy

#### Instantaneous Attributes (Hilbert Transform)
- Instantaneous Amplitude (Envelope)
- Instantaneous Phase
- Instantaneous Frequency
- Coherence

### 🔧 Processing Capabilities

- Bandpass Filtering
- Automatic Gain Control (AGC)
- Linear & Exponential Gain
- Trace Normalization (Multiple methods)
- Smoothing Filters

### 🤖 Machine Learning

- K-Means Clustering
- DBSCAN
- Gaussian Mixture Models (GMM)
- Multi-attribute classification

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download the repository**

```bash
cd seislab
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the application**

```bash
python main.py
```

## Project Structure

```
seislab/
│
├── main.py                          # Application entry point
│
├── gui/                             # GUI components
│   ├── __init__.py
│   ├── main_window.py              # Main application window
│   ├── segy_viewer.py              # Seismic visualization widget
│   ├── attribute_panel.py          # Attribute computation panel
│   ├── processing_panel.py         # Signal processing panel
│   ├── interpretation_panel.py     # Interpretation tools
│   └── info_panel.py               # Information display
│
├── seismic/                         # Seismic data handling
│   ├── __init__.py
│   └── segy_loader.py              # SEG-Y file loader
│
├── attributes/                      # Attribute algorithms
│   ├── __init__.py
│   ├── rms.py                      # RMS and energy attributes
│   └── instantaneous.py            # Instantaneous attributes
│
├── processing/                      # Signal processing
│   ├── __init__.py
│   └── filters.py                  # Filters and gain control
│
├── ml/                             # Machine learning
│   ├── __init__.py
│   └── facies_classifier.py        # Unsupervised classification
│
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Usage Guide

### 1. Loading Data

- **File → Open SEG-Y** or press `Ctrl+O`
- Select your SEG-Y file
- Data will be automatically parsed and displayed

### 2. Navigation

- **Inline View**: Navigate through inline sections
- **Crossline View**: Navigate through crossline sections
- **Time Slice**: View horizontal time slices

### 3. Display Settings

- **Colormap**: Choose from multiple colormaps (seismic, gray, viridis, etc.)
- **Gain**: Adjust amplitude gain (0.1 - 10.0)
- **Clip**: Set amplitude clipping percentage

### 4. Computing Attributes

**Method 1: Quick Actions**
- Click "Compute Attributes" button
- Select attribute type
- Set parameters
- Click "Compute"

**Method 2: Menu**
- **Attributes** menu → Select attribute
- Results displayed in Attributes tab

**Available Attributes:**
- RMS Amplitude
- Instantaneous Amplitude
- Instantaneous Phase
- Instantaneous Frequency

### 5. Applying Filters

1. Go to **Processing** tab
2. Select filter type
3. Adjust parameters
4. Click "Apply Filter"
5. Use "Reset to Original" to revert

**Filter Types:**
- Bandpass Filter (specify low/high cut frequencies)
- AGC (Automatic Gain Control)
- Trace Normalization
- Median Filter
- Gaussian Smoothing

### 6. Machine Learning Classification

1. Compute multiple attributes
2. **Machine Learning** menu → Select algorithm
3. Configure number of clusters
4. View classified facies

### 7. Interpretation

1. Go to **Interpretation** tab
2. Click "Start Picking"
3. Click on seismic section to pick horizons
4. Click "Save Horizon" to store picks
5. Export horizons for further analysis

### 8. Exporting Results

- **File → Export Data** or press `Ctrl+E`
- Choose format (NumPy .npy or CSV)
- Save processed data or attributes

## Keyboard Shortcuts

- `Ctrl+O` - Open SEG-Y file
- `Ctrl+E` - Export data
- `Ctrl+Q` - Quit application
- `F11` - Toggle fullscreen

## Design Features

### Professional Light Theme
- Clean, modern interface
- High contrast for readability
- Professional color scheme
- Responsive layout

### Architecture Highlights
- **Object-Oriented Design**: Clean class-based structure
- **Modular Components**: Separated concerns and reusable code
- **Thread Safety**: Background computation without UI blocking
- **Scalable**: Easy to extend with new algorithms

## Advanced Features

### Custom Attribute Development

Add new attributes by creating a class in the `attributes/` directory:

```python
class MyAttribute:
    def compute(self, data):
        # Your algorithm here
        return processed_data
```

### Custom Filters

Extend processing capabilities in `processing/filters.py`:

```python
class MyFilter:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
        
    def apply(self, data):
        # Your filter logic
        return filtered_data
```

## Technical Specifications

- **Language**: Python 3.8+
- **GUI Framework**: PyQt5
- **Numerical Computing**: NumPy, SciPy
- **Visualization**: Matplotlib
- **Machine Learning**: scikit-learn
- **Data Format**: SEG-Y (via segyio)

## Performance Notes

- Efficient NumPy array operations
- Background threading for heavy computations
- Optimized visualization rendering
- Memory-efficient data handling

## Demo Mode

If `segyio` is not installed, the application runs with **synthetic data** for demonstration purposes, showcasing all features without requiring actual SEG-Y files.

## Troubleshooting

### Installation Issues

**Problem**: `segyio` installation fails

**Solution**: The application works without it using synthetic data

**Problem**: GUI doesn't appear

**Solution**: Ensure PyQt5 is properly installed:
```bash
pip install --upgrade PyQt5
```

### Runtime Issues

**Problem**: Slow attribute computation

**Solution**: Reduce window size or process smaller data sections

**Problem**: Memory errors

**Solution**: Load smaller SEG-Y files or process data in chunks

## Contributing

This project follows clean code principles:

1. Use descriptive variable names
2. Add docstrings to all classes and methods
3. Separate GUI logic from algorithms
4. Write modular, reusable code
5. Follow PEP 8 style guidelines

## Future Enhancements

- [ ] 3D visualization
- [ ] Well log integration
- [ ] Advanced ML models (neural networks)
- [ ] Batch processing
- [ ] Plugin architecture
- [ ] Project management system
- [ ] Cloud data integration

## License

MIT License - Free for educational and commercial use

## Citation

If you use SeisLab in your research, please cite:

```
SeisLab - Professional Seismic Analysis & Attribute Extraction
Version 1.0 (2024)
```

## Contact & Support

For questions, suggestions, or contributions:
- Open an issue on the repository
- Submit pull requests for improvements

---

**Built with ❤️ for the geophysics community**
