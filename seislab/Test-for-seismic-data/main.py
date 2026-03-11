import sys
import numpy as np
import plotly.graph_objects as go
import segyio
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView

class SegyViewerApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(SegyViewerApp, self).__init__()
        
        # Load the UI file created in Qt Designer
        uic.loadUi('viewer.ui', self)
        
        # Load and apply the modern light theme
        try:
            with open('style.qss', 'r') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: style.qss not found. Using default styling.")

        # Internal data state
        self.data_cube = None

        # Setup Plotly Web Engine View (Replaces Matplotlib)
        self.web_view = QWebEngineView(self)
        self.plot_layout.addWidget(self.web_view)
        self.set_empty_view()

        # Connect UI Elements to Functions
        self.btn_load.clicked.connect(self.load_segy)
        self.combo_cmap.currentTextChanged.connect(self.plot_3d)
        self.spin_clip.valueChanged.connect(self.plot_3d)

    def set_empty_view(self):
        """Displays a placeholder when no data is loaded."""
        empty_html = """
        <html>
            <body style='background-color: #F8F9FA; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; color: #6C757D;'>
                <h2>No SEGY Data Loaded</h2>
            </body>
        </html>
        """
        self.web_view.setHtml(empty_html)

    def load_segy(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open SEG-Y File", "", "SEG-Y Files (*.sgy *.segy);;All Files (*)", options=options
        )
        
        if not file_path:
            return

        try:
            # Your manual reshaping logic to bypass missing geometry
            with segyio.open(file_path, ignore_geometry=True) as f:
                traces = np.array([np.copy(t) for t in f.trace])
                n_traces, n_samples = traces.shape
                
                # approximate grid
                n_inline = int(np.sqrt(n_traces))
                n_crossline = n_traces // n_inline
                traces = traces[:n_inline * n_crossline]
                
                self.data_cube = traces.reshape(n_inline, n_crossline, n_samples)
                
            self.plot_3d()
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading File", f"Could not read SEG-Y file:\n{str(e)}")

    def plot_3d(self):
        if self.data_cube is None:
            return

        # Fetch settings from GUI
        clip = self.spin_clip.value()
        cmap_choice = self.combo_cmap.currentText()
        
        # Map GUI colormap names to Plotly colorscales
        colorscale_map = {
            "seismic": "RdBu_r",
            "gray": "Greys",
            "RdBu": "RdBu_r"
        }
        plotly_cmap = colorscale_map.get(cmap_choice, "RdBu_r")

        # Downsample for faster rendering in 3D (adjust as needed)
        downsample = 2
        data = self.data_cube[::downsample, ::downsample, ::downsample]
        ni, nx, nt = data.shape
        
        inline_idx = ni // 2
        xline_idx = nx // 2
        
        vmin, vmax = np.percentile(data, [100 - clip, clip])
        
        fig = go.Figure()
        
        # Inline slice
        inline = data[inline_idx, :, :].T
        X, Z = np.meshgrid(np.arange(nx), np.arange(nt))
        Y = np.full_like(X, inline_idx)
        fig.add_surface(
            x=X, y=Y, z=Z,
            surfacecolor=inline,
            colorscale=plotly_cmap,
            cmin=vmin, cmax=vmax,
            showscale=True
        )
        
        # Crossline slice
        cross = data[:, xline_idx, :].T
        Y, Z = np.meshgrid(np.arange(ni), np.arange(nt))
        X = np.full_like(Y, xline_idx)
        fig.add_surface(
            x=X, y=Y, z=Z,
            surfacecolor=cross,
            colorscale=plotly_cmap,
            cmin=vmin, cmax=vmax,
            showscale=False
        )
        
        fig.update_layout(
            scene=dict(
                xaxis_title="Crossline",
                yaxis_title="Inline",
                zaxis_title="Time",
                zaxis=dict(autorange="reversed"),
                aspectratio=dict(x=1, y=1, z=1.5),
                bgcolor="#F8F9FA" # Match light theme
            ),
            margin=dict(l=0, r=0, b=0, t=30),
            paper_bgcolor="#F8F9FA"
        )
        
        # Convert the Plotly figure to HTML and render it in the QWebEngineView
        html = fig.to_html(include_plotlyjs='cdn')
        self.web_view.setHtml(html)

if __name__ == '__main__':
    # Enable High DPI scaling for modern high-res monitors
    QtWidgets.QApplication.setAttribute(sys.modules['PyQt5.QtCore'].Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(sys.modules['PyQt5.QtCore'].Qt.AA_UseHighDpiPixmaps, True)
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    viewer = SegyViewerApp()
    viewer.show()
    sys.exit(app.exec_())