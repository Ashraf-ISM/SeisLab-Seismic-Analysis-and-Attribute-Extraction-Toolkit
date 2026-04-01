# SeisLab Quick Start Guide

## Installation (2 minutes)

### Step 1: Install Python Dependencies

```bash
cd seislab
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
python main.py
```

That's it! The application will launch with a professional light theme interface.

## First Steps (5 minutes)

### 1. Understanding the Interface

The SeisLab window consists of:

- **Left Panel**: Controls and file information
- **Center Area**: Tabbed workspace with 4 main views
  - Seismic Viewer
  - Attributes
  - Processing
  - Interpretation
- **Menu Bar**: File, View, Attributes, Processing, ML, Help
- **Status Bar**: Progress and information

### 2. Demo Mode (No SEG-Y File Required)

If you don't have a SEG-Y file, SeisLab runs with synthetic data automatically:

1. Launch the application
2. Go to **File → Open SEG-Y**
3. The synthetic data loader will activate
4. Explore all features with demo data

### 3. Loading Your Data

If you have SEG-Y files:

```
File → Open SEG-Y → Select your .sgy or .segy file
```

The application will:
- Parse the SEG-Y headers
- Extract trace data
- Display the first inline
- Populate navigation controls

### 4. Basic Workflow

#### A. View Seismic Data

1. **Navigation**:
   - Adjust "Inline" spinner to change inline number
   - Adjust "Crossline" for crossline view
   - Select view mode from dropdown

2. **Display Settings**:
   - Choose colormap (seismic, gray, viridis, etc.)
   - Adjust gain (0.1 to 10.0)
   - Set clip percentage (1 to 100%)

#### B. Compute Attributes

1. Click **Attributes** tab
2. Select attribute type (e.g., "RMS Amplitude")
3. Set window size (default: 25 samples)
4. Click **Compute Attribute**
5. View results in the display

**Try these attributes:**
- RMS Amplitude - highlights amplitude variations
- Instantaneous Amplitude - shows envelope
- Instantaneous Phase - reveals discontinuities
- Instantaneous Frequency - detects frequency changes

#### C. Apply Processing

1. Click **Processing** tab
2. Select filter type
3. Configure parameters:
   - **Bandpass**: Set low (10 Hz) and high (60 Hz) frequencies
   - **AGC**: Set window size (50 samples)
   - **Normalization**: Choose method
4. Click **Apply Filter**
5. Compare with original using **Reset to Original**

#### D. Interpret Horizons

1. Click **Interpretation** tab
2. Click **Start Picking**
3. Click on the seismic section to pick points
4. Click **Stop Picking** when done
5. Click **Save Horizon**
6. Repeat for multiple horizons

### 5. Export Results

```
File → Export Data → Choose format (NumPy or CSV)
```

## Tips & Tricks

### Visualization
- **Zoom**: Use matplotlib toolbar zoom tool
- **Pan**: Use pan tool in toolbar
- **Reset**: View → Reset View
- **Fullscreen**: Press F11

### Performance
- Start with smaller inline/crossline ranges
- Reduce window sizes for faster attribute computation
- Use clip percentage to enhance features

### Workflows

**Structure Mapping:**
1. Load data
2. Compute Instantaneous Phase
3. Use Interpretation to pick horizons
4. Export picks

**Facies Analysis:**
1. Compute multiple attributes (RMS, Inst Amp, Inst Phase)
2. Machine Learning → K-Means
3. Analyze clustered facies

**Frequency Analysis:**
1. Compute Instantaneous Frequency
2. Apply Bandpass Filter
3. Compare frequency content

## Common Operations

### Change Colormap
```
Display Settings → Colormap → Select from dropdown
```

### Enhance Weak Signals
```
Display Settings → Gain → Increase value (e.g., 2.0-3.0)
```

### Remove Noise
```
Processing Tab → Bandpass Filter → Set frequencies → Apply
```

### Find Horizons
```
Interpretation Tab → Start Picking → Click points → Save
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open file |
| Ctrl+E | Export data |
| Ctrl+Q | Quit |
| F11 | Fullscreen |

## Next Steps

After mastering the basics:

1. **Experiment with parameters**: Try different window sizes and filter settings
2. **Combine attributes**: Compute multiple attributes for comparison
3. **Machine learning**: Use ML for automated facies classification
4. **Custom development**: Add your own attributes and filters

## Getting Help

- Check **README.md** for detailed documentation
- Use **Help → Documentation** in the menu
- Review the code examples in each module

---

**You're ready to start analyzing seismic data!** 🎉

Have questions? Check the troubleshooting section in README.md
