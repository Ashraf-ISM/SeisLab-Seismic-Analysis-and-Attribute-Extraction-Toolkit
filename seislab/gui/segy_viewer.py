"""
Seismic Viewer Widget
Professional seismic data visualization
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QAction, QLabel
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use("Qt5Agg")

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import colors

import matplotlib.pyplot as plt
import numpy as np


class SeismicViewer(QWidget):
    """Widget for displaying seismic sections."""

    def __init__(self):
        super().__init__()

        self.current_data = None
        self.colormap = "seismic"
        self.gain = 1.0
        self.clip = 99.0
        self.max_render_points = 120

        self.setup_ui()

    # -------------------------------------------------------------
    # UI
    # -------------------------------------------------------------

    def setup_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.figure = Figure(figsize=(10, 8), facecolor="white")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: white;")

        self.ax = self.figure.add_subplot(111)

        self.toolbar = NavigationToolbar(self.canvas, self)

        self.info_label = QLabel("No data loaded")
        self.info_label.setStyleSheet(
            """
            QLabel {
                padding: 8px;
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
                font-weight: bold;
                color: #1976d2;
            }
            """
        )

        layout.addWidget(self.info_label)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.show_empty_plot()

    # -------------------------------------------------------------
    # Empty plot
    # -------------------------------------------------------------

    def show_empty_plot(self):

        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        self.ax.text(
            0.5,
            0.5,
            "Load SEG-Y data to begin\n\nFile → Open SEG-Y\nor\nSurvey → Open SEG-Y Survey",
            ha="center",
            va="center",
            fontsize=16,
            color="#757575",
            transform=self.ax.transAxes,
        )

        self.ax.set_xticks([])
        self.ax.set_yticks([])

        for spine in self.ax.spines.values():
            spine.set_visible(False)

        self.canvas.draw()

    # -------------------------------------------------------------
    # Reset axis
    # -------------------------------------------------------------

    def _new_axis(self, three_d=False):

        self.figure.clear()

        if three_d:
            self.ax = self.figure.add_subplot(111, projection="3d")
        else:
            self.ax = self.figure.add_subplot(111)

    # -------------------------------------------------------------
    # 2D seismic section
    # -------------------------------------------------------------

    def display_section(self, data, colormap="seismic", gain=1.0, clip=99.0):

        self.current_data = data
        self.colormap = colormap
        self.gain = gain
        self.clip = clip

        if data is None:
            self.show_empty_plot()
            return

        self._new_axis(False)

        plot_data = data * gain

        clip_val = np.percentile(np.abs(plot_data), clip)
        vmin = -clip_val
        vmax = clip_val

        im = self.ax.imshow(
            plot_data.T,
            aspect="auto",
            cmap=colormap,
            vmin=vmin,
            vmax=vmax,
            origin="upper",
            interpolation="nearest",
        )

        cbar = self.figure.colorbar(im, ax=self.ax, pad=0.02)
        cbar.set_label("Amplitude", fontsize=10)

        self.ax.set_xlabel("Trace Number", fontsize=11, weight="bold")
        self.ax.set_ylabel("Time (samples)", fontsize=11, weight="bold")
        self.ax.set_title("Seismic Section", fontsize=13, weight="bold")

        self.ax.invert_yaxis()

        self.ax.grid(True, alpha=0.3)

        self.info_label.setText(
            f"Shape: {data.shape[0]} × {data.shape[1]} | "
            f"Min: {data.min():.3f} | Max: {data.max():.3f}"
        )

        self.canvas.draw_idle()

    # -------------------------------------------------------------
    # Inline / Crossline Viewer
    # -------------------------------------------------------------

    def display_inline_crossline(
        self,
        volume,
        inline_index,
        crossline_index,
        timeslice_index=None,
        show_inline=True,
        show_crossline=True,
        show_timeslice=True,
        colormap="seismic",
        gain=1.0,
        clip=99.0,
        show_grid=True,
        show_axis=True,
    ):

        if volume is None:
            self.show_empty_plot()
            return

        if volume.ndim != 3:
            self.show_empty_plot()
            return

        ni, nx, nt = volume.shape

        # --------------------------------------------------
        # AUTO DETECT 2D DATA
        # --------------------------------------------------

        if nx == 1:
            section = volume[:, 0, :]
            self.display_section(section, colormap, gain, clip)
            return

        inline_index = int(np.clip(inline_index, 0, ni - 1))
        crossline_index = int(np.clip(crossline_index, 0, nx - 1))

        if timeslice_index is None:
            timeslice_index = nt // 2

        timeslice_index = int(np.clip(timeslice_index, 0, nt - 1))

        self._new_axis(True)

        plot_volume = volume * gain

        clip_val = np.percentile(np.abs(plot_volume), clip)
        vmin = -clip_val
        vmax = clip_val

        cmap = plt.get_cmap(colormap)
        norm = colors.Normalize(vmin=vmin, vmax=vmax)

        x_coords = np.arange(nx)
        y_coords = np.arange(ni)
        z_coords = np.arange(nt)

        step_x = max(1, int(np.ceil(nx / self.max_render_points)))
        step_y = max(1, int(np.ceil(ni / self.max_render_points)))
        step_z = max(1, int(np.ceil(nt / self.max_render_points)))

        x_sub = x_coords[::step_x]
        y_sub = y_coords[::step_y]
        z_sub = z_coords[::step_z]

        # --------------------------------------------------
        # INLINE
        # --------------------------------------------------

        if show_inline:

            inline_data = plot_volume[inline_index, :, :].T

            X, Z = np.meshgrid(x_sub, z_sub)
            Y = np.full_like(X, inline_index)

            inline_sub = inline_data[::step_z, ::step_x]

            self.ax.plot_surface(
                X,
                Y,
                Z,
                facecolors=cmap(norm(inline_sub)),
                shade=False,
                linewidth=0,
            )

        # --------------------------------------------------
        # CROSSLINE
        # --------------------------------------------------

        if show_crossline:

            xline_data = plot_volume[:, crossline_index, :].T

            Y, Z = np.meshgrid(y_sub, z_sub)
            X = np.full_like(Y, crossline_index)

            xline_sub = xline_data[::step_z, ::step_y]

            self.ax.plot_surface(
                X,
                Y,
                Z,
                facecolors=cmap(norm(xline_sub)),
                shade=False,
                linewidth=0,
            )

        # --------------------------------------------------
        # TIMESLICE
        # --------------------------------------------------

        if show_timeslice:

            ts_data = plot_volume[:, :, timeslice_index]

            X, Y = np.meshgrid(x_sub, y_sub)
            Z = np.full_like(X, timeslice_index)

            ts_sub = ts_data[::step_y, ::step_x]

            self.ax.plot_surface(
                X,
                Y,
                Z,
                facecolors=cmap(norm(ts_sub)),
                shade=False,
                linewidth=0,
                alpha=0.9,
            )

        self.ax.set_xlabel("Crossline")
        self.ax.set_ylabel("Inline")
        self.ax.set_zlabel("Sample")

        self.ax.invert_zaxis()
        self.ax.view_init(24, -62)

        self.ax.grid(show_grid)

        if not show_axis:
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_zticks([])

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        cbar = self.figure.colorbar(sm, ax=self.ax, pad=0.08, shrink=0.65)
        cbar.set_label("Amplitude")

        self.info_label.setText(
            f"Volume: {ni} × {nx} × {nt} | Inline {inline_index} | Crossline {crossline_index}"
        )

        self.canvas.draw_idle()

    # -------------------------------------------------------------
    # Wiggle plot
    # -------------------------------------------------------------

    def plot_wiggle(self, data, traces_to_plot=50):

        if data is None:
            return

        self._new_axis(False)

        n_traces = min(data.shape[0], traces_to_plot)
        skip = max(1, data.shape[0] // n_traces)

        t = np.arange(data.shape[1])
        spacing = np.max(np.abs(data)) * 2

        for i, trace_idx in enumerate(range(0, data.shape[0], skip)):

            trace = data[trace_idx]

            self.ax.plot(trace + i * spacing, t, "k", linewidth=0.8)

            self.ax.fill_betweenx(
                t,
                i * spacing,
                trace + i * spacing,
                where=(trace > 0),
                color="black",
                alpha=0.6,
            )

        self.ax.invert_yaxis()

        self.ax.set_xlabel("Trace")
        self.ax.set_ylabel("Time")
        self.ax.set_title("Wiggle Plot")

        self.canvas.draw_idle()

    # -------------------------------------------------------------
    # Reset
    # -------------------------------------------------------------

    def reset_view(self):

        if self.current_data is not None:
            self.display_section(self.current_data, self.colormap, self.gain, self.clip)
        else:
            self.show_empty_plot()

    # -------------------------------------------------------------
    # Update
    # -------------------------------------------------------------

    def update_view(self, new_data):

        self.display_section(new_data, self.colormap, self.gain, self.clip)
