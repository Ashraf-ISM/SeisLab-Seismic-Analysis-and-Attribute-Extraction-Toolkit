"""
Attribute Panel
Interface for computing and displaying seismic attributes
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QListWidget,
    QLabel,
    QComboBox,
    QSpinBox,
    QProgressBar,
    QMessageBox,
)
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import matplotlib

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from attributes.seismic_attributes import SeismicAttributes


class AttributeComputeThread(QThread):
    """Thread for computing attributes without blocking UI."""

    finished = pyqtSignal(np.ndarray, str)
    error = pyqtSignal(str)

    def __init__(self, data, attribute_name, window_size=25, sample_rate_ms=2.0, sample_axis=1):
        super().__init__()
        self.data = data
        self.attribute_name = attribute_name
        self.window_size = window_size
        self.sample_rate_ms = sample_rate_ms
        self.sample_axis = sample_axis

    def run(self):
        """Compute attribute in background."""
        try:
            calculator = SeismicAttributes(sample_rate_ms=self.sample_rate_ms)
            window_traces = max(3, min(21, (int(self.window_size) // 4) | 1))
            sigma_samples = max(0.75, float(self.window_size) / 10.0)
            sigma_traces = max(0.75, float(window_traces) / 6.0)

            result = calculator.compute_attribute(
                self.data,
                self.attribute_name,
                sample_axis=self.sample_axis,
                window_samples=int(self.window_size),
                window_traces=window_traces,
                sigma_samples=sigma_samples,
                sigma_traces=sigma_traces,
            )
            self.finished.emit(result, self.attribute_name)
        except Exception as e:
            self.error.emit(str(e))


class AttributePanel(QWidget):
    """Panel for attribute extraction and display."""

    ATTRIBUTE_ITEMS = [
        "RMS Amplitude",
        "Instantaneous Amplitude",
        "Instantaneous Phase",
        "Instantaneous Frequency",
        "Envelope",
        "Sweetness",
        "Dominant Frequency",
        "Coherence",
        "Variance",
        "Dip",
        "Azimuth",
        "Curvature",
    ]

    ATTRIBUTE_ALIASES = {
        "rms": "RMS Amplitude",
        "inst_amp": "Instantaneous Amplitude",
        "inst_phase": "Instantaneous Phase",
        "inst_freq": "Instantaneous Frequency",
        "envelope": "Envelope",
        "sweetness": "Sweetness",
        "dominant_frequency": "Dominant Frequency",
        "coherence": "Coherence",
        "variance": "Variance",
        "dip": "Dip",
        "azimuth": "Azimuth",
        "curvature": "Curvature",
    }

    def __init__(self):
        super().__init__()

        self.current_attribute = None
        self.attribute_results = {}
        self.input_data = None
        self.sample_rate_ms = 2.0
        self.sample_axis = 1  # SeisLab sections are usually [trace, sample].

        self.setup_ui()

    def setup_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)

        # Attribute selection
        attr_group = QGroupBox("Attribute Selection")
        attr_layout = QVBoxLayout()

        self.attr_combo = QComboBox()
        self.attr_combo.addItems(self.ATTRIBUTE_ITEMS)
        attr_layout.addWidget(QLabel("Attribute Type:"))
        attr_layout.addWidget(self.attr_combo)

        self.window_spin = QSpinBox()
        self.window_spin.setMinimum(5)
        self.window_spin.setMaximum(101)
        self.window_spin.setValue(25)
        self.window_spin.setSingleStep(2)
        attr_layout.addWidget(QLabel("Window Size:"))
        attr_layout.addWidget(self.window_spin)
        
        self.btn_compute = QPushButton("Compute Attribute")
        self.btn_compute.clicked.connect(self.compute_selected_attribute)
        attr_layout.addWidget(self.btn_compute)

        attr_group.setLayout(attr_layout)
        left_layout.addWidget(attr_group)

        # Computed attributes list
        list_group = QGroupBox("Computed Attributes")
        list_layout = QVBoxLayout()

        self.attr_list = QListWidget()
        self.attr_list.itemClicked.connect(self.display_selected_attribute)
        list_layout.addWidget(self.attr_list)

        self.btn_export = QPushButton("Export Selected")
        self.btn_export.setEnabled(False)
        list_layout.addWidget(self.btn_export)

        list_group.setLayout(list_layout)
        left_layout.addWidget(list_group)

        left_layout.addStretch()

        # Right side - Display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)

        # Info label
        self.info_label = QLabel("Select an attribute to compute")
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #e8f5e9;
                border: 1px solid #81c784;
                border-radius: 4px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        right_layout.addWidget(self.info_label)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        right_layout.addWidget(self.progress)

        # Matplotlib figure
        self.figure = Figure(figsize=(8, 6), facecolor="white")
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
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.text(
            0.5,
            0.5,
            "Compute an attribute to view results",
            ha="center",
            va="center",
            fontsize=14,
            color="#757575",
            transform=self.ax.transAxes,
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.canvas.draw_idle()

    def set_data(self, data, sample_rate_ms=None, sample_axis=1):
        """Set current seismic section used by attribute computations."""
        self.input_data = data
        self.sample_axis = 1 if sample_axis == 1 else 0
        if sample_rate_ms is not None:
            self.sample_rate_ms = float(sample_rate_ms)

    def _canonical_attribute_name(self, name):
        key = str(name).strip()
        if key in self.ATTRIBUTE_ALIASES:
            return self.ATTRIBUTE_ALIASES[key]
        return key

    def compute_selected_attribute(self):
        """Compute the selected attribute."""
        attribute_name = self.attr_combo.currentText()

        if self.input_data is None:
            QMessageBox.warning(self, "Warning", "No seismic data available.")
            return

        self.compute_attribute(
            attribute_name,
            self.input_data,
            sample_rate_ms=self.sample_rate_ms,
            sample_axis=self.sample_axis,
        )

    def compute_attribute(self, attribute_name, data, sample_rate_ms=None, sample_axis=1):
        """
        Compute seismic attribute.

        Args:
            attribute_name: Attribute display name or alias code.
            data: Input seismic data
        """
        if data is None:
            QMessageBox.warning(self, "Warning", "No seismic data available.")
            return

        self.input_data = data
        self.sample_axis = 1 if sample_axis == 1 else 0
        if sample_rate_ms is not None:
            self.sample_rate_ms = float(sample_rate_ms)

        attribute_name = self._canonical_attribute_name(attribute_name)

        # Show progress
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.btn_compute.setEnabled(False)
        self.info_label.setText(f"Computing {attribute_name}...")

        # Start computation thread
        self.compute_thread = AttributeComputeThread(
            data,
            attribute_name,
            window_size=self.window_spin.value(),
            sample_rate_ms=self.sample_rate_ms,
            sample_axis=self.sample_axis,
        )
        self.compute_thread.finished.connect(self.on_compute_finished)
        self.compute_thread.error.connect(self.on_compute_error)
        self.compute_thread.start()

    def on_compute_finished(self, result, attribute_name):
        """Handle completed attribute computation."""
        self.progress.setVisible(False)
        self.btn_compute.setEnabled(True)

        # Store result
        self.attribute_results[attribute_name] = result

        # Update list
        existing = [self.attr_list.item(i).text() for i in range(self.attr_list.count())]
        if attribute_name not in existing:
            self.attr_list.addItem(attribute_name)

        # Display result
        self.display_attribute(result, attribute_name)
        self.info_label.setText(f"Computed {attribute_name} successfully")
        self.btn_export.setEnabled(True)

    def on_compute_error(self, error_msg):
        """Handle computation error."""
        self.progress.setVisible(False)
        self.btn_compute.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Computation failed:\n{error_msg}")
        self.info_label.setText("Computation failed")

    def display_selected_attribute(self, item):
        """Display selected attribute from list."""
        attribute_name = item.text()
        if attribute_name in self.attribute_results:
            result = self.attribute_results[attribute_name]
            self.display_attribute(result, attribute_name)

    def display_attribute(self, data, attribute_name):
        """
        Display attribute result.

        Args:
            data: Attribute data array
            attribute_name: Attribute display name
        """
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.current_attribute = data

        data = np.asarray(data)
        p01 = float(np.nanpercentile(data, 1))
        p99 = float(np.nanpercentile(data, 99))
        if not np.isfinite(p01) or not np.isfinite(p99):
            p01, p99 = 0.0, 1.0

        # Choose appropriate colormap
        if attribute_name == "Instantaneous Phase":
            cmap = "hsv"
            vmin, vmax = -np.pi, np.pi
        elif attribute_name == "Azimuth":
            cmap = "twilight"
            vmin, vmax = 0.0, 360.0
        elif attribute_name == "Coherence":
            cmap = "viridis"
            vmin, vmax = 0.0, 1.0
        elif attribute_name in {"Dip", "Curvature"}:
            clip = max(abs(p01), abs(p99), 1e-9)
            cmap = "seismic"
            vmin, vmax = -clip, clip
        elif attribute_name in {"Instantaneous Frequency", "Dominant Frequency", "Sweetness", "Variance"}:
            cmap = "magma"
            vmin, vmax = max(0.0, p01), p99
        else:
            cmap = "inferno"
            vmin, vmax = p01, p99

        # Plot
        im = self.ax.imshow(
            data.T,
            aspect="auto",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            interpolation="nearest",
            origin="upper",
        )

        # Colorbar
        cbar = self.figure.colorbar(im, ax=self.ax, pad=0.02)
        cbar.set_label(attribute_name, fontsize=10, weight="bold")

        # Labels
        self.ax.set_xlabel("Trace Number", fontsize=11, weight="bold")
        self.ax.set_ylabel("Time (samples)", fontsize=11, weight="bold")
        self.ax.set_title(f"{attribute_name} Attribute", fontsize=13, weight="bold", pad=15)

        # Grid and styling
        self.ax.grid(True, alpha=0.25, linestyle="--", linewidth=0.5)
        self.ax.tick_params(labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#e0e0e0")
            spine.set_linewidth(1.5)

        self.figure.tight_layout()
        self.canvas.draw_idle()
