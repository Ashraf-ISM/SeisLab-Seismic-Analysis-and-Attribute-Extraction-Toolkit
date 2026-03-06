# SeisLab Developer Guide

## Architecture Overview

SeisLab follows a professional, modular architecture designed for maintainability, scalability, and ease of extension.

### Design Principles

1. **Separation of Concerns**: GUI logic is separated from business logic
2. **Object-Oriented Design**: Each module is implemented as classes
3. **Modularity**: Components can be used independently
4. **Reusability**: Algorithms can be imported and used in other projects
5. **Extensibility**: Easy to add new features

### Directory Structure

```
seislab/
├── main.py                    # Entry point
├── gui/                       # User interface components
│   ├── main_window.py        # Main application controller
│   ├── segy_viewer.py        # Visualization widget
│   ├── attribute_panel.py    # Attribute computation UI
│   ├── processing_panel.py   # Processing controls
│   ├── interpretation_panel.py  # Interpretation tools
│   └── info_panel.py         # Information display
├── seismic/                   # Data handling
│   └── segy_loader.py        # SEG-Y I/O
├── attributes/                # Attribute algorithms
│   ├── rms.py                # Basic attributes
│   └── instantaneous.py      # Complex attributes
├── processing/                # Signal processing
│   └── filters.py            # Filters and gain
├── ml/                        # Machine learning
│   └── facies_classifier.py  # Classification
└── resources/                 # Assets (icons, etc.)
```

## Adding New Features

### 1. Adding a New Attribute

Create a new attribute class in `attributes/`:

```python
# attributes/my_attribute.py

import numpy as np

class MyAttribute:
    """
    Description of your attribute.
    """
    
    def __init__(self, parameter1=10):
        """
        Initialize with parameters.
        
        Args:
            parameter1: Description
        """
        self.parameter1 = parameter1
        
    def compute(self, data):
        """
        Compute the attribute.
        
        Args:
            data: 2D numpy array (traces x samples)
            
        Returns:
            2D numpy array of attribute values
        """
        # Your algorithm here
        result = np.zeros_like(data)
        
        # Process each trace
        for i in range(data.shape[0]):
            result[i, :] = self._compute_trace(data[i, :])
            
        return result
        
    def _compute_trace(self, trace):
        """Process single trace."""
        # Your trace processing logic
        return processed_trace
```

Register in `gui/attribute_panel.py`:

```python
# In AttributePanel.setup_ui()
self.attr_combo.addItems([
    # ... existing items ...
    "My New Attribute"
])

# In compute_attribute()
attr_map = {
    # ... existing mappings ...
    "My New Attribute": "my_attr"
}

# In AttributeComputeThread.run()
elif self.attr_type == 'my_attr':
    from attributes.my_attribute import MyAttribute
    calculator = MyAttribute(parameter=value)
```

### 2. Adding a New Filter

Create filter class in `processing/filters.py`:

```python
class MyFilter:
    """Description of filter."""
    
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
        
    def apply(self, data):
        """
        Apply filter to data.
        
        Args:
            data: 2D numpy array
            
        Returns:
            Filtered 2D numpy array
        """
        # Your filter implementation
        return filtered_data
```

Add to `gui/processing_panel.py`:

```python
# In setup_ui()
self.filter_combo.addItems([
    # ... existing items ...
    "My New Filter"
])

# In update_filter_params()
elif filter_type == "My New Filter":
    # Add parameter widgets
    pass

# In apply_filter()
elif filter_type == "My New Filter":
    param1 = self.param1_spin.value()
    filter_obj = MyFilter(param1)
    self.processed_data = filter_obj.apply(self.original_data)
```

### 3. Adding ML Algorithms

Extend `ml/facies_classifier.py`:

```python
class MyClassifier:
    """Custom ML classifier."""
    
    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters
        self.model = None
        
    def fit(self, X):
        """Train the model."""
        # Your ML algorithm
        pass
        
    def predict(self, X):
        """Make predictions."""
        # Prediction logic
        pass
```

### 4. Custom Visualization

Add to `gui/segy_viewer.py`:

```python
def my_custom_plot(self, data):
    """
    Custom visualization method.
    
    Args:
        data: Input data
    """
    self.ax.clear()
    
    # Your plotting logic
    # Use matplotlib commands
    
    self.canvas.draw()
```

## Code Style Guidelines

### 1. Naming Conventions

```python
# Classes: PascalCase
class SeismicAttribute:
    pass

# Functions/Methods: snake_case
def compute_attribute():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_TRACES = 1000

# Private methods: _leading_underscore
def _internal_method():
    pass
```

### 2. Documentation

Always include docstrings:

```python
def function_name(param1, param2):
    """
    Brief description.
    
    Longer description if needed. Explain the purpose,
    algorithm, or important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When validation fails
    """
    pass
```

### 3. Type Hints (Optional but Recommended)

```python
from typing import Optional, List
import numpy as np

def compute_rms(data: np.ndarray, 
                window: int = 25) -> np.ndarray:
    """Compute RMS with type hints."""
    pass
```

### 4. Error Handling

```python
def load_data(filepath: str):
    """Load with proper error handling."""
    try:
        # Main logic
        data = load_file(filepath)
        return data
        
    except FileNotFoundError:
        raise ValueError(f"File not found: {filepath}")
        
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {str(e)}")
```

## Testing

### Unit Tests Structure

```python
# tests/test_attributes.py

import unittest
import numpy as np
from attributes.rms import RMSAmplitude

class TestRMSAmplitude(unittest.TestCase):
    
    def setUp(self):
        """Set up test data."""
        self.data = np.random.randn(10, 100)
        self.calculator = RMSAmplitude(window_size=25)
        
    def test_compute_shape(self):
        """Test output shape matches input."""
        result = self.calculator.compute(self.data)
        self.assertEqual(result.shape, self.data.shape)
        
    def test_compute_positive(self):
        """Test RMS values are positive."""
        result = self.calculator.compute(self.data)
        self.assertTrue(np.all(result >= 0))
        
if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python -m unittest discover tests/
```

## Performance Optimization

### 1. NumPy Vectorization

❌ **Slow (loops):**
```python
result = np.zeros_like(data)
for i in range(len(data)):
    for j in range(len(data[0])):
        result[i, j] = data[i, j] * 2
```

✅ **Fast (vectorized):**
```python
result = data * 2
```

### 2. Threading for Heavy Computation

```python
from PyQt5.QtCore import QThread, pyqtSignal

class ComputeThread(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, data):
        super().__init__()
        self.data = data
        
    def run(self):
        # Heavy computation here
        result = heavy_computation(self.data)
        self.finished.emit(result)

# Usage in GUI
thread = ComputeThread(data)
thread.finished.connect(self.on_finished)
thread.start()
```

### 3. Memory Management

```python
# Use views instead of copies when possible
view = data[10:20, :]  # View (fast)
copy = data[10:20, :].copy()  # Copy (slower)

# Delete large arrays when done
del large_array
import gc
gc.collect()
```

## GUI Best Practices

### 1. Signal-Slot Connections

```python
# Connect signals in __init__ or setup method
self.button.clicked.connect(self.on_button_clicked)
self.slider.valueChanged.connect(self.on_value_changed)

# Use lambda for parameters
self.button.clicked.connect(
    lambda: self.process_data(parameter=value)
)
```

### 2. Thread Safety

```python
# Always update GUI from main thread
def on_computation_finished(self, result):
    """Callback runs in main thread."""
    self.display_result(result)
    self.progress_bar.setVisible(False)
```

### 3. Responsive UI

```python
# Process events during long operations
from PyQt5.QtWidgets import QApplication

for i in range(large_number):
    # Do work
    if i % 100 == 0:
        QApplication.processEvents()
```

## Debugging Tips

### 1. Enable Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### 2. Qt Debug Mode

```python
# In main.py
import sys
from PyQt5.QtCore import qDebug

# Enable debug output
qDebug("Debug message")
```

### 3. Print Array Info

```python
def debug_array(arr, name="array"):
    """Print debugging info for numpy array."""
    print(f"{name}:")
    print(f"  Shape: {arr.shape}")
    print(f"  Dtype: {arr.dtype}")
    print(f"  Min: {arr.min():.3f}")
    print(f"  Max: {arr.max():.3f}")
    print(f"  Mean: {arr.mean():.3f}")
```

## Building and Distribution

### Create Standalone Executable

Using PyInstaller:

```bash
pip install pyinstaller

pyinstaller --onefile --windowed \
    --name SeisLab \
    --icon=resources/icon.ico \
    main.py
```

### Create Installer

Using Inno Setup (Windows):

```ini
[Setup]
AppName=SeisLab
AppVersion=1.0
DefaultDirName={pf}\SeisLab
DefaultGroupName=SeisLab
OutputDir=dist
OutputBaseFilename=SeisLab_Setup

[Files]
Source: "dist\SeisLab.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\SeisLab"; Filename: "{app}\SeisLab.exe"
```

## Contributing Guidelines

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Follow code style**: Use provided guidelines
4. **Add tests**: Cover new functionality
5. **Document changes**: Update README and docstrings
6. **Submit pull request**: With clear description

## Resources

- PyQt5 Documentation: https://doc.qt.io/qtforpython/
- NumPy Guide: https://numpy.org/doc/
- SciPy Signal Processing: https://docs.scipy.org/doc/scipy/reference/signal.html
- Scikit-learn: https://scikit-learn.org/

---

**Happy coding! Build amazing seismic analysis tools!** 🚀
