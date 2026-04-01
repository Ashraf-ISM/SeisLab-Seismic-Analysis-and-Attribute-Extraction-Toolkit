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
#  DESIGN TOKENS — light workstation palette
# ═════════════════════════════════════════════════════════════════════════════
C = {
    "bg_app":       "#E9EFF5",
    "bg_panel":     "#FFFFFF",
    "bg_input":     "#FFFFFF",
    "bg_row_alt":   "#F5F8FC",
    "bg_hover":     "#EAF3FF",
    "bg_selected":  "#D5E8FF",
    "border":       "#CCD7E3",
    "border_focus": "#2F80ED",
    "divider":      "#E3EAF2",
    "text_primary": "#172330",
    "text_secondary":"#4A5568",
    "text_muted":   "#9AA0AD",
    "text_white":   "#FFFFFF",
    "accent":       "#155C98",
    "accent_hover": "#114C7D",
    "accent_light": "#E6F0FA",
    "ok":           "#1B7F4F",
    "ok_bg":        "#E6F4EE",
    "ok_border":    "#A3D9BE",
    "error":        "#B91C1C",
    "error_bg":     "#FEE2E2",
    "error_border": "#FCA5A5",
    "progress_bg":  "#E2E8F0",
    "progress_fill":"#2F80ED",
}

LIGHT_SS = """
QWidget#AttributePanel {
    background-color: %(bg_app)s;
}
QWidget {
    background-color: %(bg_app)s;
    color: %(text_primary)s;
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
}
QGroupBox {
    background-color: %(bg_panel)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    margin-top: 20px;
    padding: 12px 12px 12px 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: 1px;
    padding: 2px 6px;
    background-color: %(bg_panel)s;
    color: %(accent)s;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.8px;
}
QFrame#hero_card {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #F7FBFF,
        stop: 1 #E6F1FB
    );
    border: 1px solid #BFD4E8;
    border-radius: 10px;
}
QFrame#plot_card, QFrame#info_card {
    background-color: %(bg_panel)s;
    border: 1px solid %(border)s;
    border-radius: 10px;
}
QLabel#hero_eyebrow {
    color: %(accent)s;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.8px;
}
QLabel#hero_title {
    color: %(text_primary)s;
    font-size: 18px;
    font-weight: 700;
}
QLabel#hero_subtitle {
    color: %(text_secondary)s;
    font-size: 11px;
}
QLabel#plot_hint {
    background-color: %(accent_light)s;
    color: %(accent)s;
    border: 1px solid #C6D9EE;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 700;
    padding: 4px 10px;
}
QLabel#context_label {
    color: %(text_secondary)s;
    font-size: 10px;
    padding-top: 2px;
}
QComboBox {
    background-color: %(bg_input)s;
    border: 1px solid %(border)s;
    border-radius: 5px;
    padding: 5px 32px 5px 10px;
    color: %(text_primary)s;
    min-height: 28px;
    selection-background-color: %(bg_selected)s;
}
QComboBox:hover  { border-color: %(accent)s; background-color: %(bg_hover)s; }
QComboBox:focus  { border-color: %(border_focus)s; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid %(accent)s;
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
QComboBox QAbstractItemView::item { padding: 6px 10px; min-height: 26px; }
QComboBox QAbstractItemView::item:hover { background-color: %(bg_hover)s; }
QSpinBox {
    background-color: %(bg_input)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 5px 8px;
    color: %(text_primary)s;
    min-height: 28px;
}
QSpinBox:hover { border-color: %(accent)s; }
QSpinBox:focus { border-color: %(border_focus)s; }
QSpinBox::up-button, QSpinBox::down-button {
    background-color: %(bg_app)s;
    border: none;
    border-left: 1px solid %(border)s;
    width: 20px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: %(bg_hover)s; }
QPushButton#btn_compute {
    background-color: %(accent)s;
    border: 1px solid %(accent)s;
    border-radius: 6px;
    color: %(text_white)s;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 8px 0;
    min-height: 36px;
}
QPushButton#btn_compute:hover { background-color: %(accent_hover)s; border-color: %(accent_hover)s; }
QPushButton#btn_compute:pressed { background-color: #0D4F8C; }
QPushButton#btn_compute:disabled {
    background-color: #DCE8F4;
    border-color: #C1D2E3;
    color: %(text_secondary)s;
}
QPushButton#btn_export {
    background-color: %(bg_panel)s;
    border: 1px solid %(ok_border)s;
    border-radius: 5px;
    color: %(ok)s;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 0;
    min-height: 30px;
}
QPushButton#btn_export:hover { background-color: %(ok_bg)s; border-color: %(ok)s; }
QPushButton#btn_export:pressed { background-color: #C6EDD9; }
QPushButton#btn_export:disabled {
    background-color: #F4F7FB;
    border-color: %(border)s;
    color: %(text_secondary)s;
}
QListWidget {
    background-color: %(bg_panel)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    color: %(text_primary)s;
    outline: none;
    padding: 4px;
    alternate-background-color: %(bg_row_alt)s;
}
QListWidget::item { padding: 8px 10px; border-bottom: 1px solid %(divider)s; border-radius: 4px; margin: 1px 0; }
QListWidget::item:selected { background-color: %(bg_selected)s; color: %(accent)s; border-left: 3px solid %(accent)s; }
QListWidget::item:hover:!selected { background-color: %(bg_hover)s; }
QProgressBar {
    background-color: %(progress_bg)s;
    border: none;
    border-radius: 4px;
    height: 6px;
    color: transparent;
}
QProgressBar::chunk { background-color: %(progress_fill)s; border-radius: 3px; }
QLabel { color: %(text_secondary)s; font-size: 11px; background: transparent; }
QScrollBar:vertical { background: %(bg_app)s; width: 8px; border: none; border-radius: 4px; }
QScrollBar::handle:vertical { background: %(border)s; border-radius: 4px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: %(accent)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: %(bg_app)s; height: 8px; border: none; }
QScrollBar::handle:horizontal { background: %(border)s; border-radius: 4px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: %(accent)s; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QToolTip { background-color: %(text_primary)s; border: none; color: #FFFFFF; padding: 5px 10px; border-radius: 4px; font-size: 11px; }
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
        "window_samples": win,
        "window_traces": win_traces,
        "sigma_samples": max(0.75, float(win) / 10.0),
        "sigma_traces": max(0.75, float(win_traces) / 6.0),
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
            calc = SeismicAttributes(sample_rate_ms=self.sample_rate_ms)
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
class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setStyleSheet(f"color: {C['divider']}; margin: 3px 0;")
        self.setFixedHeight(1)


class StatusBadge(QLabel):
    _PRESETS = {
        "idle":    ("●  Ready",         C["bg_app"],      C["text_muted"],  C["border"]),
        "working": ("◌  Computing …",   C["accent_light"],C["accent"],      C["accent"]),
        "ok":      ("✔  Computed",       C["ok_bg"],       C["ok"],          C["ok_border"]),
        "error":   ("✖  Failed",         C["error_bg"],    C["error"],       C["error_border"]),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(26)
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
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.4px;
                padding: 2px 10px;
            }}
        """)


def _stat_row(key: str, parent_layout) -> QLabel:
    row = QHBoxLayout()
    row.setSpacing(4)
    lbl = QLabel(f"{key}:")
    lbl.setFixedWidth(60)
    lbl.setStyleSheet(f"color:{C['text_muted']};font-size:10px;")
    val = QLabel("—")
    val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    val.setStyleSheet(
        f"color:{C['text_primary']};font-size:10px;"
        f"font-family:'Consolas','Courier New',monospace;font-weight:600;"
    )
    row.addWidget(lbl)
    row.addWidget(val)
    parent_layout.addLayout(row)
    return val


class Attribute3DDialog(QDialog):
    def __init__(self, volume, attribute_name, inline_index,
                 crossline_index, timeslice_index, cmap,
                 sample_rate_ms, window_size, parent=None):
        super().__init__(parent)
        self.volume = np.asarray(volume) if volume is not None else None
        self.attribute_name = attribute_name
        self.inline_index = int(inline_index or 0)
        self.crossline_index = int(crossline_index or 0)
        self.timeslice_index = int(timeslice_index or 0)
        self.cmap_name = cmap
        self.sample_rate_ms = float(sample_rate_ms or 2.0)
        self.window_size = int(window_size)

        self.setWindowTitle(f"3D Slice View — {attribute_name}")
        self.resize(1180, 820)
        self.setMinimumSize(840, 620)
        self._build_ui()
        self._render_slices()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QLabel(f"{self.attribute_name} — 3D Inline / Crossline Slice View")
        header.setStyleSheet(
            "color:#172330;"
            "font-size:15px;"
            "font-weight:700;"
            "padding:2px 0;"
        )
        layout.addWidget(header)

        hint = QLabel(
            "Orthogonal attribute slices for the active inline and crossline. Rotate with left-drag."
        )
        hint.setStyleSheet("color:#4A5568; font-size:11px;")
        layout.addWidget(hint)

        self.figure = Figure(figsize=(10, 7), facecolor="#0B0F14")
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet(
            "QToolBar { background:#F7FAFD; border:1px solid #D7E0EA; }"
        )

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)

    def _compute_attribute_slice(self, section):
        calc = SeismicAttributes(sample_rate_ms=self.sample_rate_ms)
        return calc.compute_attribute(
            section,
            self.attribute_name,
            sample_axis=1,
            **_attribute_compute_kwargs(self.window_size),
        )

    def _render_slices(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection="3d")
        ax.set_facecolor("#0B0F14")
        self.figure.patch.set_facecolor("#0B0F14")

        volume = np.asarray(self.volume) if self.volume is not None else None
        if volume is None or volume.ndim != 3 or volume.size == 0:
            ax.text2D(
                0.5, 0.5, "No seismic volume available for 3D slice rendering",
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=12, color="#D7E2F0",
            )
            ax.set_axis_off()
            self.canvas.draw_idle()
            return

        ni, nx, nt = volume.shape
        self.inline_index = int(np.clip(self.inline_index, 0, ni - 1))
        self.crossline_index = int(np.clip(self.crossline_index, 0, nx - 1))
        self.timeslice_index = int(np.clip(self.timeslice_index, 0, nt - 1))

        inline_attr = self._compute_attribute_slice(volume[self.inline_index, :, :])
        crossline_attr = self._compute_attribute_slice(volume[:, self.crossline_index, :])

        finite_parts = []
        for part in (inline_attr, crossline_attr):
            vals = np.asarray(part)
            vals = vals[np.isfinite(vals)]
            if vals.size:
                finite_parts.append(vals)
        if not finite_parts:
            ax.text2D(
                0.5, 0.5, "Attribute slices contain no finite values",
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=12, color="#D7E2F0",
            )
            ax.set_axis_off()
            self.canvas.draw_idle()
            return

        finite = np.concatenate(finite_parts)
        lo = float(np.percentile(finite, 2))
        hi = float(np.percentile(finite, 98))
        if not np.isfinite(lo) or not np.isfinite(hi) or np.isclose(lo, hi):
            lo = float(np.min(finite))
            hi = float(np.max(finite))
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
        inline_sub = np.clip(inline_data[::step_z, ::step_x], lo, hi)
        ax.plot_surface(
            X_inline,
            Y_inline,
            Z_inline,
            facecolors=cmap(norm(inline_sub)),
            shade=False,
            linewidth=0,
            antialiased=False,
            alpha=0.98,
        )

        crossline_data = np.asarray(crossline_attr).T
        Y_xline, Z_xline = np.meshgrid(y_sub, z_sub)
        X_xline = np.full_like(Y_xline, self.crossline_index)
        crossline_sub = np.clip(crossline_data[::step_z, ::step_y], lo, hi)
        ax.plot_surface(
            X_xline,
            Y_xline,
            Z_xline,
            facecolors=cmap(norm(crossline_sub)),
            shade=False,
            linewidth=0,
            antialiased=False,
            alpha=0.98,
        )

        z_line = z_coords[::step_z]
        ax.plot(
            np.full_like(z_line, self.crossline_index),
            np.full_like(z_line, self.inline_index),
            z_line,
            color="#00D3FF",
            linewidth=1.6,
            alpha=0.95,
        )
        x_line = x_coords[::step_x]
        ax.plot(
            x_line,
            np.full_like(x_line, self.inline_index),
            np.full_like(x_line, self.timeslice_index),
            color="#00D3FF",
            linewidth=1.0,
            alpha=0.75,
        )
        y_line = y_coords[::step_y]
        ax.plot(
            np.full_like(y_line, self.crossline_index),
            y_line,
            np.full_like(y_line, self.timeslice_index),
            color="#00D3FF",
            linewidth=1.0,
            alpha=0.75,
        )

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = self.figure.colorbar(sm, ax=ax, pad=0.08, shrink=0.7)
        cbar.set_label(self.attribute_name, fontsize=10, color="#D7E2F0")
        cbar.ax.yaxis.set_tick_params(labelsize=8, color="#B7C7D9")
        plt.setp(cbar.ax.get_yticklabels(), color="#D7E2F0")
        cbar.outline.set_edgecolor("#546375")

        ax.set_title(
            f"{self.attribute_name} — Inline {self.inline_index} / Crossline {self.crossline_index}",
            fontsize=13, fontweight="bold", color="#E7EEF7", pad=16,
        )
        ax.set_xlabel("Crossline", fontsize=10, fontweight="bold", color="#D7E2F0", labelpad=10)
        ax.set_ylabel("Inline", fontsize=10, fontweight="bold", color="#D7E2F0", labelpad=10)
        ax.set_zlabel("Time / Sample", fontsize=10, fontweight="bold", color="#D7E2F0", labelpad=10)
        ax.tick_params(axis="x", colors="#B7C7D9", labelsize=8)
        ax.tick_params(axis="y", colors="#B7C7D9", labelsize=8)
        ax.tick_params(axis="z", colors="#B7C7D9", labelsize=8)
        ax.view_init(elev=23, azim=-58)
        ax.invert_yaxis()
        ax.invert_zaxis()
        ax.grid(True, alpha=0.18)

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
    Light workstation theme — always bright background.
    Does NOT include Visual Parameters, Sample Data, or Amplitude Distribution
    (those belong to the main Viewport widget).
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
        self.current_attribute = None
        self.current_attribute_name = None
        self.current_image_matrix = None
        self.current_volume = None
        self.current_inline_index = 0
        self.current_crossline_index = 0
        self.current_timeslice_index = 0
        self.attribute_results = {}
        self.input_data        = None
        self.sample_rate_ms    = 2.0
        self.sample_axis       = 1
        self.current_section_kind = "Section"
        self.current_section_index = None
        self.current_x_label = "Trace Number"
        self.current_y_label = "Time (samples)"
        self.current_display_cmap = None
        self.current_grid_visible = True
        self.current_interpolation = "bilinear"
        self._data_signature = None
        self._default_plot_hint = "Right-click image for options / 3D slice view"
        self._three_d_dialog = None

        self.setStyleSheet(LIGHT_SS)
        self._configure_mpl()
        self._build_ui()

    # ── matplotlib light theme ────────────────────────────────────────────
    def _configure_mpl(self):
        plt.rcParams.update({
            "figure.facecolor":  "#FFFFFF",
            "axes.facecolor":    "#FAFBFC",
            "axes.edgecolor":    C["border"],
            "axes.labelcolor":   C["text_secondary"],
            "axes.titlecolor":   C["text_primary"],
            "xtick.color":       "#718096",
            "ytick.color":       "#718096",
            "text.color":        C["text_primary"],
            "grid.color":        C["divider"],
            "grid.linestyle":    "--",
            "grid.linewidth":    0.5,
            "axes.grid":         True,
            "axes.titlesize":    12,
            "axes.titleweight":  "bold",
            "axes.labelsize":    10,
            "axes.labelweight":  "bold",
        })

    # ── root layout ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)
        root.addWidget(self._build_left(),  stretch=1)
        root.addWidget(self._build_right(), stretch=4)

    # ═════════════════════════════════════════════════════════════════════
    #  LEFT PANEL
    # ═════════════════════════════════════════════════════════════════════
    def _build_left(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(280)
        w.setStyleSheet(f"background:{C['bg_app']};")

        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        hero = QFrame()
        hero.setObjectName("hero_card")
        hero_lay = QVBoxLayout(hero)
        hero_lay.setContentsMargins(16, 14, 16, 14)
        hero_lay.setSpacing(4)

        hero_eyebrow = QLabel("ATTRIBUTE STUDIO")
        hero_eyebrow.setObjectName("hero_eyebrow")
        hero_title = QLabel("Attribute Engine")
        hero_title.setObjectName("hero_title")
        hero_subtitle = QLabel(
            "Structural, spectral, and instantaneous attribute extraction "
            "for the active seismic section."
        )
        hero_subtitle.setWordWrap(True)
        hero_subtitle.setObjectName("hero_subtitle")

        hero_lay.addWidget(hero_eyebrow)
        hero_lay.addWidget(hero_title)
        hero_lay.addWidget(hero_subtitle)
        lay.addWidget(hero)

        # ── attribute selection ──
        g1 = QGroupBox("Attribute Selection")
        l1 = QVBoxLayout()
        l1.setSpacing(6)

        lbl_t = QLabel("Attribute Type")
        lbl_t.setStyleSheet(f"color:{C['text_secondary']};font-weight:600;")
        l1.addWidget(lbl_t)

        self.attr_combo = QComboBox()
        for name in self.ATTRIBUTE_ITEMS:
            tag = ATTR_META.get(name, {}).get("tag", "")
            self.attr_combo.addItem(f"{name}  [{tag}]")
        self.attr_combo.setToolTip("Select the seismic attribute to compute")
        l1.addWidget(self.attr_combo)

        l1.addWidget(Divider())

        lbl_w = QLabel("Window Size (samples)")
        lbl_w.setStyleSheet(f"color:{C['text_secondary']};font-weight:600;")
        l1.addWidget(lbl_w)

        self.window_spin = QSpinBox()
        self.window_spin.setMinimum(5)
        self.window_spin.setMaximum(101)
        self.window_spin.setValue(25)
        self.window_spin.setSingleStep(2)
        self.window_spin.setToolTip("Analysis window length in samples")
        l1.addWidget(self.window_spin)

        self.context_label = QLabel("Active section: awaiting data")
        self.context_label.setObjectName("context_label")
        self.context_label.setWordWrap(True)
        l1.addWidget(self.context_label)

        l1.addSpacing(2)
        self.btn_compute = QPushButton("  Compute Attribute")
        self.btn_compute.setObjectName("btn_compute")
        self.btn_compute.setCursor(Qt.PointingHandCursor)
        self.btn_compute.clicked.connect(self.compute_selected_attribute)
        l1.addWidget(self.btn_compute)

        g1.setLayout(l1)
        lay.addWidget(g1)

        # ── computed list ──
        g2 = QGroupBox("Computed Results")
        l2 = QVBoxLayout()
        l2.setSpacing(6)

        self.attr_list = QListWidget()
        self.attr_list.setAlternatingRowColors(True)
        self.attr_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.attr_list.setMinimumHeight(150)
        self.attr_list.setMaximumHeight(220)
        self.attr_list.itemClicked.connect(self._on_list_click)
        l2.addWidget(self.attr_list)

        self.btn_export = QPushButton("  Save Current Image")
        self.btn_export.setObjectName("btn_export")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._save_current_plot)
        l2.addWidget(self.btn_export)

        g2.setLayout(l2)
        lay.addWidget(g2)

        # ── statistics ──
        g3 = QGroupBox("Statistics")
        l3 = QVBoxLayout()
        l3.setSpacing(3)
        l3.setContentsMargins(8, 8, 8, 8)

        self._s_min  = _stat_row("Min",     l3)
        self._s_max  = _stat_row("Max",     l3)
        self._s_mean = _stat_row("Mean",    l3)
        self._s_std  = _stat_row("Std Dev", l3)
        l3.addWidget(Divider())
        self._s_p1   = _stat_row("P1",      l3)
        self._s_p99  = _stat_row("P99",     l3)

        g3.setLayout(l3)
        lay.addWidget(g3)

        lay.addStretch()
        return w

    # ═════════════════════════════════════════════════════════════════════
    #  RIGHT PANEL
    # ═════════════════════════════════════════════════════════════════════
    def _build_right(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        info_card = QFrame()
        info_card.setObjectName("info_card")
        info_lay = QVBoxLayout(info_card)
        info_lay.setContentsMargins(14, 12, 14, 12)
        info_lay.setSpacing(3)

        info_title = QLabel("Attribute Preview")
        info_title.setStyleSheet(
            f"color:{C['text_primary']};font-size:14px;font-weight:700;"
        )
        info_subtitle = QLabel(
            "Inline and crossline attributes render here. Right-click the image for plot actions."
        )
        info_subtitle.setObjectName("context_label")
        info_subtitle.setWordWrap(True)
        info_lay.addWidget(info_title)
        info_lay.addWidget(info_subtitle)
        lay.addWidget(info_card)

        plot_card = QFrame()
        plot_card.setObjectName("plot_card")
        plot_lay = QVBoxLayout(plot_card)
        plot_lay.setContentsMargins(14, 12, 14, 14)
        plot_lay.setSpacing(10)

        # top toolbar row
        tb = QHBoxLayout()
        tb.setSpacing(8)

        self.status_badge = StatusBadge()
        self.status_badge.setFixedWidth(164)
        tb.addWidget(self.status_badge)

        self.title_label = QLabel("No attribute selected")
        self.title_label.setStyleSheet(
            f"color:{C['text_primary']};font-size:13px;font-weight:700;"
        )
        tb.addWidget(self.title_label)
        tb.addStretch()

        self.plot_hint = QLabel(self._default_plot_hint)
        self.plot_hint.setObjectName("plot_hint")
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
                padding: 2px 8px;
            }}
        """)
        tb.addWidget(self.cmap_chip)

        plot_lay.addLayout(tb)

        # progress bar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        plot_lay.addWidget(self.progress)

        # matplotlib canvas
        self.figure = Figure(figsize=(11.5, 7.2), facecolor="#FFFFFF")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumHeight(520)
        self.canvas.setCursor(Qt.CrossCursor)
        self.canvas.setToolTip(
            "Right-click the rendered attribute image for save, copy, colormap, display, and 3D slice options."
        )
        self.canvas.setStyleSheet(
            f"background:#FFFFFF; border:1px solid {C['border']}; border-radius:8px;"
        )
        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)
        plot_lay.addWidget(self.canvas, 1)

        self.ax = self.figure.add_subplot(111)
        self._show_empty_plot()
        lay.addWidget(plot_card, 1)
        return w

    # ─────────────────────────────────────────────────────────────────────
    #  Empty placeholder
    # ─────────────────────────────────────────────────────────────────────
    def _show_empty_plot(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#FAFBFC")
        self.figure.patch.set_facecolor("#FFFFFF")
        self.current_attribute = None
        self.current_attribute_name = None
        self.current_image_matrix = None
        for sp in self.ax.spines.values():
            sp.set_edgecolor(C["border"])
            sp.set_linewidth(0.8)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.grid(False)
        self.ax.text(0.5, 0.57, "Seismic Attribute Workstation",
                     ha="center", va="center", fontsize=16,
                     color="#7F93A8", fontweight="bold",
                     transform=self.ax.transAxes)
        section_desc = self._section_descriptor()
        self.ax.text(0.5, 0.44,
                     f"{section_desc}: select an attribute type and press Compute Attribute",
                     ha="center", va="center", fontsize=10,
                     color="#8FA0B2", transform=self.ax.transAxes)
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
        self.input_data  = data
        self.sample_axis = 1 if sample_axis == 1 else 0
        if sample_rate_ms is not None:
            self.sample_rate_ms = float(sample_rate_ms)
        self.current_volume = np.asarray(volume) if volume is not None else None
        self.current_inline_index = int(inline_index or 0)
        self.current_crossline_index = int(crossline_index or 0)
        self.current_timeslice_index = int(timeslice_index or 0)

        prev_signature = self._data_signature
        self.current_section_kind = section_kind
        self.current_section_index = section_index
        self.current_x_label = horizontal_label
        self.current_y_label = vertical_label
        self._data_signature = (
            section_kind,
            section_index,
            tuple(np.shape(data)),
            round(self.sample_rate_ms, 6),
        )

        shape = " x ".join(str(v) for v in np.shape(data)) if data is not None else "n/a"
        section_desc = self._section_descriptor()
        self.context_label.setText(
            f"Active section: {section_desc} | {shape} | sample rate {self.sample_rate_ms:.2f} ms"
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
        self.current_attribute = None
        self.current_attribute_name = None
        self.current_image_matrix = None
        self.cmap_chip.setVisible(False)
        self.title_label.setText(f"{self._section_descriptor()} ready")
        self.title_label.setStyleSheet(
            f"color:{C['text_primary']};font-size:13px;font-weight:700;"
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
            QMessageBox.warning(self, "No Data Loaded",
                                "No seismic section is loaded.\n"
                                "Please open a SEG-Y file first.")
            return
        self.compute_attribute(name, self.input_data,
                               sample_rate_ms=self.sample_rate_ms,
                               sample_axis=self.sample_axis)

    def compute_attribute(self, attribute_name, data,
                          sample_rate_ms=None, sample_axis=1):
        if data is None:
            QMessageBox.warning(self, "No Data", "No seismic data available.")
            return

        self.input_data  = data
        self.sample_axis = 1 if sample_axis == 1 else 0
        if sample_rate_ms is not None:
            self.sample_rate_ms = float(sample_rate_ms)

        attribute_name = self._canonical(attribute_name)

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.btn_compute.setEnabled(False)
        self.status_badge.set_state("working")
        self.title_label.setText(f"Computing {attribute_name}…")
        self.cmap_chip.setVisible(False)

        self._thread = AttributeComputeThread(
            data, attribute_name,
            window_size=self.window_spin.value(),
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
        self.current_attribute = np.asarray(data)
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
        data = self.current_attribute
        attribute_name = self.current_attribute_name

        arr = np.asarray(data)
        p01 = float(np.nanpercentile(arr, 1))
        p99 = float(np.nanpercentile(arr, 99))
        if not np.isfinite(p01) or not np.isfinite(p99):
            p01, p99 = 0.0, 1.0

        meta       = ATTR_META.get(attribute_name, {})
        default_cmap = meta.get("cmap", "viridis")
        cmap       = self.current_display_cmap or default_cmap
        attr_color = meta.get("color", C["accent"])
        display = arr.T
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
            vmin, vmax = max(0.0, p01) if p01 >= 0 else p01, p99

        im = self.ax.imshow(
            display,
            aspect="auto",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            interpolation=self.current_interpolation,
            origin="upper",
        )

        cbar = self.figure.colorbar(im, ax=self.ax,
                                    pad=0.012, fraction=0.022, shrink=0.94)
        cbar.ax.yaxis.set_tick_params(labelsize=8, color="#718096")
        cbar.outline.set_edgecolor(C["border"])
        cbar.outline.set_linewidth(0.8)
        cbar.set_label(attribute_name, fontsize=9, fontweight="bold",
                       color=C["text_secondary"], labelpad=8)
        plt.setp(cbar.ax.get_yticklabels(), color=C["text_secondary"])

        self.ax.set_title(
            f"{attribute_name}  —  {self._section_descriptor()}",
            fontsize=12, fontweight="bold", color=attr_color, pad=10,
        )
        self.ax.set_xlabel(self.current_x_label,   fontsize=10, fontweight="bold",
                           color=C["text_secondary"], labelpad=6)
        self.ax.set_ylabel(self.current_y_label, fontsize=10, fontweight="bold",
                           color=C["text_secondary"], labelpad=6)

        for sp in self.ax.spines.values():
            sp.set_edgecolor(C["border"])
            sp.set_linewidth(0.8)
        self.ax.tick_params(axis="both", labelsize=8,
                            colors="#718096", length=3, width=0.6)
        self.ax.grid(self.current_grid_visible, alpha=0.5, linestyle="--",
                     linewidth=0.4, color=C["divider"])

        self.figure.subplots_adjust(left=0.075, right=0.93, top=0.90, bottom=0.11)
        self.canvas.draw_idle()

        # update toolbar
        self.title_label.setText(attribute_name)
        self.title_label.setStyleSheet(
            f"color:{attr_color};font-size:13px;font-weight:700;"
        )
        self.cmap_chip.setText(f"cmap: {cmap}")
        self.cmap_chip.setVisible(True)
        self._set_plot_hint(self._default_plot_hint, enabled=True)
        self.status_badge.set_state("ok", f"✔  {attribute_name}")
        self._update_stats(arr)

    def _set_plot_hint(self, text: str, enabled: bool = True):
        if not hasattr(self, "plot_hint"):
            return
        fg = C["accent"] if enabled else C["text_muted"]
        bg = C["accent_light"] if enabled else "#F3F5F8"
        bd = "#C6D9EE" if enabled else C["divider"]
        self.plot_hint.setText(text)
        self.plot_hint.setStyleSheet(
            f"background-color:{bg};"
            f"color:{fg};"
            f"border:1px solid {bd};"
            "border-radius:12px;"
            "font-size:10px;"
            "font-weight:700;"
            "padding:4px 10px;"
        )

    def _on_canvas_click(self, event):
        if event.inaxes != self.ax or self.current_attribute is None:
            return
        button = str(getattr(event.button, "name", event.button)).lower()
        if button in {"3", "right", "mousebutton.right"}:
            self._show_plot_context_menu(event)
            return
        if button in {"1", "left", "mousebutton.left"}:
            self._show_cursor_sample(event)

    def _show_cursor_sample(self, event):
        if self.current_image_matrix is None:
            return
        if event.xdata is None or event.ydata is None:
            return

        x_idx = int(round(event.xdata))
        y_idx = int(round(event.ydata))
        if y_idx < 0 or x_idx < 0:
            return
        if y_idx >= self.current_image_matrix.shape[0] or x_idx >= self.current_image_matrix.shape[1]:
            return

        value = float(self.current_image_matrix[y_idx, x_idx])
        self._set_plot_hint(
            f"{self.current_x_label}: {x_idx} | {self.current_y_label}: {y_idx} | value: {value:.5g}",
            enabled=True,
        )

    def _show_plot_context_menu(self, event):
        if self.current_attribute is None:
            return

        menu = QMenu(self)
        save_act = menu.addAction("Save Image As…")
        copy_act = menu.addAction("Copy Image to Clipboard")
        view_3d_act = menu.addAction("Open 3D Inline / Crossline View")
        menu.addSeparator()

        restore_act = menu.addAction("Restore Default Display")
        grid_act = menu.addAction("Show Grid")
        grid_act.setCheckable(True)
        grid_act.setChecked(self.current_grid_visible)

        interp_menu = menu.addMenu("Interpolation")
        smooth_act = interp_menu.addAction("Smooth")
        smooth_act.setCheckable(True)
        smooth_act.setChecked(self.current_interpolation == "bilinear")
        exact_act = interp_menu.addAction("Exact Samples")
        exact_act.setCheckable(True)
        exact_act.setChecked(self.current_interpolation == "nearest")

        cmap_menu = menu.addMenu("Colormap")
        cmap_actions = {}
        default_cmap = ATTR_META.get(self.current_attribute_name, {}).get("cmap", "viridis")
        using_default_cmap = self.current_display_cmap is None
        effective_cmap = self.current_display_cmap or default_cmap
        for label, cmap_name in [
            ("Attribute Default", None),
            ("Inferno", "inferno"),
            ("Seismic", "seismic"),
            ("Viridis", "viridis"),
            ("Plasma", "plasma"),
            ("Hot", "hot"),
            ("Gray", "gray"),
        ]:
            act = cmap_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(
                (cmap_name is None and using_default_cmap)
                or (cmap_name is not None and not using_default_cmap and cmap_name == effective_cmap)
            )
            cmap_actions[act] = cmap_name

        chosen = menu.exec_(self._event_global_pos(event))
        if chosen is None:
            return
        if chosen == save_act:
            self._save_current_plot()
            return
        if chosen == copy_act:
            self._copy_plot_to_clipboard()
            return
        if chosen == view_3d_act:
            self._open_3d_view()
            return
        if chosen == restore_act:
            self.current_display_cmap = None
            self.current_grid_visible = True
            self.current_interpolation = "bilinear"
            self._render_current_attribute()
            return
        if chosen == grid_act:
            self.current_grid_visible = grid_act.isChecked()
            self._render_current_attribute()
            return
        if chosen == smooth_act:
            self.current_interpolation = "bilinear"
            self._render_current_attribute()
            return
        if chosen == exact_act:
            self.current_interpolation = "nearest"
            self._render_current_attribute()
            return
        if chosen in cmap_actions:
            self.current_display_cmap = cmap_actions[chosen]
            self._render_current_attribute()

    def _event_global_pos(self, event):
        gui_event = getattr(event, "guiEvent", None)
        if gui_event is not None and hasattr(gui_event, "globalPos"):
            return gui_event.globalPos()
        x = int(getattr(event, "x", self.canvas.width() / 2))
        y = int(self.canvas.height() - getattr(event, "y", self.canvas.height() / 2))
        return self.canvas.mapToGlobal(QPoint(x, y))

    def _copy_plot_to_clipboard(self):
        pixmap = self.canvas.grab()
        QApplication.clipboard().setPixmap(pixmap)
        self._set_plot_hint("Image copied to clipboard", enabled=True)

    def _open_3d_view(self):
        if self.current_attribute is None or not self.current_attribute_name:
            return
        if self.current_volume is None or getattr(self.current_volume, "ndim", 0) != 3:
            QMessageBox.information(
                self,
                "3D Slice View",
                "A loaded seismic volume is required for the 3D inline/crossline view.",
            )
            return

        cmap_name = self.current_display_cmap or ATTR_META.get(
            self.current_attribute_name, {}
        ).get("cmap", "viridis")

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
        base_name = f"{self.current_attribute_name.lower().replace(' ', '_')}_{section_name}"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Attribute Image",
            f"{base_name}.png",
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
            for w in (self._s_min, self._s_max, self._s_mean,
                      self._s_std, self._s_p1, self._s_p99):
                w.setText("—")
            return
        f = lambda v: f"{v:.5g}"
        self._s_min.setText(f(float(np.min(finite))))
        self._s_max.setText(f(float(np.max(finite))))
        self._s_mean.setText(f(float(np.mean(finite))))
        self._s_std.setText(f(float(np.std(finite))))
        self._s_p1.setText(f(float(np.percentile(finite, 1))))
        self._s_p99.setText(f(float(np.percentile(finite, 99))))

    # ── backward-compat public aliases ───────────────────────────────────
    def show_empty_plot(self):
        self._show_empty_plot()

    def on_compute_finished(self, result, attribute_name):
        self._on_finished(result, attribute_name)

    def on_compute_error(self, error_msg):
        self._on_error(error_msg)

    def display_selected_attribute(self, item):
        self._on_list_click(item)
