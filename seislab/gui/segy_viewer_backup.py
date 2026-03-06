# """
# Seismic Viewer Widget
# Professional seismic data visualization
# """

# from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QAction, QLabel
# from PyQt5.QtCore import Qt
# import matplotlib
# matplotlib.use('Qt5Agg')
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
# import numpy as np


# class SeismicViewer(QWidget):
#     """Widget for displaying seismic sections."""
    
#     def __init__(self):
#         super().__init__()
        
#         self.current_data = None
#         self.colormap = 'seismic'
#         self.gain = 1.0
#         self.clip = 99.0
        
#         self.setup_ui()
        
#     def setup_ui(self):
#         """Initialize the user interface."""
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(5, 5, 5, 5)
        
#         # Create matplotlib figure
#         self.figure = Figure(figsize=(10, 8), facecolor='white')
#         self.canvas = FigureCanvas(self.figure)
#         self.canvas.setStyleSheet("background-color: white;")
        
#         # Create axis
#         self.ax = self.figure.add_subplot(111)
        
#         # Navigation toolbar
#         self.toolbar = NavigationToolbar(self.canvas, self)
#         self.toolbar.setStyleSheet("""
#             QToolBar {
#                 background-color: #fafafa;
#                 border: 1px solid #e0e0e0;
#                 padding: 4px;
#             }
#         """)
        
#         # Info label
#         self.info_label = QLabel("No data loaded")
#         self.info_label.setStyleSheet("""
#             QLabel {
#                 padding: 8px;
#                 background-color: #e3f2fd;
#                 border: 1px solid #90caf9;
#                 border-radius: 4px;
#                 font-weight: bold;
#                 color: #1976d2;
#             }
#         """)
        
#         # Add widgets
#         layout.addWidget(self.info_label)
#         layout.addWidget(self.toolbar)
#         layout.addWidget(self.canvas)
        
#         # Initial empty plot
#         self.show_empty_plot()
        
#     def show_empty_plot(self):
#         """Display empty plot with instructions."""
#         self.ax.clear()
#         self.ax.text(0.5, 0.5, 'Load SEG-Y data to begin\n\nFile → Open SEG-Y',
#                     ha='center', va='center', fontsize=16, color='#757575',
#                     transform=self.ax.transAxes)
#         self.ax.set_xticks([])
#         self.ax.set_yticks([])
#         self.ax.spines['top'].set_visible(False)
#         self.ax.spines['right'].set_visible(False)
#         self.ax.spines['bottom'].set_visible(False)
#         self.ax.spines['left'].set_visible(False)
#         self.canvas.draw()
        
#     def display_section(self, data, colormap='seismic', gain=1.0, clip=99.0):
#         """
#         Display seismic section.
        
#         Args:
#             data: 2D numpy array of seismic data
#             colormap: Colormap name
#             gain: Gain multiplier
#             clip: Clip percentage
#         """
#         self.current_data = data
#         self.colormap = colormap
#         self.gain = gain
#         self.clip = clip
        
#         if data is None:
#             self.show_empty_plot()
#             return
            
#         # Clear previous plot
#         self.ax.clear()
        
#         # Apply gain
#         plot_data = data * gain
        
#         # Calculate clip values
#         vmin = np.percentile(plot_data, 100 - clip)
#         vmax = np.percentile(plot_data, clip)
        
#         # Ensure symmetric colorscale for seismic data
#         if colormap == 'seismic':
#             vmax = max(abs(vmin), abs(vmax))
#             vmin = -vmax
            
#         # Plot seismic section
#         im = self.ax.imshow(plot_data.T, aspect='auto', cmap=colormap,
#                            vmin=vmin, vmax=vmax, interpolation='bilinear')
        
#         # Add colorbar
#         cbar = self.figure.colorbar(im, ax=self.ax, pad=0.02)
#         cbar.set_label('Amplitude', fontsize=10, weight='bold')
#         cbar.ax.tick_params(labelsize=9)
        
#         # Labels
#         self.ax.set_xlabel('Trace Number', fontsize=11, weight='bold')
#         self.ax.set_ylabel('Time (samples)', fontsize=11, weight='bold')
#         self.ax.set_title('Seismic Section', fontsize=13, weight='bold', pad=15)
        
#         # Grid
#         self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
#         # Update info
#         self.info_label.setText(
#             f"Shape: {data.shape[0]} × {data.shape[1]} | "
#             f"Min: {data.min():.3f} | Max: {data.max():.3f} | "
#             f"Mean: {data.mean():.3f}"
#         )
        
#         # Style adjustments
#         self.ax.tick_params(labelsize=9)
#         for spine in self.ax.spines.values():
#             spine.set_edgecolor('#e0e0e0')
#             spine.set_linewidth(1.5)
            
#         self.figure.tight_layout()
#         self.canvas.draw()
        
#     def plot_wiggle(self, data, traces_to_plot=50):
#         """
#         Display wiggle plot.
        
#         Args:
#             data: 2D numpy array
#             traces_to_plot: Number of traces to display
#         """
#         if data is None:
#             return
            
#         self.ax.clear()
        
#         n_traces = min(data.shape[0], traces_to_plot)
#         skip = max(1, data.shape[0] // n_traces)
        
#         for i in range(0, data.shape[0], skip):
#             trace = data[i, :]
#             x = np.arange(len(trace)) + i * 2
#             self.ax.plot(trace, x, 'k-', linewidth=0.5)
            
#         self.ax.set_xlabel('Amplitude', fontsize=11, weight='bold')
#         self.ax.set_ylabel('Time (samples)', fontsize=11, weight='bold')
#         self.ax.set_title('Wiggle Plot', fontsize=13, weight='bold', pad=15)
#         self.ax.invert_yaxis()
#         self.ax.grid(True, alpha=0.3)
        
#         self.figure.tight_layout()
#         self.canvas.draw()
        
#     def reset_view(self):
#         """Reset view to default."""
#         if self.current_data is not None:
#             self.display_section(self.current_data, self.colormap, self.gain, self.clip)
#         else:
#             self.show_empty_plot()
            
#     def update_view(self, new_data):
#         """
#         Update display with new data.
        
#         Args:
#             new_data: 2D numpy array
#         """
#         self.display_section(new_data, self.colormap, self.gain, self.clip)
