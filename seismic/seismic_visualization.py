"""
Qt-based seismic visualization — matplotlib 3-D embedded in Qt.

NO PyVista. NO QWebEngineView. Only matplotlib (already installed).

WHY PREVIOUS VERSIONS WERE PATCHY
-----------------------------------
1. PyVista renders VTK cells.  Each cell covers (rstride × cstride) samples.
   Default is rstride=cstride=1 but VTK still blends only 4 corners per cell,
   and each corner maps to multiple screen pixels → blocky.

2. The old matplotlib code also had this problem because it used the default
   rstride/cstride which skips rows/columns.

THE FIX
-------
matplotlib plot_surface with facecolors + rstride=1, cstride=1 renders
every single sample as its own coloured face.  This gives the same
per-sample resolution as Plotly WebGL.

We embed the matplotlib figure in Qt using FigureCanvasQTAgg.
"""

from __future__ import annotations
import argparse
import sys
import numpy as np

import matplotlib
matplotlib.use("Qt5Agg")   # must be before pyplot import

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  registers the 3d projection

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QApplication, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QSlider, QSpinBox,
    QVBoxLayout, QWidget,
)

if __package__:
    from .segy_loader import SegyLoader
else:
    from segy_loader import SegyLoader


# ---------------------------------------------------------------------------
# Core draw function — completely standalone, testable without Qt
# ---------------------------------------------------------------------------

def draw_seismic_3d(ax,
                    data: np.ndarray,
                    inline_idx: int,
                    xline_idx: int,
                    vmin: float,
                    vmax: float) -> None:
    """
    Draw inline + crossline slices on a matplotlib 3-D axes.

    Parameters
    ----------
    ax          : Axes3D
    data        : ndarray (ni, nx, nt)  float32
    inline_idx  : which inline to show
    xline_idx   : which crossline to show
    vmin, vmax  : amplitude clip limits
    """
    ax.clear()

    ni, nx, nt = data.shape
    cmap = plt.cm.RdBu_r
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    # ------------------------------------------------------------------
    # INLINE SLICE
    # axes: X = crossline (0..nx-1), Y = inline_idx (const), Z = time
    # meshgrid convention for plot_surface: X[row,col], Y[row,col], Z[row,col]
    # use indexing='xy' (default) so rows = Z-axis, cols = X-axis
    # ------------------------------------------------------------------
    amp_il = data[inline_idx, :, :]          # (nx, nt)

    xv = np.arange(nx)
    zv = np.arange(nt)
    Xil, Zil = np.meshgrid(xv, zv)          # both (nt, nx)  — 'xy' indexing
    Yil = np.full_like(Xil, inline_idx, dtype=float)

    # facecolors must match the (nt-1, nx-1) face grid produced by plot_surface
    # with rstride=1, cstride=1.  We use the (nt, nx) colour array; matplotlib
    # automatically crops to (nt-1, nx-1) faces.  amp_il.T → (nt, nx) to align.
    fc_il = cmap(norm(amp_il.T))             # (nt, nx, 4)

    ax.plot_surface(
        Xil, Yil, Zil,
        facecolors=fc_il,
        shade=False,
        rstride=1, cstride=1,               # ← every sample = one face
        antialiased=False,
    )

    # ------------------------------------------------------------------
    # CROSSLINE SLICE
    # axes: X = xline_idx (const), Y = inline (0..ni-1), Z = time
    # ------------------------------------------------------------------
    amp_xl = data[:, xline_idx, :]           # (ni, nt)

    yv = np.arange(ni)
    Yxl, Zxl = np.meshgrid(yv, zv)          # both (nt, ni)
    Xxl = np.full_like(Yxl, xline_idx, dtype=float)

    fc_xl = cmap(norm(amp_xl.T))             # (nt, ni, 4)

    ax.plot_surface(
        Xxl, Yxl, Zxl,
        facecolors=fc_xl,
        shade=False,
        rstride=1, cstride=1,
        antialiased=False,
    )

    # ------------------------------------------------------------------
    # Colour bar  (manual — plot_surface with facecolors has no auto cbar)
    # ------------------------------------------------------------------
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # Remove old colorbars if any
    if hasattr(ax, '_seislab_cbar') and ax._seislab_cbar is not None:
        try:
            ax._seislab_cbar.remove()
        except Exception:
            pass

    ax._seislab_cbar = ax.get_figure().colorbar(
        sm, ax=ax, shrink=0.5, pad=0.05, label="Amplitude"
    )

    # ------------------------------------------------------------------
    # Labels / appearance
    # ------------------------------------------------------------------
    ax.set_xlabel("Crossline", labelpad=6)
    ax.set_ylabel("Inline",    labelpad=6)
    ax.set_zlabel("Time",      labelpad=6)
    ax.invert_zaxis()   # time increases downward

    ax.set_title(
        f"Inline {inline_idx}  |  Crossline {xline_idx}",
        fontsize=11, pad=10
    )

    ax.set_facecolor("#1a1a2e")
    ax.get_figure().patch.set_facecolor("#1a1a2e")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.zaxis.label.set_color("white")
    ax.title.set_color("white")


# ---------------------------------------------------------------------------
# Qt viewer widget
# ---------------------------------------------------------------------------

class SeisLab3DViewer(QWidget):

    def __init__(self, loader, inline_idx=None, xline_idx=None, clip=98.0, parent=None):
        super().__init__(parent)

        if loader.data is None:
            raise ValueError("Seismic data not loaded")

        self.loader = loader
        self.data   = np.asarray(loader.data, dtype=np.float32)
        self.clip   = clip

        self.ni, self.nx, self.nt = self.data.shape
        self.inline_idx = inline_idx if inline_idx is not None else self.ni // 2
        self.xline_idx  = xline_idx  if xline_idx  is not None else self.nx // 2

        self.vmin = float(np.percentile(self.data, 100.0 - clip))
        self.vmax = float(np.percentile(self.data,         clip))

        # matplotlib figure + canvas
        self.fig = Figure(figsize=(10, 8), facecolor="#1a1a2e")
        self.ax  = self.fig.add_subplot(111, projection="3d")
        self.canvas = FigureCanvas(self.fig)

        self.info_label = QLabel()
        self._setup_ui()
        self._refresh()

    # -----------------------------------------------------------------------
    def _setup_ui(self):
        self.setWindowTitle("SeisLab Seismic Cube Viewer")
        root = QVBoxLayout(self)

        box  = QGroupBox("Slice Controls")
        form = QFormLayout(box)

        self.il_slider, self.il_spin = self._make_ctrl(self.ni, self.inline_idx)
        self.xl_slider, self.xl_spin = self._make_ctrl(self.nx, self.xline_idx)

        for slider, spin, label, slot in [
            (self.il_slider, self.il_spin, "Inline",    self._on_inline),
            (self.xl_slider, self.xl_spin, "Crossline", self._on_xline),
        ]:
            slider.valueChanged.connect(spin.setValue)
            spin.valueChanged.connect(slot)
            row = QHBoxLayout()
            row.addWidget(slider)
            row.addWidget(spin)
            w = QWidget(); w.setLayout(row)
            form.addRow(label, w)

        root.addWidget(box)
        root.addWidget(self.info_label)
        root.addWidget(self.canvas, stretch=1)

    def _make_ctrl(self, size, value):
        s = QSlider(Qt.Horizontal)
        s.setRange(0, size - 1); s.setValue(value)
        b = QSpinBox()
        b.setRange(0, size - 1); b.setValue(value)
        return s, b

    # -----------------------------------------------------------------------
    def _refresh(self):
        draw_seismic_3d(
            self.ax, self.data,
            self.inline_idx, self.xline_idx,
            self.vmin, self.vmax,
        )
        self.canvas.draw()
        self.info_label.setText(
            f"Cube {self.ni} × {self.nx} × {self.nt}  |  "
            f"Inline {self.inline_idx}  |  Crossline {self.xline_idx}  |  "
            f"clip [{self.vmin:.0f} … {self.vmax:.0f}]"
        )

    def _on_inline(self, v):
        self.inline_idx = v
        self.il_slider.blockSignals(True); self.il_slider.setValue(v); self.il_slider.blockSignals(False)
        self._refresh()

    def _on_xline(self, v):
        self.xline_idx = v
        self.xl_slider.blockSignals(True); self.xl_slider.setValue(v); self.xl_slider.blockSignals(False)
        self._refresh()


# ---------------------------------------------------------------------------
# Entry-points  (same public API as before)
# ---------------------------------------------------------------------------

def load_and_show(filepath):
    loader = SegyLoader(filepath)
    loader.load_data()
    app = QApplication.instance() or QApplication(sys.argv)
    v = SeisLab3DViewer(loader)
    v.resize(1400, 900)
    v.show()
    return v, app


def build_argument_parser():
    p = argparse.ArgumentParser(description="SeisLab 3-D seismic cube viewer")
    p.add_argument("filepath")
    p.add_argument("--inline", type=int,   default=None)
    p.add_argument("--xline",  type=int,   default=None)
    p.add_argument("--clip",   type=float, default=98.0)
    return p


def main():
    args = build_argument_parser().parse_args()
    _, app = load_and_show(args.filepath)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()