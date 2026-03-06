"""
Processing Panel
Interface for applying signal processing filters
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QDoubleSpinBox,
                             QCheckBox, QSlider, QMessageBox)
from PyQt5.QtCore import Qt
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from processing.filters import BandpassFilter, GainControl, TraceNormalization


class ProcessingPanel(QWidget):
    """Panel for signal processing operations."""
    
    def __init__(self):
        super().__init__()
        
        self.original_data = None
        self.processed_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        # Filter selection
        filter_group = QGroupBox("Filter Selection")
        filter_layout = QVBoxLayout()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Bandpass Filter",
            "Gain Control",
            "Trace Normalization",
            "Median Filter",
            "Gaussian Smoothing"
        ])
        self.filter_combo.currentTextChanged.connect(self.update_filter_params)
        filter_layout.addWidget(QLabel("Filter Type:"))
        filter_layout.addWidget(self.filter_combo)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        
        # Filter parameters (dynamic)
        self.params_group = QGroupBox("Parameters")
        self.params_layout = QVBoxLayout()
        self.params_group.setLayout(self.params_layout)
        left_layout.addWidget(self.params_group)
        
        # Update parameter widgets
        self.update_filter_params()
        
        # Apply button
        self.btn_apply = QPushButton("Apply Filter")
        self.btn_apply.clicked.connect(self.apply_filter)
        left_layout.addWidget(self.btn_apply)
        
        # Reset button
        self.btn_reset = QPushButton("Reset to Original")
        self.btn_reset.clicked.connect(self.reset_to_original)
        self.btn_reset.setEnabled(False)
        left_layout.addWidget(self.btn_reset)
        
        left_layout.addStretch()
        
        # Right side - Display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        
        # Info label
        self.info_label = QLabel("Load seismic data to apply processing")
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #fff3e0;
                border: 1px solid #ffb74d;
                border-radius: 4px;
                font-weight: bold;
                color: #e65100;
            }
        """)
        right_layout.addWidget(self.info_label)
        
        # Matplotlib figure
        self.figure = Figure(figsize=(8, 6), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        right_layout.addWidget(self.canvas)
        
        # Add to main layout
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 3)
        
        # Show empty plot
        self.show_empty_plot()
        
    def show_empty_plot(self):
        """Display empty plot with instructions."""
        self.ax.clear()
        self.ax.text(0.5, 0.5, 'Apply processing filters to seismic data',
                    ha='center', va='center', fontsize=14, color='#757575',
                    transform=self.ax.transAxes)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.canvas.draw()
        
    def update_filter_params(self):
        """Update parameter widgets based on selected filter."""
        # Clear existing widgets
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        filter_type = self.filter_combo.currentText()
        
        if filter_type == "Bandpass Filter":
            self.params_layout.addWidget(QLabel("Low Cut Frequency (Hz):"))
            self.lowcut_spin = QDoubleSpinBox()
            self.lowcut_spin.setMinimum(1.0)
            self.lowcut_spin.setMaximum(250.0)
            self.lowcut_spin.setValue(10.0)
            self.params_layout.addWidget(self.lowcut_spin)
            
            self.params_layout.addWidget(QLabel("High Cut Frequency (Hz):"))
            self.highcut_spin = QDoubleSpinBox()
            self.highcut_spin.setMinimum(1.0)
            self.highcut_spin.setMaximum(250.0)
            self.highcut_spin.setValue(60.0)
            self.params_layout.addWidget(self.highcut_spin)
            
        elif filter_type == "Gain Control":
            self.params_layout.addWidget(QLabel("Gain Type:"))
            self.gain_type_combo = QComboBox()
            self.gain_type_combo.addItems(["AGC", "Linear", "Exponential"])
            self.params_layout.addWidget(self.gain_type_combo)
            
            self.params_layout.addWidget(QLabel("Window Size:"))
            self.gain_window = QDoubleSpinBox()
            self.gain_window.setMinimum(10)
            self.gain_window.setMaximum(200)
            self.gain_window.setValue(50)
            self.params_layout.addWidget(self.gain_window)
            
        elif filter_type == "Trace Normalization":
            self.params_layout.addWidget(QLabel("Normalization Method:"))
            self.norm_method = QComboBox()
            self.norm_method.addItems(["Max Absolute", "RMS", "Mean"])
            self.params_layout.addWidget(self.norm_method)
            
        elif filter_type == "Median Filter":
            self.params_layout.addWidget(QLabel("Kernel Size:"))
            self.kernel_spin = QDoubleSpinBox()
            self.kernel_spin.setMinimum(3)
            self.kernel_spin.setMaximum(21)
            self.kernel_spin.setValue(5)
            self.kernel_spin.setSingleStep(2)
            self.params_layout.addWidget(self.kernel_spin)
            
        elif filter_type == "Gaussian Smoothing":
            self.params_layout.addWidget(QLabel("Sigma:"))
            self.sigma_spin = QDoubleSpinBox()
            self.sigma_spin.setMinimum(0.1)
            self.sigma_spin.setMaximum(10.0)
            self.sigma_spin.setValue(1.0)
            self.sigma_spin.setSingleStep(0.1)
            self.params_layout.addWidget(self.sigma_spin)
            
    def set_data(self, data):
        """
        Set input data for processing.
        
        Args:
            data: 2D numpy array
        """
        self.original_data = data.copy()
        self.processed_data = None
        self.display_data(data, "Original Data")
        self.info_label.setText("Data loaded - apply filters")
        
    def apply_filter(self):
        """Apply selected filter to data."""
        if self.original_data is None:
            QMessageBox.warning(self, "Warning", "No data loaded.")
            return
            
        filter_type = self.filter_combo.currentText()
        
        try:
            if filter_type == "Bandpass Filter":
                lowcut = self.lowcut_spin.value()
                highcut = self.highcut_spin.value()
                sample_rate = 500.0  # Hz (2ms sample rate)
                
                filter_obj = BandpassFilter(lowcut, highcut, sample_rate)
                self.processed_data = filter_obj.apply(self.original_data)
                
            elif filter_type == "Gain Control":
                gain_type = self.gain_type_combo.currentText()
                window = int(self.gain_window.value())
                
                gain_obj = GainControl(gain_type.lower(), window)
                self.processed_data = gain_obj.apply(self.original_data)
                
            elif filter_type == "Trace Normalization":
                method = self.norm_method.currentText().lower().replace(' ', '_')
                
                norm_obj = TraceNormalization(method)
                self.processed_data = norm_obj.apply(self.original_data)
                
            else:
                QMessageBox.information(self, "Info", 
                                       f"{filter_type} not yet implemented.")
                return
                
            self.display_data(self.processed_data, f"Processed: {filter_type}")
            self.btn_reset.setEnabled(True)
            self.info_label.setText(f"Applied {filter_type}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed:\n{str(e)}")
            
    def reset_to_original(self):
        """Reset to original data."""
        if self.original_data is not None:
            self.processed_data = None
            self.display_data(self.original_data, "Original Data")
            self.btn_reset.setEnabled(False)
            self.info_label.setText("Reset to original data")
            
    def display_data(self, data, title):
        """
        Display data.
        
        Args:
            data: 2D numpy array
            title: Plot title
        """
        self.ax.clear()
        
        # Calculate clip values
        vmin = np.percentile(data, 1)
        vmax = np.percentile(data, 99)
        vmax = max(abs(vmin), abs(vmax))
        vmin = -vmax
        
        # Plot
        im = self.ax.imshow(data.T, aspect='auto', cmap='seismic',
                           vmin=vmin, vmax=vmax, interpolation='bilinear')
        
        # Colorbar
        cbar = self.figure.colorbar(im, ax=self.ax, pad=0.02)
        cbar.set_label('Amplitude', fontsize=10, weight='bold')
        
        # Labels
        self.ax.set_xlabel('Trace Number', fontsize=11, weight='bold')
        self.ax.set_ylabel('Time (samples)', fontsize=11, weight='bold')
        self.ax.set_title(title, fontsize=13, weight='bold', pad=15)
        
        # Grid and styling
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        self.ax.tick_params(labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#e0e0e0')
            spine.set_linewidth(1.5)
            
        self.figure.tight_layout()
        self.canvas.draw()
