"""
Attribute Panel
Interface for computing and displaying seismic attributes.

Design: Professional light-theme geoscience workstation (Petrel / Kingdom style).
        Clean whites, slate accents, crisp typography — always light.
        Visual Parameters / Sample Data / Amplitude Distribution panels are
        intentionally NOT part of this widget (they live elsewhere in the app).
"""

import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QComboBox,
    QSpinBox,
    QProgressBar,
    QMessageBox,
    QFileDialog,
    QDialog,
    QFrame,
    QSizePolicy,
    QAbstractItemView,
    QMenu,
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint
from PyQt5.QtGui import QColor

import numpy as np
import matplotlib

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import colors as mcolors
import matplotlib.pyplot as plt

from attributes.seismic_attributes import SeismicAttributes


# ═════════════════════════════════════════════════════════════════════════════
#  DESIGN TOKENS
# ═════════════════════════════════════════════════════════════════════════════
C = {
    "bg_app":        "#F0F3F7",
    "bg_panel":      "#FFFFFF",
    "bg_sidebar":    "#F7F9FC",
    "bg_input":      "#FFFFFF",
    "bg_row_alt":    "#F8FAFD",
    "bg_hover":      "#EEF4FF",
    "bg_selected":   "#DDE9FA",
    "border":        "#D1DCE8",
    "border_focus":  "#2A78D4",
    "divider":       "#E8EEF5",
    "text_primary":  "#1A2535",
    "text_secondary":"#526070",
    "text_muted":    "#9DAFC0",
    "text_white":    "#FFFFFF",
    "accent":        "#1558A8",
    "accent_hover":  "#0F4A8E",
    "accent_light":  "#EBF2FC",
    "ok":            "#1A7A4C",
    "ok_bg":         "#EAF6EF",
    "ok_border":     "#9FD5B8",
    "error":         "#C0221E",
    "error_bg":      "#FEE8E8",
    "error_border":  "#F4A5A3",
    "progress_bg":   "#DDE6F0",
    "progress_fill": "#2A78D4",
}

STYLESHEET = """
/* ── Root ─────────────────────────────────────────────────────────────── */
QWidget#AttributePanel {
    background-color: %(bg_app)s;
}
QWidget {
    background-color: %(bg_app)s;
    color: %(text_primary)s;
    font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
}

/* ── Sidebar container ───────────────────────────────────────────────── */
QWidget#sidebar {
    background-color: %(bg_sidebar)s;
    border-right: 1px solid %(border)s;
}

/* ── Section headers (replacing QGroupBox) ──────────────────────────── */
QLabel#section_header {
    color: %(text_muted)s;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.4px;
    background: transparent;
    padding: 0;
    border: none;
}

/* ── Inputs ──────────────────────────────────────────────────────────── */
QComboBox {
    background-color: %(bg_input)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 4px 28px 4px 8px;
    color: %(text_primary)s;
    min-height: 26px;
    font-size: 12px;
}
QComboBox:hover  { border-color: %(accent)s; }
QComboBox:focus  { border-color: %(border_focus)s; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid %(text_muted)s;
    width: 0; height: 0;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: %(bg_panel)s;
    border: 1px solid %(border)s;
    selection-background-color: %(bg_selected)s;
    selection-color: %(accent)s;
    color: %(text_primary)s;
    outline: none;
    padding: 2px;
}
QComboBox QAbstractItemView::item { padding: 5px 10px; min-height: 24px; }
QComboBox QAbstractItemView::item:hover { background-color: %(bg_hover)s; }

QSpinBox {
    background-color: %(bg_input)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 4px 8px;
    color: %(text_primary)s;
    min-height: 26px;
    font-size: 12px;
}
QSpinBox:hover { border-color: %(accent)s; }
QSpinBox:focus { border-color: %(border_focus)s; }
QSpinBox::up-button, QSpinBox::down-button {
    background-color: %(bg_app)s;
    border: none;
    border-left: 1px solid %(border)s;
    width: 18px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: %(bg_hover)s; }

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton#btn_compute {
    background-color: %(accent)s;
    border: 1px solid %(accent)s;
    border-radius: 4px;
    color: %(text_white)s;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 0;
    min-height: 30px;
}
QPushButton#btn_compute:hover   { background-color: %(accent_hover)s; }
QPushButton#btn_compute:pressed { background-color: #0C3E7A; }
QPushButton#btn_compute:disabled {
    background-color: #C8D9EE;
    border-color: #B8CCE0;
    color: %(text_muted)s;
}
QPushButton#btn_export {
    background-color: %(bg_panel)s;
    border: 1px solid %(ok_border)s;
    border-radius: 4px;
    color: %(ok)s;
    font-size: 11px;
    font-weight: 600;
    padding: 5px 0;
    min-height: 26px;
}
QPushButton#btn_export:hover   { background-color: %(ok_bg)s; }
QPushButton#btn_export:pressed { background-color: #C2E8D4; }
QPushButton#btn_export:disabled {
    background-color: %(bg_app)s;
    border-color: %(border)s;
    color: %(text_muted)s;
}

/* ── List ────────────────────────────────────────────────────────────── */
QListWidget {
    background-color: %(bg_panel)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    color: %(text_primary)s;
    outline: none;
    padding: 2px;
    alternate-background-color: %(bg_row_alt)s;
}
QListWidget::item {
    padding: 5px 8px;
    border-bottom: 1px solid %(divider)s;
    border-radius: 3px;
    margin: 1px 0;
    font-size: 11px;
}
QListWidget::item:selected {
    background-color: %(bg_selected)s;
    color: %(accent)s;
    border-left: 2px solid %(accent)s;
}
QListWidget::item:hover:!selected { background-color: %(bg_hover)s; }

/* ── Progress ────────────────────────────────────────────────────────── */
QProgressBar {
    background-color: %(progress_bg)s;
    border: none;
    border-radius: 2px;
    height: 3px;
    color: transparent;
}
QProgressBar::chunk { background-color: %(progress_fill)s; border-radius: 2px; }

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel { color: %(text_secondary)s; font-size: 11px; background: transparent; }

/* ── Scrollbars ──────────────────────────────────────────────────────── */
QScrollBar:vertical { background: %(bg_app)s; width: 7px; border: none; }
QScrollBar::handle:vertical { background: %(border)s; border-radius: 3px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: %(accent)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: %(bg_app)s; height: 7px; border: none; }
QScrollBar::handle:horizontal { background: %(border)s; border-radius: 3px; min-width: 20px; }
QScrollBar::handle:horizontal:hover { background: %(accent)s; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Tooltips ────────────────────────────────────────────────────────── */
QToolTip {
    background-color: %(text_primary)s;
    border: none;
    color: #FFFFFF;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 11px;
}
""" % C

# ─────────────────────────────────────────────────────────────────────────────
#  Attribute metadata
# ─────────────────────────────────────────────────────────────────────────────
ATTR_META = {
    "RMS Amplitude":           {"color": "#C0392B", "tag": "AMP",   "cmap": "inferno"},
    "Instantaneous Amplitude": {"color": "#E67E22", "tag": "AMP",   "cmap": "inferno"},
    "Instantaneous Phase":     {"color": "#8E44AD", "tag": "INST",  "cmap": "twilight_shifted"},
    "Instantaneous Frequency": {"color": "#D35400", "tag": "INST",  "cmap": "magma"},
    "Envelope":                {"color": "#2980B9", "tag": "AMP",   "cmap": "Blues"},
    "Sweetness":               {"color": "#27AE60", "tag": "SPEC",  "cmap": "YlGn"},
    "Dominant Frequency":      {"color": "#F39C12", "tag": "SPEC",  "cmap": "magma"},
    "Coherence":               {"color": "#1A6FBF", "tag": "STRUC", "cmap": "plasma"},
    "Variance":                {"color": "#E74C3C", "tag": "STRUC", "cmap": "hot"},
    "Dip":                     {"color": "#16A085", "tag": "STRUC", "cmap": "RdBu_r"},
    "Azimuth":                 {"color": "#6C3483", "tag": "STRUC", "cmap": "hsv"},
    "Curvature":               {"color": "#117A65", "tag": "STRUC", "cmap": "RdBu_r"},
}


def _attribute_compute_kwargs(window_size: int) -> dict:
    win = int(window_size)
    win_traces = max(3, min(21, (win // 4) | 1))
    return {
        "window": win,
        "ws":     win_traces,
        "wt":     win,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  Background thread
# ═════════════════════════════════════════════════════════════════════════════
class AttributeComputeThread(QThread):
    finished = pyqtSignal(np.ndarray, str)
    error    = pyqtSignal(str)

    def __init__(self, data, attribute_name, window_size=25,
                 sample_rate_ms=2.0, sample_axis=1):
        super().__init__()
        self.data           = data
        self.attribute_name = attribute_name
        self.window_size    = window_size
        self.sample_rate_ms = sample_rate_ms
        self.sample_axis    = sample_axis

    def run(self):
        try:
            calc   = SeismicAttributes(sample_rate_ms=self.sample_rate_ms)
            result = calc.compute_attribute(
                self.data, self.attribute_name,
                sample_axis=self.sample_axis,
                **_attribute_compute_kwargs(self.window_size),
            )
            self.finished.emit(result, self.attribute_name)
        except Exception as e:
            self.error.emit(str(e))


# ═════════════════════════════════════════════════════════════════════════════
#  Helper widgets
# ═════════════════════════════════════════════════════════════════════════════
class HRule(QFrame):
    """Thin horizontal rule."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background:{C['divider']}; border:none; margin:0;")


def _section_header(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("section_header")
    lbl.setStyleSheet(
        f"color:{C['text_muted']}; font-size:10px; font-weight:700;"
        f"letter-spacing:1.4px; background:transparent; padding:0; border:none;"
    )
    return lbl


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{C['text_secondary']}; font-size:11px; font-weight:600;"
        f"background:transparent; padding:0;"
    )
    return lbl


class StatusBadge(QLabel):
    _PRESETS = {
        "idle":    ("● Ready",        C["bg_app"],      C["text_muted"],  C["border"]),
        "working": ("◌ Computing…",   C["accent_light"],C["accent"],      C["accent"]),
        "ok":      ("✔ Computed",      C["ok_bg"],       C["ok"],          C["ok_border"]),
        "error":   ("✖ Failed",        C["error_bg"],    C["error"],       C["error_border"]),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(22)
        self.set_state("idle")

    def set_state(self, state: str, label: str = ""):
        text, bg, fg, bd = self._PRESETS.get(state, self._PRESETS["idle"])
        if label:
            text = label
        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {bd};
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.3px;
                padding: 1px 8px;
            }}
        """)


def _stat_row(key: str, parent_layout) -> QLabel:
    row = QHBoxLayout()
    row.setSpacing(0)
    row.setContentsMargins(0, 0, 0, 0)
    lbl = QLabel(key)
    lbl.setFixedWidth(54)
    lbl.setStyleSheet(f"color:{C['text_muted']};font-size:10px;background:transparent;")
    val = QLabel("—")
    val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    val.setStyleSheet(
        f"color:{C['text_primary']};font-size:10px;"
        f"font-family:'Consolas','Courier New',monospace;font-weight:600;background:transparent;"
    )
    row.addWidget(lbl)
    row.addWidget(val)
    parent_layout.addLayout(row)
    return val


# ═════════════════════════════════════════════════════════════════════════════
#  3-D dialog (unchanged logic, refreshed visuals)
# ═════════════════════════════════════════════════════════════════════════════
class Attribute3DDialog(QDialog):
    def __init__(self, volume, attribute_name, inline_index,
                 crossline_index, timeslice_index, cmap,
                 sample_rate_ms, window_size, parent=None):
        super().__init__(parent)
        self.volume           = np.asarray(volume) if volume is not None else None
        self.attribute_name   = attribute_name
        self.inline_index     = int(inline_index or 0)
        self.crossline_index  = int(crossline_index or 0)
        self.timeslice_index  = int(timeslice_index or 0)
        self.cmap_name        = cmap
        self.sample_rate_ms   = float(sample_rate_ms or 2.0)
        self.window_size      = int(window_size)

        self.setWindowTitle(f"3D Slice View — {attribute_name}")
        self.resize(1180, 820)
        self.setMinimumSize(840, 620)
        self._build_ui()
        self._render_slices()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel(f"{self.attribute_name}  —  3D Inline / Crossline Slice View")
        header.setStyleSheet(
            f"color:{C['text_primary']};font-size:14px;font-weight:700;padding:0;"
        )
        layout.addWidget(header)

        self.figure  = Figure(figsize=(10, 7), facecolor="#0B0F14")
        self.canvas  = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet(
            f"QToolBar {{ background:{C['bg_app']}; border:1px solid {C['border']}; }}"
        )
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)

    def _compute_attribute_slice(self, section):
        calc = SeismicAttributes(sample_rate_ms=self.sample_rate_ms)
        return calc.compute_attribute(
            section, self.attribute_name, sample_axis=1,
            **_attribute_compute_kwargs(self.window_size),
        )

    def _render_slices(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection="3d")
        ax.set_facecolor("#0B0F14")
        self.figure.patch.set_facecolor("#0B0F14")

        volume = np.asarray(self.volume) if self.volume is not None else None
        if volume is None or volume.ndim != 3 or volume.size == 0:
            ax.text2D(0.5, 0.5, "No seismic volume available",
                      transform=ax.transAxes, ha="center", va="center",
                      fontsize=12, color="#D7E2F0")
            ax.set_axis_off()
            self.canvas.draw_idle()
            return

        ni, nx, nt = volume.shape
        self.inline_index    = int(np.clip(self.inline_index,    0, ni - 1))
        self.crossline_index = int(np.clip(self.crossline_index, 0, nx - 1))
        self.timeslice_index = int(np.clip(self.timeslice_index, 0, nt - 1))

        inline_attr    = self._compute_attribute_slice(volume[self.inline_index, :, :])
        crossline_attr = self._compute_attribute_slice(volume[:, self.crossline_index, :])

        finite_parts = [
            np.asarray(p)[np.isfinite(np.asarray(p))]
            for p in (inline_attr, crossline_attr)
            if np.asarray(p)[np.isfinite(np.asarray(p))].size
        ]
        if not finite_parts:
            ax.text2D(0.5, 0.5, "Attribute slices contain no finite values",
                      transform=ax.transAxes, ha="center", va="center",
                      fontsize=12, color="#D7E2F0")
            ax.set_axis_off()
            self.canvas.draw_idle()
            return

        finite = np.concatenate(finite_parts)
        lo = float(np.percentile(finite, 2))
        hi = float(np.percentile(finite, 98))
        if not np.isfinite(lo) or not np.isfinite(hi) or np.isclose(lo, hi):
            lo, hi = float(np.min(finite)), float(np.max(finite))
        if np.isclose(lo, hi):
            hi = lo + 1.0

        cmap = plt.get_cmap(self.cmap_name or "viridis")
        norm = mcolors.Normalize(vmin=lo, vmax=hi)

        x_coords = np.arange(nx)
        y_coords = np.arange(ni)
        z_coords = np.arange(nt)

        step_x = max(1, int(np.ceil(nx / 220)))
        step_y = max(1, int(np.ceil(ni / 220)))
        step_z = max(1, int(np.ceil(nt / 180)))

        x_sub = x_coords[::step_x]
        y_sub = y_coords[::step_y]
        z_sub = z_coords[::step_z]

        inline_data = np.asarray(inline_attr).T
        X_inline, Z_inline = np.meshgrid(x_sub, z_sub)
        Y_inline = np.full_like(X_inline, self.inline_index)
        ax.plot_surface(X_inline, Y_inline, Z_inline,
                        facecolors=cmap(norm(np.clip(inline_data[::step_z, ::step_x], lo, hi))),
                        shade=False, linewidth=0, antialiased=False, alpha=0.98)

        crossline_data = np.asarray(crossline_attr).T
        Y_xline, Z_xline = np.meshgrid(y_sub, z_sub)
        X_xline = np.full_like(Y_xline, self.crossline_index)
        ax.plot_surface(X_xline, Y_xline, Z_xline,
                        facecolors=cmap(norm(np.clip(crossline_data[::step_z, ::step_y], lo, hi))),
                        shade=False, linewidth=0, antialiased=False, alpha=0.98)

        # intersection lines
        z_line = z_coords[::step_z]
        ax.plot(np.full_like(z_line, self.crossline_index, dtype=float),
                np.full_like(z_line, self.inline_index, dtype=float),
                z_line.astype(float), color="#00D3FF", linewidth=1.6, alpha=0.95)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = self.figure.colorbar(sm, ax=ax, pad=0.08, shrink=0.7)
        cbar.set_label(self.attribute_name, fontsize=10, color="#D7E2F0")
        cbar.ax.yaxis.set_tick_params(labelsize=8, color="#B7C7D9")
        plt.setp(cbar.ax.get_yticklabels(), color="#D7E2F0")
        cbar.outline.set_edgecolor("#546375")

        ax.set_title(
            f"{self.attribute_name}  —  IL {self.inline_index} / XL {self.crossline_index}",
            fontsize=12, fontweight="bold", color="#E7EEF7", pad=14,
        )
        for lbl, setter in [("Crossline", ax.set_xlabel),
                             ("Inline",    ax.set_ylabel),
                             ("Sample",    ax.set_zlabel)]:
            setter(lbl, fontsize=10, color="#D7E2F0", labelpad=8)
        for axis in ("x", "y", "z"):
            ax.tick_params(axis=axis, colors="#B7C7D9", labelsize=8)

        ax.view_init(elev=23, azim=-58)
        ax.invert_yaxis()
        ax.invert_zaxis()
        ax.grid(True, alpha=0.15)
        try:
            ax.xaxis.set_pane_color((0.06, 0.08, 0.11, 1.0))
            ax.yaxis.set_pane_color((0.06, 0.08, 0.11, 1.0))
            ax.zaxis.set_pane_color((0.08, 0.10, 0.13, 1.0))
        except Exception:
            pass

        self.figure.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.03)
        self.canvas.draw_idle()


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN PANEL
# ═════════════════════════════════════════════════════════════════════════════
class AttributePanel(QWidget):
    """
    Self-contained seismic attribute extraction and display panel.
    Professional light workstation theme.
    Does NOT include Visual Parameters, Sample Data, or Amplitude Distribution.
    """

    ATTRIBUTE_ITEMS = list(ATTR_META.keys())

    ATTRIBUTE_ALIASES = {
        "rms":                "RMS Amplitude",
        "inst_amp":           "Instantaneous Amplitude",
        "inst_phase":         "Instantaneous Phase",
        "inst_freq":          "Instantaneous Frequency",
        "envelope":           "Envelope",
        "sweetness":          "Sweetness",
        "dominant_frequency": "Dominant Frequency",
        "coherence":          "Coherence",
        "variance":           "Variance",
        "dip":                "Dip",
        "azimuth":            "Azimuth",
        "curvature":          "Curvature",
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("AttributePanel")
        self.current_attribute       = None
        self.current_attribute_name  = None
        self.current_image_matrix    = None
        self.current_volume          = None
        self.current_inline_index    = 0
        self.current_crossline_index = 0
        self.current_timeslice_index = 0
        self.attribute_results       = {}
        self.input_data              = None
        self.sample_rate_ms          = 2.0
        self.sample_axis             = 1
        self.current_section_kind    = "Section"
        self.current_section_index   = None
        self.current_x_label         = "Trace Number"
        self.current_y_label         = "Time (samples)"
        self.current_display_cmap    = None
        self.current_grid_visible    = True
        self.current_interpolation   = "bilinear"
        self._data_signature         = None
        self._default_plot_hint      = "Right-click image for options"
        self._three_d_dialog         = None

        self.setStyleSheet(STYLESHEET)
        self._configure_mpl()
        self._build_ui()

    # ── matplotlib light theme ────────────────────────────────────────────
    def _configure_mpl(self):
        plt.rcParams.update({
            "figure.facecolor": "#FFFFFF",
            "axes.facecolor":   "#FAFBFC",
            "axes.edgecolor":   C["border"],
            "axes.labelcolor":  C["text_secondary"],
            "axes.titlecolor":  C["text_primary"],
            "xtick.color":      "#718096",
            "ytick.color":      "#718096",
            "text.color":       C["text_primary"],
            "grid.color":       C["divider"],
            "grid.linestyle":   "--",
            "grid.linewidth":   0.5,
            "axes.grid":        True,
            "axes.titlesize":   12,
            "axes.titleweight": "bold",
            "axes.labelsize":   10,
            "axes.labelweight": "bold",
        })

    # ── root layout ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_left())
        root.addWidget(self._build_right(), stretch=1)

    # ═════════════════════════════════════════════════════════════════════
    #  LEFT SIDEBAR
    # ═════════════════════════════════════════════════════════════════════
    def _build_left(self) -> QWidget:
        w = QWidget()
        w.setObjectName("sidebar")
        w.setFixedWidth(256)

        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(16)

        # ── Attribute Selection ──────────────────────────────────────────
        lay.addWidget(_section_header("Attribute Selection"))

        lay.addWidget(_field_label("Type"))
        self.attr_combo = QComboBox()
        for name in self.ATTRIBUTE_ITEMS:
            tag = ATTR_META.get(name, {}).get("tag", "")
            self.attr_combo.addItem(f"{name}  [{tag}]")
        self.attr_combo.setToolTip("Select the seismic attribute to compute")
        lay.addWidget(self.attr_combo)

        lay.addWidget(_field_label("Window (samples)"))
        self.window_spin = QSpinBox()
        self.window_spin.setMinimum(5)
        self.window_spin.setMaximum(101)
        self.window_spin.setValue(25)
        self.window_spin.setSingleStep(2)
        self.window_spin.setToolTip("Analysis window length in samples")
        lay.addWidget(self.window_spin)

        self.context_label = QLabel("Active section: awaiting data")
        self.context_label.setWordWrap(True)
        self.context_label.setStyleSheet(
            f"color:{C['text_muted']};font-size:10px;background:transparent;"
        )
        lay.addWidget(self.context_label)

        self.btn_compute = QPushButton("Compute Attribute")
        self.btn_compute.setObjectName("btn_compute")
        self.btn_compute.setCursor(Qt.PointingHandCursor)
        self.btn_compute.clicked.connect(self.compute_selected_attribute)
        lay.addWidget(self.btn_compute)

        lay.addWidget(HRule())

        # ── Computed Results ─────────────────────────────────────────────
        lay.addWidget(_section_header("Computed Results"))

        self.attr_list = QListWidget()
        self.attr_list.setAlternatingRowColors(True)
        self.attr_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.attr_list.setMinimumHeight(100)
        self.attr_list.setMaximumHeight(180)
        self.attr_list.itemClicked.connect(self._on_list_click)
        lay.addWidget(self.attr_list)

        self.btn_export = QPushButton("Save Current Image")
        self.btn_export.setObjectName("btn_export")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._save_current_plot)
        lay.addWidget(self.btn_export)

        lay.addWidget(HRule())

        # ── Statistics ───────────────────────────────────────────────────
        lay.addWidget(_section_header("Statistics"))

        stats_lay = QVBoxLayout()
        stats_lay.setSpacing(2)
        stats_lay.setContentsMargins(0, 0, 0, 0)
        self._s_min  = _stat_row("Min",     stats_lay)
        self._s_max  = _stat_row("Max",     stats_lay)
        self._s_mean = _stat_row("Mean",    stats_lay)
        self._s_std  = _stat_row("Std Dev", stats_lay)
        stats_lay.addSpacing(2)
        self._s_p1   = _stat_row("P1",      stats_lay)
        self._s_p99  = _stat_row("P99",     stats_lay)
        lay.addLayout(stats_lay)

        lay.addStretch()
        return w

    # ═════════════════════════════════════════════════════════════════════
    #  RIGHT — plot area
    # ═════════════════════════════════════════════════════════════════════
    def _build_right(self) -> QWidget:
        w   = QWidget()
        w.setStyleSheet(f"background:{C['bg_app']};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # ── toolbar row ──────────────────────────────────────────────────
        tb = QHBoxLayout()
        tb.setSpacing(8)
        tb.setContentsMargins(0, 0, 0, 0)

        self.status_badge = StatusBadge()
        self.status_badge.setFixedWidth(130)
        tb.addWidget(self.status_badge)

        self.title_label = QLabel("No attribute selected")
        self.title_label.setStyleSheet(
            f"color:{C['text_primary']};font-size:13px;font-weight:700;background:transparent;"
        )
        tb.addWidget(self.title_label)
        tb.addStretch()

        self.plot_hint = QLabel(self._default_plot_hint)
        self._style_hint(enabled=False)
        tb.addWidget(self.plot_hint)

        self.cmap_chip = QLabel()
        self.cmap_chip.setVisible(False)
        self.cmap_chip.setStyleSheet(f"""
            QLabel {{
                background-color: {C['accent_light']};
                color: {C['accent']};
                border: 1px solid {C['accent']};
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                padding: 2px 7px;
                background: transparent;
            }}
        """)
        tb.addWidget(self.cmap_chip)
        lay.addLayout(tb)

        # ── progress bar ─────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setFixedHeight(3)
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        lay.addWidget(self.progress)

        # ── matplotlib canvas ────────────────────────────────────────────
        self.figure = Figure(figsize=(11.5, 7.2), facecolor="#FFFFFF")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumHeight(480)
        self.canvas.setCursor(Qt.CrossCursor)
        self.canvas.setToolTip("Right-click for save, colormap, 3D view, and display options.")
        self.canvas.setStyleSheet(
            f"background:#FFFFFF; border:1px solid {C['border']}; border-radius:6px;"
        )
        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)
        lay.addWidget(self.canvas, 1)

        self.ax = self.figure.add_subplot(111)
        self._show_empty_plot()
        return w

    # ─────────────────────────────────────────────────────────────────────
    #  Hint label style
    # ─────────────────────────────────────────────────────────────────────
    def _style_hint(self, enabled: bool = True):
        fg = C["accent"]      if enabled else C["text_muted"]
        bg = C["accent_light"] if enabled else C["bg_app"]
        bd = "#BED3EE"         if enabled else C["border"]
        self.plot_hint.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {bd};
                border-radius: 10px;
                font-size: 10px;
                font-weight: 600;
                padding: 3px 9px;
                background: transparent;
            }}
        """)

    def _set_plot_hint(self, text: str, enabled: bool = True):
        if not hasattr(self, "plot_hint"):
            return
        self.plot_hint.setText(text)
        self._style_hint(enabled)

    # ─────────────────────────────────────────────────────────────────────
    #  Empty placeholder
    # ─────────────────────────────────────────────────────────────────────
    def _show_empty_plot(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#F8FAFC")
        self.figure.patch.set_facecolor("#FFFFFF")
        self.current_attribute      = None
        self.current_attribute_name = None
        self.current_image_matrix   = None

        for sp in self.ax.spines.values():
            sp.set_edgecolor(C["border"])
            sp.set_linewidth(0.8)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.grid(False)
        self.ax.text(0.5, 0.54, "Attribute Preview",
                     ha="center", va="center", fontsize=15,
                     color="#A0B4C8", fontweight="bold",
                     transform=self.ax.transAxes)
        section_desc = self._section_descriptor()
        self.ax.text(0.5, 0.44,
                     f"{section_desc} — select an attribute and press Compute",
                     ha="center", va="center", fontsize=10,
                     color="#B8C8D8", transform=self.ax.transAxes)
        self.figure.subplots_adjust(left=0.04, right=0.98, top=0.96, bottom=0.06)
        self._set_plot_hint(self._default_plot_hint, enabled=False)
        self.canvas.draw_idle()

    # ─────────────────────────────────────────────────────────────────────
    #  Public data interface
    # ─────────────────────────────────────────────────────────────────────
    def set_data(self, data, sample_rate_ms=None, sample_axis=1,
                 section_kind="Section", section_index=None,
                 horizontal_label="Trace Number", vertical_label="Time (samples)",
                 volume=None, inline_index=0, crossline_index=0, timeslice_index=0):
        self.input_data              = data
        self.sample_axis             = 1 if sample_axis == 1 else 0
        if sample_rate_ms is not None:
            self.sample_rate_ms = float(sample_rate_ms)
        self.current_volume          = np.asarray(volume) if volume is not None else None
        self.current_inline_index    = int(inline_index or 0)
        self.current_crossline_index = int(crossline_index or 0)
        self.current_timeslice_index = int(timeslice_index or 0)

        prev_signature = self._data_signature
        self.current_section_kind  = section_kind
        self.current_section_index = section_index
        self.current_x_label       = horizontal_label
        self.current_y_label       = vertical_label
        self._data_signature       = (
            section_kind, section_index,
            tuple(np.shape(data)),
            round(self.sample_rate_ms, 6),
        )

        shape        = " × ".join(str(v) for v in np.shape(data)) if data is not None else "n/a"
        section_desc = self._section_descriptor()
        self.context_label.setText(
            f"{section_desc}  ·  {shape}  ·  {self.sample_rate_ms:.2f} ms"
        )
        if prev_signature is not None and prev_signature != self._data_signature:
            self._reset_for_new_section()

    def _section_descriptor(self) -> str:
        if self.current_section_index is None:
            return self.current_section_kind
        return f"{self.current_section_kind} {self.current_section_index}"

    def _reset_for_new_section(self):
        self.attribute_results.clear()
        self.attr_list.clear()
        self.btn_export.setEnabled(False)
        self.current_attribute      = None
        self.current_attribute_name = None
        self.current_image_matrix   = None
        self.cmap_chip.setVisible(False)
        self.title_label.setText(f"{self._section_descriptor()} ready")
        self.title_label.setStyleSheet(
            f"color:{C['text_primary']};font-size:13px;font-weight:700;background:transparent;"
        )
        self.status_badge.set_state("idle")
        self._clear_stats()
        self._show_empty_plot()

    def _clear_stats(self):
        for w in (self._s_min, self._s_max, self._s_mean,
                  self._s_std, self._s_p1, self._s_p99):
            w.setText("—")

    def _canonical(self, name: str) -> str:
        key = str(name).strip()
        if "  [" in key:
            key = key.split("  [")[0].strip()
        if key in self.ATTRIBUTE_ALIASES:
            return self.ATTRIBUTE_ALIASES[key]
        return key

    # ─────────────────────────────────────────────────────────────────────
    #  Computation
    # ─────────────────────────────────────────────────────────────────────
    def compute_selected_attribute(self):
        name = self._canonical(self.attr_combo.currentText())
        if self.input_data is None:
            QMessageBox.warning(self, "No Data",
                                "No seismic section is loaded.\n"
                                "Please open a SEG-Y file first.")
            return
        self.compute_attribute(
            name,
            self.input_data,
            sample_rate_ms=self.sample_rate_ms,
            sample_axis=self.sample_axis,
            window_size=self.window_spin.value(),
        )

    def compute_attribute(self, attribute_name, data,
                          sample_rate_ms=None, sample_axis=1, window_size=None):
        if data is None:
            QMessageBox.warning(self, "No Data", "No seismic data available.")
            return

        self.input_data  = data
        self.sample_axis = 1 if sample_axis == 1 else 0
        if sample_rate_ms is not None:
            self.sample_rate_ms = float(sample_rate_ms)

        attribute_name = self._canonical(attribute_name)
        if window_size is None:
            window_size = self.window_spin.value() if hasattr(self, "window_spin") else 25

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.btn_compute.setEnabled(False)
        self.status_badge.set_state("working")
        self.title_label.setText(f"Computing {attribute_name}…")
        self.cmap_chip.setVisible(False)

        self._thread = AttributeComputeThread(
            data, attribute_name,
            window_size=window_size,
            sample_rate_ms=self.sample_rate_ms,
            sample_axis=self.sample_axis,
        )
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()
    
    # ─────────────────────────────────────────────────────────────────────
    #  Thread callbacks
    # ─────────────────────────────────────────────────────────────────────
    def _on_finished(self, result: np.ndarray, attribute_name: str):
        self.progress.setVisible(False)
        self.btn_compute.setEnabled(True)
        self.attribute_results[attribute_name] = result

        existing = [self.attr_list.item(i).data(Qt.UserRole)
                    for i in range(self.attr_list.count())]
        if attribute_name not in existing:
            meta  = ATTR_META.get(attribute_name, {})
            color = meta.get("color", C["accent"])
            item  = QListWidgetItem(f"  {attribute_name}")
            item.setData(Qt.UserRole, attribute_name)
            item.setForeground(QColor(color))
            fnt = item.font()
            fnt.setPointSize(10)
            item.setFont(fnt)
            self.attr_list.addItem(item)

        self.display_attribute(result, attribute_name)
        self.status_badge.set_state("ok", f"✔  {attribute_name}")
        self.btn_export.setEnabled(True)

    def _on_error(self, msg: str):
        self.progress.setVisible(False)
        self.btn_compute.setEnabled(True)
        self.status_badge.set_state("error")
        self.title_label.setText("Computation failed")
        QMessageBox.critical(self, "Computation Error",
                             f"Attribute computation failed:\n\n{msg}")

    # ─────────────────────────────────────────────────────────────────────
    #  List click
    # ─────────────────────────────────────────────────────────────────────
    def _on_list_click(self, item: QListWidgetItem):
        name = item.data(Qt.UserRole)
        if name and name in self.attribute_results:
            self.display_attribute(self.attribute_results[name], name)

    # ─────────────────────────────────────────────────────────────────────
    #  Display
    # ─────────────────────────────────────────────────────────────────────
    def display_attribute(self, data: np.ndarray, attribute_name: str):
        self.current_attribute      = np.asarray(data)
        self.current_attribute_name = attribute_name
        self._render_current_attribute()

    def _render_current_attribute(self):
        if self.current_attribute is None or not self.current_attribute_name:
            self._show_empty_plot()
            return

        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#FAFBFC")
        self.figure.patch.set_facecolor("#FFFFFF")

        data           = self.current_attribute
        attribute_name = self.current_attribute_name
        arr            = np.asarray(data)
        p01            = float(np.nanpercentile(arr, 1))
        p99            = float(np.nanpercentile(arr, 99))
        if not np.isfinite(p01) or not np.isfinite(p99):
            p01, p99 = 0.0, 1.0

        meta         = ATTR_META.get(attribute_name, {})
        default_cmap = meta.get("cmap", "viridis")
        cmap         = self.current_display_cmap or default_cmap
        attr_color   = meta.get("color", C["accent"])
        display      = arr.T
        self.current_image_matrix = display

        if attribute_name == "Instantaneous Phase":
            vmin, vmax = -np.pi, np.pi
        elif attribute_name == "Azimuth":
            vmin, vmax = 0.0, 360.0
        elif attribute_name == "Coherence":
            vmin, vmax = 0.0, 1.0
        elif attribute_name in {"Dip", "Curvature"}:
            clip = max(abs(p01), abs(p99), 1e-9)
            vmin, vmax = -clip, clip
        else:
            vmin, vmax = (max(0.0, p01) if p01 >= 0 else p01), p99

        im = self.ax.imshow(
            display, aspect="auto", cmap=cmap,
            vmin=vmin, vmax=vmax,
            interpolation=self.current_interpolation,
            origin="upper",
        )

        cbar = self.figure.colorbar(im, ax=self.ax,
                                    pad=0.010, fraction=0.020, shrink=0.92)
        cbar.ax.yaxis.set_tick_params(labelsize=8, color="#718096")
        cbar.outline.set_edgecolor(C["border"])
        cbar.outline.set_linewidth(0.6)
        cbar.set_label(attribute_name, fontsize=9, fontweight="bold",
                       color=C["text_secondary"], labelpad=6)
        plt.setp(cbar.ax.get_yticklabels(), color=C["text_secondary"])

        self.ax.set_title(
            f"{attribute_name}  —  {self._section_descriptor()}",
            fontsize=12, fontweight="bold", color=attr_color, pad=8,
        )
        self.ax.set_xlabel(self.current_x_label, fontsize=10, fontweight="bold",
                           color=C["text_secondary"], labelpad=4)
        self.ax.set_ylabel(self.current_y_label, fontsize=10, fontweight="bold",
                           color=C["text_secondary"], labelpad=4)
        for sp in self.ax.spines.values():
            sp.set_edgecolor(C["border"])
            sp.set_linewidth(0.6)
        self.ax.tick_params(axis="both", labelsize=8, colors="#718096",
                            length=3, width=0.5)
        self.ax.grid(self.current_grid_visible, alpha=0.4, linestyle="--",
                     linewidth=0.35, color=C["divider"])

        self.figure.subplots_adjust(left=0.07, right=0.93, top=0.90, bottom=0.10)
        self.canvas.draw_idle()

        self.title_label.setText(attribute_name)
        self.title_label.setStyleSheet(
            f"color:{attr_color};font-size:13px;font-weight:700;background:transparent;"
        )
        self.cmap_chip.setText(f"cmap: {cmap}")
        self.cmap_chip.setVisible(True)
        self._set_plot_hint(self._default_plot_hint, enabled=True)
        self.status_badge.set_state("ok", f"✔  {attribute_name}")
        self._update_stats(arr)

    # ─────────────────────────────────────────────────────────────────────
    #  Canvas interaction
    # ─────────────────────────────────────────────────────────────────────
    def _on_canvas_click(self, event):
        if event.inaxes != self.ax or self.current_attribute is None:
            return
        button = str(getattr(event.button, "name", event.button)).lower()
        if button in {"3", "right", "mousebutton.right"}:
            self._show_plot_context_menu(event)
        elif button in {"1", "left", "mousebutton.left"}:
            self._show_cursor_sample(event)

    def _show_cursor_sample(self, event):
        if self.current_image_matrix is None:
            return
        if event.xdata is None or event.ydata is None:
            return
        x_idx = int(round(event.xdata))
        y_idx = int(round(event.ydata))
        h, w = self.current_image_matrix.shape
        if not (0 <= y_idx < h and 0 <= x_idx < w):
            return
        value = float(self.current_image_matrix[y_idx, x_idx])
        self._set_plot_hint(
            f"{self.current_x_label}: {x_idx}  ·  "
            f"{self.current_y_label}: {y_idx}  ·  val: {value:.5g}",
            enabled=True,
        )

    def _show_plot_context_menu(self, event):
        if self.current_attribute is None:
            return

        menu     = QMenu(self)
        save_act = menu.addAction("Save Image As…")
        copy_act = menu.addAction("Copy Image to Clipboard")
        view_3d  = menu.addAction("Open 3D Inline / Crossline View")
        menu.addSeparator()

        restore_act = menu.addAction("Restore Defaults")
        grid_act    = menu.addAction("Show Grid")
        grid_act.setCheckable(True)
        grid_act.setChecked(self.current_grid_visible)

        interp_menu = menu.addMenu("Interpolation")
        smooth_act  = interp_menu.addAction("Smooth")
        smooth_act.setCheckable(True)
        smooth_act.setChecked(self.current_interpolation == "bilinear")
        exact_act   = interp_menu.addAction("Exact Samples")
        exact_act.setCheckable(True)
        exact_act.setChecked(self.current_interpolation == "nearest")

        cmap_menu    = menu.addMenu("Colormap")
        cmap_actions = {}
        default_cmap     = ATTR_META.get(self.current_attribute_name, {}).get("cmap", "viridis")
        using_default    = self.current_display_cmap is None
        effective_cmap   = self.current_display_cmap or default_cmap
        for label, cmap_name in [
            ("Attribute Default", None),
            ("Inferno",  "inferno"),
            ("Seismic",  "seismic"),
            ("Viridis",  "viridis"),
            ("Plasma",   "plasma"),
            ("Hot",      "hot"),
            ("Gray",     "gray"),
        ]:
            act = cmap_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(
                (cmap_name is None and using_default)
                or (cmap_name is not None and not using_default and cmap_name == effective_cmap)
            )
            cmap_actions[act] = cmap_name

        chosen = menu.exec_(self._event_global_pos(event))
        if chosen is None:
            return
        if chosen == save_act:
            self._save_current_plot()
        elif chosen == copy_act:
            self._copy_plot_to_clipboard()
        elif chosen == view_3d:
            self._open_3d_view()
        elif chosen == restore_act:
            self.current_display_cmap  = None
            self.current_grid_visible  = True
            self.current_interpolation = "bilinear"
            self._render_current_attribute()
        elif chosen == grid_act:
            self.current_grid_visible = grid_act.isChecked()
            self._render_current_attribute()
        elif chosen == smooth_act:
            self.current_interpolation = "bilinear"
            self._render_current_attribute()
        elif chosen == exact_act:
            self.current_interpolation = "nearest"
            self._render_current_attribute()
        elif chosen in cmap_actions:
            self.current_display_cmap = cmap_actions[chosen]
            self._render_current_attribute()

    def _event_global_pos(self, event):
        gui_event = getattr(event, "guiEvent", None)
        if gui_event is not None and hasattr(gui_event, "globalPos"):
            return gui_event.globalPos()
        x = int(getattr(event, "x",  self.canvas.width()  / 2))
        y = int(self.canvas.height() - getattr(event, "y", self.canvas.height() / 2))
        return self.canvas.mapToGlobal(QPoint(x, y))

    def _copy_plot_to_clipboard(self):
        QApplication.clipboard().setPixmap(self.canvas.grab())
        self._set_plot_hint("Image copied to clipboard", enabled=True)

    def _open_3d_view(self):
        if self.current_attribute is None or not self.current_attribute_name:
            return
        if self.current_volume is None or getattr(self.current_volume, "ndim", 0) != 3:
            QMessageBox.information(
                self, "3D Slice View",
                "A loaded seismic volume is required for the 3D inline/crossline view.",
            )
            return

        cmap_name = self.current_display_cmap or ATTR_META.get(
            self.current_attribute_name, {}).get("cmap", "viridis")

        if self._three_d_dialog is not None:
            try:
                self._three_d_dialog.close()
            except Exception:
                pass

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._three_d_dialog = Attribute3DDialog(
                self.current_volume,
                self.current_attribute_name,
                self.current_inline_index,
                self.current_crossline_index,
                self.current_timeslice_index,
                cmap_name,
                self.sample_rate_ms,
                self.window_spin.value(),
                parent=self,
            )
        finally:
            QApplication.restoreOverrideCursor()
        self._three_d_dialog.show()
        self._three_d_dialog.raise_()
        self._three_d_dialog.activateWindow()
        self._set_plot_hint("Opened 3D inline / crossline view", enabled=True)

    def _save_current_plot(self):
        if self.current_attribute is None or not self.current_attribute_name:
            return
        section_name = self._section_descriptor().lower().replace(" ", "_")
        base_name    = f"{self.current_attribute_name.lower().replace(' ', '_')}_{section_name}"
        path, _      = QFileDialog.getSaveFileName(
            self, "Save Attribute Image", f"{base_name}.png",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;PDF Document (*.pdf);;SVG Vector (*.svg)",
        )
        if not path:
            return
        root, ext = os.path.splitext(path)
        if not ext:
            path = root + ".png"
        self.figure.savefig(path, dpi=220, bbox_inches="tight", facecolor="#FFFFFF")
        self._set_plot_hint(f"Saved: {os.path.basename(path)}", enabled=True)

    # ─────────────────────────────────────────────────────────────────────
    #  Statistics
    # ─────────────────────────────────────────────────────────────────────
    def _update_stats(self, data: np.ndarray):
        finite = data.ravel()
        finite = finite[np.isfinite(finite)]
        if len(finite) == 0:
            self._clear_stats()
            return
        f = lambda v: f"{v:.5g}"
        self._s_min.setText(f(float(np.min(finite))))
        self._s_max.setText(f(float(np.max(finite))))
        self._s_mean.setText(f(float(np.mean(finite))))
        self._s_std.setText(f(float(np.std(finite))))
        self._s_p1.setText(f(float(np.percentile(finite, 1))))
        self._s_p99.setText(f(float(np.percentile(finite, 99))))

    # ── backward-compat public aliases ───────────────────────────────────
    def show_empty_plot(self):           self._show_empty_plot()
    def on_compute_finished(self, r, n): self._on_finished(r, n)
    def on_compute_error(self, msg):     self._on_error(msg)
    def display_selected_attribute(self, item): self._on_list_click(item)
