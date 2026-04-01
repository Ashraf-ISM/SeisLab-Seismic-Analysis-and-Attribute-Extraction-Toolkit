"""
Interpretation Panel
Interactive horizon picking and interpretation tools
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class InterpretationPanel(QWidget):
    """Panel for seismic interpretation and horizon picking."""
    
    def __init__(self):
        super().__init__()
        
        self.data = None
        self.horizons = {}
        self.current_horizon = []
        self.picking_mode = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        # Picking controls
        pick_group = QGroupBox("Horizon Picking")
        pick_layout = QVBoxLayout()
        
        self.btn_start_pick = QPushButton("Start Picking")
        self.btn_start_pick.clicked.connect(self.start_picking)
        pick_layout.addWidget(self.btn_start_pick)
        
        self.btn_stop_pick = QPushButton("Stop Picking")
        self.btn_stop_pick.clicked.connect(self.stop_picking)
        self.btn_stop_pick.setEnabled(False)
        pick_layout.addWidget(self.btn_stop_pick)
        
        self.btn_save_horizon = QPushButton("Save Horizon")
        self.btn_save_horizon.clicked.connect(self.save_horizon)
        self.btn_save_horizon.setEnabled(False)
        pick_layout.addWidget(self.btn_save_horizon)
        
        self.btn_clear = QPushButton("Clear Current")
        self.btn_clear.clicked.connect(self.clear_current_horizon)
        pick_layout.addWidget(self.btn_clear)
        
        pick_group.setLayout(pick_layout)
        left_layout.addWidget(pick_group)
        
        # Horizons list
        horizon_group = QGroupBox("Saved Horizons")
        horizon_layout = QVBoxLayout()
        
        self.horizon_list = QListWidget()
        self.horizon_list.itemClicked.connect(self.display_selected_horizon)
        horizon_layout.addWidget(self.horizon_list)
        
        self.btn_export = QPushButton("Export Horizon")
        self.btn_export.clicked.connect(self.export_horizon)
        self.btn_export.setEnabled(False)
        horizon_layout.addWidget(self.btn_export)
        
        self.btn_delete = QPushButton("Delete Horizon")
        self.btn_delete.clicked.connect(self.delete_horizon)
        self.btn_delete.setEnabled(False)
        horizon_layout.addWidget(self.btn_delete)
        
        horizon_group.setLayout(horizon_layout)
        left_layout.addWidget(horizon_group)
        
        left_layout.addStretch()
        
        # Right side - Display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        
        # Info label
        self.info_label = QLabel("Click 'Start Picking' to begin interpretation")
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #f3e5f5;
                border: 1px solid #ba68c8;
                border-radius: 4px;
                font-weight: bold;
                color: #6a1b9a;
            }
        """)
        right_layout.addWidget(self.info_label)
        
        # Matplotlib figure
        self.figure = Figure(figsize=(8, 6), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        right_layout.addWidget(self.canvas)
        
        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Add to main layout
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 3)
        
        # Show empty plot
        self.show_empty_plot()
        
    def show_empty_plot(self):
        """Display empty plot with instructions."""
        self.ax.clear()
        self.ax.text(0.5, 0.5, 'Load data and start picking horizons',
                    ha='center', va='center', fontsize=14, color='#757575',
                    transform=self.ax.transAxes)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.canvas.draw()
        
    def set_data(self, data):
        """
        Set seismic data for interpretation.
        
        Args:
            data: 2D numpy array
        """
        self.data = data
        self.display_data()
        
    def display_data(self):
        """Display seismic data with horizons."""
        if self.data is None:
            self.show_empty_plot()
            return
            
        self.ax.clear()
        
        # Plot seismic data
        vmin = np.percentile(self.data, 1)
        vmax = np.percentile(self.data, 99)
        vmax = max(abs(vmin), abs(vmax))
        vmin = -vmax
        
        self.ax.imshow(self.data.T, aspect='auto', cmap='seismic',
                      vmin=vmin, vmax=vmax, interpolation='bilinear')
        
        # Plot saved horizons
        for name, points in self.horizons.items():
            if len(points) > 0:
                points = np.array(points)
                self.ax.plot(points[:, 0], points[:, 1], 'o-', 
                           linewidth=2, markersize=4, label=name)
        
        # Plot current horizon
        if len(self.current_horizon) > 0:
            points = np.array(self.current_horizon)
            self.ax.plot(points[:, 0], points[:, 1], 'ro-', 
                       linewidth=2, markersize=5, label='Current')
        
        # Labels and styling
        self.ax.set_xlabel('Trace Number', fontsize=11, weight='bold')
        self.ax.set_ylabel('Time (samples)', fontsize=11, weight='bold')
        self.ax.set_title('Seismic Interpretation', fontsize=13, weight='bold', pad=15)
        
        if self.horizons or self.current_horizon:
            self.ax.legend(loc='upper right', fontsize=9)
        
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        self.ax.tick_params(labelsize=9)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def start_picking(self):
        """Start horizon picking mode."""
        self.picking_mode = True
        self.btn_start_pick.setEnabled(False)
        self.btn_stop_pick.setEnabled(True)
        self.btn_save_horizon.setEnabled(True)
        self.info_label.setText("Picking mode active - click to add points")
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
        
    def stop_picking(self):
        """Stop horizon picking mode."""
        self.picking_mode = False
        self.btn_start_pick.setEnabled(True)
        self.btn_stop_pick.setEnabled(False)
        self.info_label.setText("Picking mode stopped")
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #f3e5f5;
                border: 1px solid #ba68c8;
                border-radius: 4px;
                font-weight: bold;
                color: #6a1b9a;
            }
        """)
        
    def on_click(self, event):
        """Handle mouse click for picking."""
        if not self.picking_mode or event.inaxes != self.ax:
            return
            
        # Add point to current horizon
        x, y = int(event.xdata), int(event.ydata)
        self.current_horizon.append([x, y])
        
        # Update display
        self.display_data()
        
    def save_horizon(self):
        """Save current horizon."""
        if len(self.current_horizon) == 0:
            QMessageBox.warning(self, "Warning", "No points picked.")
            return
            
        # Simple naming
        horizon_name = f"Horizon_{len(self.horizons) + 1}"
        
        self.horizons[horizon_name] = self.current_horizon.copy()
        self.horizon_list.addItem(horizon_name)
        
        # Clear current
        self.current_horizon = []
        self.display_data()
        
        self.btn_export.setEnabled(True)
        self.btn_delete.setEnabled(True)
        
        self.info_label.setText(f"Saved {horizon_name}")
        
    def clear_current_horizon(self):
        """Clear current horizon picks."""
        self.current_horizon = []
        self.display_data()
        
    def display_selected_horizon(self, item):
        """Highlight selected horizon."""
        horizon_name = item.text()
        self.display_data()
        
    def delete_horizon(self):
        """Delete selected horizon."""
        current_item = self.horizon_list.currentItem()
        if current_item is None:
            return
            
        horizon_name = current_item.text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {horizon_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.horizons[horizon_name]
            self.horizon_list.takeItem(self.horizon_list.currentRow())
            self.display_data()
            
    def export_horizon(self):
        """Export selected horizon."""
        current_item = self.horizon_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "Warning", "Select a horizon to export.")
            return
            
        QMessageBox.information(
            self,
            "Export",
            "Export functionality will save horizon picks to file."
        )
