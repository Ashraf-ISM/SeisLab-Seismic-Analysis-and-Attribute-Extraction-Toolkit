"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   SeismicVision Pro  –  Seismic Interpretation Platform  (Light Theme)       ║
║   Streamlined ribbon  |  Data Info popup  |  PyQt5 + Plotly WebEngine        ║
╚══════════════════════════════════════════════════════════════════════════════╝

REQUIREMENTS:
    pip install PyQt5 PyQtWebEngine plotly numpy scipy segyio psutil

USAGE:
    python seismic_vision_pro.py
    python seismic_vision_pro.py /path/to/data.segy
"""

import sys, os, json, tempfile, webbrowser, datetime
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    WEBENGINE = True
except ImportError:
    WEBENGINE = False

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY = True
except ImportError:
    PLOTLY = False

try:
    import segyio
    SEGYIO = True
except ImportError:
    SEGYIO = False

try:
    from scipy import signal as sp_signal
    from scipy.ndimage import gaussian_filter
    SCIPY = True
except ImportError:
    SCIPY = False


# ═══════════════════════════════════════════════════════════════════════
#  LIGHT THEME PALETTE
# ═══════════════════════════════════════════════════════════════════════
C = {
    # Backgrounds
    "bg_app":        "#F0F2F7",
    "bg_white":      "#FFFFFF",
    "bg_panel":      "#FAFBFD",
    "bg_toolbar":    "#FFFFFF",
    "bg_ribbon":     "#F7F9FC",
    "bg_viewport":   "#1A2235",   # dark viewport stays dark for seismic
    "bg_tree":       "#FFFFFF",
    "bg_hover":      "#E8EDFB",
    "bg_selected":   "#D0DEFF",
    "bg_header":     "#EEF2FF",
    "bg_card":       "#FFFFFF",

    # Accent
    "accent":        "#2563EB",
    "accent_light":  "#EFF6FF",
    "accent2":       "#0EA5E9",
    "accent_green":  "#16A34A",
    "accent_orange": "#EA580C",
    "accent_red":    "#DC2626",
    "accent_purple": "#7C3AED",
    "accent_gold":   "#D97706",

    # Borders
    "border":        "#E2E7F0",
    "border_med":    "#CBD5E1",
    "border_strong": "#94A3B8",

    # Text
    "text_primary":  "#0F172A",
    "text_secondary":"#475569",
    "text_dim":      "#94A3B8",
    "text_white":    "#FFFFFF",
    "text_accent":   "#2563EB",

    # Status / badge
    "badge_blue":    "#DBEAFE",
    "badge_green":   "#DCFCE7",
    "badge_orange":  "#FFEDD5",
}

QSS = f"""
/* ─── Base ──────────────────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background: {C['bg_app']};
    color: {C['text_primary']};
    font-family: 'Segoe UI', 'Calibri', Arial, sans-serif;
    font-size: 12px;
}}
QWidget#sidePanel, QWidget#rightPanel {{
    background: {C['bg_white']};
    border-right: 1px solid {C['border']};
}}

/* ─── Menu Bar ───────────────────────────────────────────────────────── */
QMenuBar {{
    background: {C['bg_toolbar']};
    color: {C['text_primary']};
    border-bottom: 1px solid {C['border']};
    padding: 0 4px;
    font-size: 12px;
}}
QMenuBar::item {{ padding: 6px 12px; border-radius: 4px; }}
QMenuBar::item:selected {{ background: {C['bg_hover']}; color: {C['accent']}; }}
QMenu {{
    background: {C['bg_white']};
    border: 1px solid {C['border_med']};
    border-radius: 8px; padding: 4px 0;
    color: {C['text_primary']};
}}
QMenu::item {{ padding: 7px 22px 7px 14px; border-radius: 4px; margin: 1px 5px; }}
QMenu::item:selected {{ background: {C['accent_light']}; color: {C['accent']}; }}
QMenu::separator {{ height:1px; background:{C['border']}; margin:3px 0; }}

/* ─── Ribbon / Tab ───────────────────────────────────────────────────── */
QTabBar#ribbonBar {{
    background: {C['bg_toolbar']};
    border-bottom: 1px solid {C['border']};
}}
QTabBar#ribbonBar::tab {{
    background: transparent;
    color: {C['text_secondary']};
    border: none;
    padding: 8px 18px; font-size: 12px;
    border-bottom: 3px solid transparent;
    margin-bottom: -1px;
}}
QTabBar#ribbonBar::tab:selected {{
    color: {C['accent']};
    font-weight: 700;
    border-bottom: 3px solid {C['accent']};
}}
QTabBar#ribbonBar::tab:hover:!selected {{
    background: {C['bg_hover']};
    color: {C['text_primary']};
    border-radius: 4px 4px 0 0;
}}

/* ─── Ribbon content ─────────────────────────────────────────────────── */
QWidget#ribbonContent {{
    background: {C['bg_ribbon']};
    border-bottom: 1px solid {C['border']};
}}
QToolButton {{
    background: transparent; border: none;
    border-radius: 5px; padding: 4px 8px;
    color: {C['text_primary']}; font-size: 11px;
    min-width: 36px;
}}
QToolButton:hover  {{ background: {C['bg_hover']}; color: {C['accent']}; }}
QToolButton:pressed{{ background: {C['bg_selected']}; }}
QToolButton:checked{{
    background: {C['accent_light']};
    color: {C['accent']};
    border: 1px solid {C['accent']};
    border-radius: 4px;
}}

/* ─── Viewport tab bar ───────────────────────────────────────────────── */
QTabBar#vpBar::tab {{
    background: {C['bg_app']};
    color: {C['text_dim']};
    border: 1px solid {C['border']};
    border-bottom: none;
    padding: 5px 14px; font-size: 11px;
    border-radius: 5px 5px 0 0;
    margin-right: 2px;
}}
QTabBar#vpBar::tab:selected {{
    background: {C['bg_white']};
    color: {C['text_primary']};
    font-weight: 600;
    border-color: {C['border_med']};
}}
QTabBar#vpBar::tab:hover:!selected {{ background: {C['bg_hover']}; }}
QTabWidget#vpTabs::pane {{
    border: 1px solid {C['border_med']};
    border-top: none;
    background: {C['bg_viewport']};
    border-radius: 0 0 6px 6px;
}}

/* ─── Panel tabs ─────────────────────────────────────────────────────── */
QTabBar#panelBar::tab {{
    background: transparent;
    color: {C['text_dim']};
    border: none;
    padding: 6px 14px; font-size: 11px;
    border-bottom: 2px solid transparent;
    margin: 0;
}}
QTabBar#panelBar::tab:selected {{
    color: {C['accent']};
    font-weight: 700;
    border-bottom: 2px solid {C['accent']};
}}
QTabBar#panelBar::tab:hover:!selected {{ color:{C['text_primary']}; }}
QTabWidget#panelTabs::pane {{
    border: none;
    background: {C['bg_white']};
}}

/* ─── Tree ───────────────────────────────────────────────────────────── */
QTreeWidget {{
    background: {C['bg_tree']};
    color: {C['text_primary']};
    border: none; outline: none;
    font-size: 12px;
    show-decoration-selected: 1;
}}
QTreeWidget::item {{ padding: 3px 6px; border-radius: 4px; }}
QTreeWidget::item:hover    {{ background: {C['bg_hover']}; }}
QTreeWidget::item:selected {{ background: {C['bg_selected']}; color: {C['accent']}; }}

/* ─── Dock ───────────────────────────────────────────────────────────── */
QDockWidget {{
    color: {C['text_secondary']};
    font-weight: 700; font-size: 10px;
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: {C['bg_header']};
    padding: 6px 10px;
    border-bottom: 1px solid {C['border']};
    color: {C['accent']};
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}
QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent; border: none; padding: 2px;
    subcontrol-position: top right; subcontrol-origin: margin;
}}
QDockWidget::close-button:hover {{ background: {C['accent_red']}; border-radius:2px; }}

/* ─── Splitter ───────────────────────────────────────────────────────── */
QSplitter::handle {{ background: {C['border']}; }}
QSplitter::handle:horizontal {{ width: 2px; }}
QSplitter::handle:vertical   {{ height: 2px; }}
QSplitter::handle:hover      {{ background: {C['accent']}; }}

/* ─── Scroll bars ────────────────────────────────────────────────────── */
QScrollBar:vertical   {{ width:6px;  background:transparent; }}
QScrollBar:horizontal {{ height:6px; background:transparent; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background:{C['border_med']}; border-radius:3px; min-height:20px; min-width:20px;
}}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background:{C['border_strong']};
}}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}

/* ─── Inputs ─────────────────────────────────────────────────────────── */
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{
    background: {C['bg_white']};
    border: 1px solid {C['border_med']};
    border-radius: 5px; padding: 5px 8px;
    color: {C['text_primary']}; font-size: 12px;
    min-height: 26px;
    selection-background-color: {C['accent_light']};
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{
    border-color: {C['accent']};
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    border: none; background: transparent; width:18px;
}}
QComboBox::drop-down {{ border:none; width:20px; }}
QComboBox QAbstractItemView {{
    background: {C['bg_white']}; border: 1px solid {C['border_med']};
    border-radius: 6px; padding: 2px;
    selection-background-color: {C['accent_light']};
    selection-color: {C['accent']};
}}

/* ─── Buttons ────────────────────────────────────────────────────────── */
QPushButton {{
    background: {C['bg_white']};
    color: {C['text_primary']};
    border: 1px solid {C['border_med']};
    border-radius: 6px; padding: 6px 16px;
    font-size: 12px; font-weight: 600;
    min-height: 28px;
}}
QPushButton:hover  {{ background: {C['bg_hover']}; border-color:{C['accent']}; color:{C['accent']}; }}
QPushButton:pressed{{ background: {C['bg_selected']}; }}
QPushButton[primary="true"] {{
    background: {C['accent']};
    color: #FFF; border: none;
}}
QPushButton[primary="true"]:hover {{ background: #1D4ED8; }}
QPushButton[primary="true"]:pressed {{ background: #1E40AF; }}
QPushButton[secondary="true"] {{
    background: {C['bg_white']};
    color: {C['accent']};
    border: 1.5px solid {C['accent']};
}}
QPushButton[secondary="true"]:hover {{ background: {C['accent_light']}; }}

/* ─── Sliders ────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height:3px; background:{C['border_med']}; border-radius:2px;
}}
QSlider::handle:horizontal {{
    background:{C['accent']}; border:2px solid {C['bg_white']};
    width:14px; height:14px; border-radius:7px; margin:-5px 0;
    box-shadow: 0 1px 3px rgba(37,99,235,0.4);
}}
QSlider::sub-page:horizontal {{ background:{C['accent']}; border-radius:2px; }}

/* ─── CheckBox ───────────────────────────────────────────────────────── */
QCheckBox {{ spacing:7px; color:{C['text_primary']}; font-size:12px; }}
QCheckBox::indicator {{
    width:15px; height:15px;
    border:1.5px solid {C['border_med']};
    border-radius:3px; background:{C['bg_white']};
}}
QCheckBox::indicator:checked {{
    background:{C['accent']}; border-color:{C['accent']};
}}

/* ─── Group Box ──────────────────────────────────────────────────────── */
QGroupBox {{
    background: transparent;
    border: 1px solid {C['border']};
    border-radius: 7px;
    margin-top: 16px; padding: 12px 8px 8px 8px;
    font-size: 10px; font-weight: 700;
    color: {C['text_secondary']};
    letter-spacing: 0.6px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 10px; top: -1px;
    padding: 1px 8px;
    background: {C['bg_white']};
    border-radius: 3px;
    color: {C['accent']};
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

/* ─── Progress Bar ───────────────────────────────────────────────────── */
QProgressBar {{
    background: {C['border']};
    border-radius: 3px; height: 5px; font-size: 0;
}}
QProgressBar::chunk {{ background: {C['accent']}; border-radius: 3px; }}

/* ─── Status Bar ─────────────────────────────────────────────────────── */
QStatusBar {{
    background: {C['bg_toolbar']};
    border-top: 1px solid {C['border']};
    color: {C['text_secondary']};
    font-size: 11px; padding: 0 10px;
}}
QStatusBar::item {{ border: none; }}

/* ─── Table ──────────────────────────────────────────────────────────── */
QTableWidget {{
    background: {C['bg_white']};
    gridline-color: {C['border']};
    border: none; font-size: 11px;
    selection-background-color: {C['accent_light']};
    selection-color: {C['accent']};
    alternate-background-color: {C['bg_panel']};
}}
QTableWidget::item {{ padding: 5px 8px; }}
QHeaderView::section {{
    background: {C['bg_header']};
    color: {C['text_secondary']};
    border: none;
    border-right: 1px solid {C['border']};
    border-bottom: 2px solid {C['border_med']};
    padding: 6px 8px;
    font-weight: 700; font-size: 11px;
}}

/* ─── Frame / Cards ──────────────────────────────────────────────────── */
QFrame#card {{
    background: {C['bg_white']};
    border: 1px solid {C['border']};
    border-radius: 8px;
}}
QFrame#infoBar {{
    background: {C['bg_header']};
    border-bottom: 1px solid {C['border']};
}}
QFrame#sectionSep {{
    background: {C['border']};
}}

/* ─── Dialog specific ────────────────────────────────────────────────── */
QDialog {{
    background: {C['bg_app']};
}}
QDialog QWidget {{
    background: {C['bg_app']};
}}
"""


# ═══════════════════════════════════════════════════════════════════════
#  DATA MODEL
# ═══════════════════════════════════════════════════════════════════════
class SeismicCube:
    def __init__(self):
        self.cube: np.ndarray | None = None
        self.filename = ""; self.filepath = ""
        self.n_inline = 0; self.n_crossline = 0; self.n_time = 0
        self.sample_rate_ms = 2.0
        self.file_headers: dict = {}
        self.trace_headers: list = []
        self.binary_header: dict = {}
        self.loaded_at: str = ""

    @property
    def duration_ms(self): return self.n_time * self.sample_rate_ms

    def clip_val(self, pct=98.0):
        return float(np.nanpercentile(np.abs(self.cube), pct))

    def full_stats(self) -> dict:
        d = self.cube.ravel()
        return {
            "Survey File"       : self.filename,
            "File Path"         : self.filepath or "Synthetic (demo)",
            "Loaded At"         : self.loaded_at,
            "Inlines"           : self.n_inline,
            "Crosslines"        : self.n_crossline,
            "Time Samples"      : self.n_time,
            "Sample Rate (ms)"  : f"{self.sample_rate_ms:.4f}",
            "Duration (ms)"     : f"{self.duration_ms:.1f}",
            "Total Traces"      : self.n_inline * self.n_crossline,
            "Total Samples"     : int(d.size),
            "Data Type"         : str(d.dtype),
            "Min Amplitude"     : f"{float(d.min()):.6f}",
            "Max Amplitude"     : f"{float(d.max()):.6f}",
            "Mean"              : f"{float(d.mean()):.8f}",
            "Std Deviation"     : f"{float(d.std()):.6f}",
            "RMS Amplitude"     : f"{float(np.sqrt(np.mean(d**2))):.6f}",
            "P1 / P99"          : f"{float(np.percentile(d,1)):.4f}  /  {float(np.percentile(d,99)):.4f}",
            "P5 / P95"          : f"{float(np.percentile(d,5)):.4f}  /  {float(np.percentile(d,95)):.4f}",
            "Median"            : f"{float(np.median(d)):.6f}",
            "Dynamic Range (dB)": f"{20*np.log10(float(d.max())/max(abs(float(d.min())),1e-12)+1e-12):.1f}",
        }


def make_demo_cube(ni=130, nx=130, nt=150, sr=2.0) -> SeismicCube:
    cube = SeismicCube()
    cube.filename = "Synthetic_Survey_3D.segy"
    cube.n_inline = ni; cube.n_crossline = nx
    cube.n_time   = nt; cube.sample_rate_ms = sr
    cube.loaded_at = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    rng = np.random.default_rng(42)
    t   = np.arange(nt) * sr
    raw = np.zeros((ni, nx, nt), np.float32)
    for t0, amp in [(80, 1.0), (170, -0.75), (260, 0.55), (340, 0.35)]:
        sigma = 18.0
        for ii in range(ni):
            for ix in range(nx):
                dip = 0.5*(ii-ni/2) + 0.25*(ix-nx/2)
                tc  = t0 + dip
                w   = amp * np.exp(-((t-tc)**2)/(2*sigma**2))
                w  *= np.cos(2*np.pi*28*(t-tc)/1000)
                raw[ii, ix] += w.astype(np.float32)
    raw += rng.normal(0, 0.04, raw.shape).astype(np.float32)
    cube.cube = raw
    cube.file_headers = {
        "Survey Name"   : "Synthetic_Survey_3D",
        "Inlines"       : ni, "Crosslines": nx, "Time Samples": nt,
        "Sample Rate"   : f"{sr} ms", "Duration": f"{nt*sr:.0f} ms",
        "Format"        : "IEEE Float 32-bit", "CRS": "WGS84 / UTM Zone 31N",
        "Acquisition"   : "Marine 3D", "Source": "Air-gun Array",
    }
    cube.binary_header = {
        "Job ID"              : 1001,
        "Line Number"         : 100,
        "Reel Number"         : 1,
        "Traces per Ensemble" : ni,
        "Samples per Trace"   : nt,
        "Sample Interval (µs)": int(sr * 1000),
        "Data Format"         : 1,
        "Ensemble Fold"       : 60,
        "Measurement System"  : "Metric",
    }
    cube.trace_headers = [
        {"Trace #": i+1, "CDP": i+1, "Offset": 0,
         "Inline": i // nx + 1, "Crossline": i % nx + 1,
         "ShotX": (i // nx) * 25, "ShotY": (i % nx) * 25,
         "ScalarElev": -100, "WaterDepth": 200}
        for i in range(min(500, ni*nx))
    ]
    return cube


def _ibm_float(ibm):
    sign = (ibm >> 31) & 1; exp = ((ibm >> 24) & 0x7F) - 64
    mant = (ibm & 0xFFFFFF).astype(np.float64) / 0x1000000
    val  = mant * np.power(16.0, exp.astype(np.float64))
    val[sign == 1] *= -1
    return val.astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════
#  LOADER THREAD
# ═══════════════════════════════════════════════════════════════════════
class CubeLoader(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__(); self.filepath = filepath

    def run(self):
        try:
            cube = SeismicCube()
            cube.filename  = os.path.basename(self.filepath)
            cube.filepath  = self.filepath
            cube.loaded_at = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            self.progress.emit(10, "Opening SEG-Y…")
            SEGYIO and self._segyio(cube) or self._raw(cube)
            self.progress.emit(100, "Loaded")
            self.finished.emit(cube)
        except Exception as e:
            self.error.emit(str(e))

    def _segyio(self, cube):
        with segyio.open(self.filepath, ignore_geometry=True) as f:
            cube.sample_rate_ms = segyio.dt(f) / 1000.0
            nt = f.samples.size; n_tr = f.tracecount
            cube.binary_header = {
                "Sample Interval (µs)": f.bin[segyio.BinField.Interval],
                "Samples per Trace"   : f.bin[segyio.BinField.Samples],
                "Data Format Code"    : f.bin[segyio.BinField.Format],
                "Total Traces"        : n_tr,
                "Measurement System"  : "Metric" if f.bin.get(segyio.BinField.MeasurementSystem,1)==1 else "Imperial",
            }
            self.progress.emit(40, f"Loading {n_tr} traces…")
            traces = f.trace.raw[:]
            try:
                il = f.attributes(segyio.TraceField.INLINE_3D)[:]
                xl = f.attributes(segyio.TraceField.CROSSLINE_3D)[:]
                ui, ux = np.unique(il), np.unique(xl)
                ni, nx = len(ui), len(ux)
                if ni * nx == n_tr:
                    cube.cube = traces.reshape(ni, nx, nt).astype(np.float32)
                    cube.n_inline = ni; cube.n_crossline = nx; cube.n_time = nt
                    self.progress.emit(80, "Geometry resolved (3D)")
                    self._read_trace_hdrs(f, cube); return
            except Exception:
                pass
            ni = int(np.sqrt(n_tr)); nx = n_tr // ni; traces = traces[:ni*nx]
            cube.cube = traces.reshape(ni, nx, nt).astype(np.float32)
            cube.n_inline = ni; cube.n_crossline = nx; cube.n_time = nt
            self._read_trace_hdrs(f, cube)

    def _read_trace_hdrs(self, f, cube):
        self.progress.emit(85, "Reading trace headers…")
        hdrs = []
        for i, h in enumerate(f.header):
            if i >= 500: break
            hdrs.append({
                "Trace #"   : i+1,
                "CDP"       : h[segyio.TraceField.CDP],
                "Inline"    : h[segyio.TraceField.INLINE_3D],
                "Crossline" : h[segyio.TraceField.CROSSLINE_3D],
                "Offset"    : h[segyio.TraceField.offset],
                "ShotX"     : h[segyio.TraceField.SourceX],
                "ShotY"     : h[segyio.TraceField.SourceY],
                "ScalarElev": h[segyio.TraceField.ElevationScalar],
            })
        cube.trace_headers = hdrs

    def _raw(self, cube):
        with open(self.filepath, 'rb') as f:
            f.seek(3200); bh = np.frombuffer(f.read(400), dtype='>i2')
            ns = max(1, int(bh[10])); sr = max(1, int(bh[9]))
            cube.sample_rate_ms = sr / 1000.0
            f.seek(0, 2); fsize = f.tell()
            tsz = 240 + ns * 4; nt = max(1, (fsize - 3600) // tsz)
            f.seek(3600); tr_list = []
            for i in range(nt):
                f.seek(240, 1); buf = f.read(ns * 4)
                if len(buf) < ns * 4: break
                tr_list.append(_ibm_float(np.frombuffer(buf, dtype='>u4')))
            arr = np.vstack(tr_list).astype(np.float32) if tr_list else np.zeros((10,10,ns), np.float32)
            ni = int(np.sqrt(len(arr))); nx = len(arr) // ni; arr = arr[:ni*nx]
            cube.cube = arr.reshape(ni, nx, ns)
            cube.n_inline = ni; cube.n_crossline = nx; cube.n_time = ns


# ═══════════════════════════════════════════════════════════════════════
#  PLOTLY HTML BUILDERS
# ═══════════════════════════════════════════════════════════════════════
COLORSCALES = ["RdBu_r","Greys","seismic","Viridis","Plasma","Jet","Hot","Turbo","Picnic","Electric","Balance"]

def build_3d_html(cube, il_idx, xl_idx, t_idx,
                  clip_pct=98, cs="RdBu_r", show_il=True,
                  show_xl=True, show_t=True, opacity=1.0, ds=1) -> str:
    d = cube.cube
    if ds > 1: d = d[::ds, ::ds, ::ds]
    ni, nx, nt = d.shape
    il = min(il_idx, ni-1); xl = min(xl_idx, nx-1); tl = min(t_idx, nt-1)
    vmax = float(np.nanpercentile(np.abs(d), clip_pct)); vmin = -vmax
    sr = cube.sample_rate_ms * ds
    t_ax = np.arange(nt) * sr
    traces = []

    if show_il:
        sl = d[il, :, :].T
        X, Z = np.meshgrid(np.arange(nx), t_ax)
        Y = np.full_like(X, il, dtype=float)
        traces.append(go.Surface(
            x=X, y=Y, z=Z, surfacecolor=sl,
            colorscale=cs, cmin=vmin, cmax=vmax,
            opacity=opacity, showscale=True,
            colorbar=dict(
                title=dict(text="Amplitude", side="right",
                           font=dict(color="#94A3B8", size=11)),
                thickness=12, len=0.55, x=1.01,
                tickfont=dict(size=9, color="#94A3B8"),
                bgcolor="rgba(15,23,42,0.8)",
                bordercolor="#334155", borderwidth=1,
            ),
            name=f"Inline {il}",
            hovertemplate="XL: %{x:.0f}<br>IL: %{y:.0f}<br>T: %{z:.0f} ms<br>Amp: %{surfacecolor:.2f}<extra>Inline</extra>",
            lighting=dict(ambient=0.85, diffuse=0.4, specular=0.05),
        ))
    if show_xl:
        sl = d[:, xl, :].T
        Y2, Z2 = np.meshgrid(np.arange(ni), t_ax)
        X2 = np.full_like(Y2, xl, dtype=float)
        traces.append(go.Surface(
            x=X2, y=Y2, z=Z2, surfacecolor=sl,
            colorscale=cs, cmin=vmin, cmax=vmax,
            opacity=opacity, showscale=False,
            name=f"XLine {xl}",
            hovertemplate="XL: %{x:.0f}<br>IL: %{y:.0f}<br>T: %{z:.0f} ms<br>Amp: %{surfacecolor:.2f}<extra>Crossline</extra>",
            lighting=dict(ambient=0.85, diffuse=0.4, specular=0.05),
        ))
    if show_t:
        sl = d[:, :, tl]
        X3, Y3 = np.meshgrid(np.arange(nx), np.arange(ni))
        Z3 = np.full_like(X3, t_ax[tl], dtype=float)
        traces.append(go.Surface(
            x=X3, y=Y3, z=Z3, surfacecolor=sl,
            colorscale=cs, cmin=vmin, cmax=vmax,
            opacity=opacity, showscale=False,
            name=f"T={t_ax[tl]:.0f}ms",
            hovertemplate="XL: %{x:.0f}<br>IL: %{y:.0f}<br>T: %{z:.0f} ms<br>Amp: %{surfacecolor:.2f}<extra>Time Slice</extra>",
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(
            text=f"<span style='font-family:Segoe UI;font-size:13px;font-weight:600;"
                 f"color:#94A3B8'>3D Seismic  ·  {cube.filename}</span>",
            x=0.02, y=0.97,
        ),
        scene=dict(
            xaxis=dict(title="Crossline", titlefont=dict(color="#64748B",size=11),
                       tickfont=dict(color="#475569",size=8),
                       backgroundcolor="rgba(13,21,35,0.97)",
                       gridcolor="#1E2A3A", showbackground=True, linecolor="#1E3050"),
            yaxis=dict(title="Inline",    titlefont=dict(color="#64748B",size=11),
                       tickfont=dict(color="#475569",size=8),
                       backgroundcolor="rgba(10,18,32,0.97)",
                       gridcolor="#1E2A3A", showbackground=True, linecolor="#1E3050"),
            zaxis=dict(title="Time (ms)", titlefont=dict(color="#64748B",size=11),
                       tickfont=dict(color="#475569",size=8),
                       backgroundcolor="rgba(8,16,28,0.97)",
                       gridcolor="#1A2638", showbackground=True,
                       autorange="reversed", linecolor="#1E3050"),
            aspectratio=dict(x=1, y=1, z=1.35),
            camera=dict(eye=dict(x=1.55, y=-1.55, z=1.0), up=dict(x=0,y=0,z=1)),
            bgcolor="rgba(10,16,28,1.0)",
            dragmode="turntable",
        ),
        paper_bgcolor="#0F1828",
        margin=dict(l=0, r=65, t=32, b=0),
        legend=dict(bgcolor="rgba(15,24,40,0.85)", bordercolor="#334155",
                    borderwidth=1, font=dict(size=11, color="#94A3B8"),
                    x=0.01, y=0.97),
        hoverlabel=dict(bgcolor="#1E293B", font_color="#E2E8F0",
                        font_size=11, bordercolor="#2563EB",
                        font_family="Segoe UI"),
        modebar=dict(bgcolor="rgba(15,24,40,0.7)", color="#64748B",
                     activecolor="#2563EB"),
        font=dict(family="Segoe UI, Arial", color="#94A3B8"),
    )
    return pio.to_html(fig, full_html=True, include_plotlyjs=True,
                       config={"scrollZoom":True,"displayModeBar":True,
                               "displaylogo":False,
                               "toImageButtonOptions":{"format":"png","width":1920,
                                   "height":1080,"filename":"seismic_3d"}})


def build_2d_html(cube, mode="inline", idx=0, cs="RdBu_r", clip=98) -> str:
    d = cube.cube; sr = cube.sample_rate_ms
    if mode=="inline":
        sl = d[min(idx,d.shape[0]-1),:,:].T; xtit="Crossline"
        title = f"Inline {idx}"
    elif mode=="crossline":
        sl = d[:,min(idx,d.shape[1]-1),:].T; xtit="Inline"
        title = f"Crossline {idx}"
    else:
        sl = d[:,:,min(idx,d.shape[2]-1)].T; xtit="Crossline"
        title = f"Time Slice – {idx*sr:.0f} ms"
    ytit="Time (ms)" if mode!="time" else "Inline"
    vmax = float(np.nanpercentile(np.abs(sl), clip))
    t_ax = np.arange(sl.shape[0])*sr if mode!="time" else np.arange(sl.shape[0])
    fig = go.Figure()
    fig.add_heatmap(z=sl, y=t_ax if mode!="time" else None,
                    colorscale=cs, zmin=-vmax, zmax=vmax,
                    colorbar=dict(title=dict(text="Amplitude",side="right",
                                  font=dict(color="#94A3B8")),
                                  thickness=11, tickfont=dict(size=8,color="#94A3B8"),
                                  bgcolor="rgba(10,18,30,0.7)",
                                  bordercolor="#334155"),
                    hovertemplate=f"{xtit}:%{{x}}<br>{ytit}:%{{y:.1f}}<br>Amp:%{{z:.3f}}<extra></extra>")
    fig.update_layout(
        title=dict(text=f"<b style='font-size:13px;color:#94A3B8'>{title}</b>", x=0.02),
        yaxis=dict(title=ytit, autorange="reversed" if mode!="time" else True,
                   tickfont=dict(size=9,color="#64748B"), titlefont=dict(size=11,color="#64748B"),
                   gridcolor="#1E2A3A", linecolor="#1E3050"),
        xaxis=dict(title=xtit,
                   tickfont=dict(size=9,color="#64748B"), titlefont=dict(size=11,color="#64748B"),
                   gridcolor="#1E2A3A", linecolor="#1E3050"),
        paper_bgcolor="#0F1828", plot_bgcolor="#08101C",
        margin=dict(l=60,r=70,t=44,b=44),
        font=dict(family="Segoe UI",color="#94A3B8"),
        hoverlabel=dict(bgcolor="#1E293B",font_color="#E2E8F0",
                        font_size=11,bordercolor="#2563EB"),
    )
    return pio.to_html(fig, full_html=True, include_plotlyjs=True,
                       config={"scrollZoom":True,"displayModeBar":True,"displaylogo":False,
                               "toImageButtonOptions":{"format":"png","width":1600,
                                   "height":800,"filename":"seismic_2d"}})


# ═══════════════════════════════════════════════════════════════════════
#  PLOTLY VIEW WIDGET
# ═══════════════════════════════════════════════════════════════════════
class PlotlyView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0)
        self._tmp = None; self._html = ""
        if WEBENGINE:
            self.view = QWebEngineView()
            self.view.settings().setAttribute(
                QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            self.view.setStyleSheet(f"background:#0F1828;")
            l.addWidget(self.view)
        else:
            lbl = QLabel("⚠  PyQtWebEngine required\npip install PyQtWebEngine\n\nPlots will open in browser.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color:{C['text_secondary']};font-size:13px;background:#0F1828;padding:40px;")
            l.addWidget(lbl); self.view = None

    def set_html(self, html: str):
        self._html = html
        if self.view:
            tmp = tempfile.NamedTemporaryFile(suffix=".html",delete=False,mode='w',encoding='utf-8')
            tmp.write(html); tmp.close()
            if self._tmp and os.path.exists(self._tmp):
                try: os.unlink(self._tmp)
                except: pass
            self._tmp = tmp.name
            self.view.load(QUrl.fromLocalFile(self._tmp))
        else:
            tmp = tempfile.NamedTemporaryFile(suffix=".html",delete=False,mode='w',encoding='utf-8')
            tmp.write(html); tmp.close(); webbrowser.open(f"file://{tmp.name}")

    def open_browser(self):
        if self._html:
            tmp = tempfile.NamedTemporaryFile(suffix=".html",delete=False,mode='w',encoding='utf-8')
            tmp.write(self._html); tmp.close(); webbrowser.open(f"file://{tmp.name}")


# ═══════════════════════════════════════════════════════════════════════
#  DATA INFO  POPUP DIALOG
# ═══════════════════════════════════════════════════════════════════════
class DataInfoDialog(QDialog):
    """Full-featured modal showing all SEG-Y metadata, trace headers, stats."""

    def __init__(self, cube: SeismicCube, parent=None):
        super().__init__(parent)
        self.cube = cube
        self.setWindowTitle(f"Data Information  –  {cube.filename}")
        self.setMinimumSize(820, 640)
        self.resize(940, 720)
        self.setStyleSheet(QSS)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header banner ────────────────────────────────────────────
        banner = QFrame()
        banner.setFixedHeight(64)
        banner.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 #EFF6FF, stop:0.6 #F0F9FF, stop:1 #F0FDF4);"
            f"border-bottom: 1px solid {C['border_med']};")
        bl = QHBoxLayout(banner); bl.setContentsMargins(20, 0, 20, 0)

        icon = QLabel("📋")
        icon.setStyleSheet("font-size:28px;background:transparent;")
        bl.addWidget(icon)
        bl.addSpacing(8)

        txt = QVBoxLayout()
        t1 = QLabel(self.cube.filename)
        t1.setStyleSheet(f"color:{C['text_primary']};font-size:15px;font-weight:700;background:transparent;")
        t2 = QLabel(f"Loaded: {self.cube.loaded_at}  ·  {self.cube.n_inline} IL × {self.cube.n_crossline} XL × {self.cube.n_time} T  ·  {self.cube.sample_rate_ms:.2f} ms/sample")
        t2.setStyleSheet(f"color:{C['text_secondary']};font-size:11px;background:transparent;")
        txt.addWidget(t1); txt.addWidget(t2)
        bl.addLayout(txt); bl.addStretch()

        # Export button
        btn_exp = QPushButton("⬇  Export CSV")
        btn_exp.setStyleSheet(
            f"QPushButton{{background:{C['accent']};color:#FFF;border:none;"
            f"border-radius:6px;padding:7px 16px;font-weight:700;}}"
            f"QPushButton:hover{{background:#1D4ED8;}}")
        btn_exp.clicked.connect(self._export_csv)
        bl.addWidget(btn_exp)
        root.addWidget(banner)

        # ── Tab widget ────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setObjectName("panelTabs")
        tabs.tabBar().setObjectName("panelBar")
        tabs.setStyleSheet(QSS)
        root.addWidget(tabs)

        # ── Tab 1: Survey Overview ────────────────────────────────────
        ov_w = QWidget(); ov_l = QVBoxLayout(ov_w)
        ov_l.setContentsMargins(16, 16, 16, 16); ov_l.setSpacing(12)

        stats = self.cube.full_stats()
        # Stat cards grid
        grid = QGridLayout(); grid.setSpacing(10)
        highlight_keys = ["Inlines","Crosslines","Time Samples","Sample Rate (ms)","Duration (ms)","RMS Amplitude"]
        for i, (k, v) in enumerate([x for x in stats.items() if x[0] in highlight_keys]):
            card = QFrame(); card.setObjectName("card")
            card.setStyleSheet(
                f"QFrame{{background:{C['bg_white']};border:1px solid {C['border']};"
                f"border-radius:10px;padding:4px;}}"
                f"QFrame:hover{{border-color:{C['accent']};background:{C['accent_light']};}}")
            cl = QVBoxLayout(card); cl.setContentsMargins(14,10,14,10); cl.setSpacing(2)
            lk = QLabel(k); lk.setStyleSheet(f"color:{C['text_dim']};font-size:10px;font-weight:600;letter-spacing:0.5px;")
            lv = QLabel(str(v)); lv.setStyleSheet(f"color:{C['accent']};font-size:18px;font-weight:700;")
            cl.addWidget(lk); cl.addWidget(lv)
            grid.addWidget(card, i // 3, i % 3)
        ov_l.addLayout(grid)

        # Full stats table
        sep = QLabel("ALL SURVEY PARAMETERS"); sep.setProperty('class','section')
        sep.setStyleSheet(f"color:{C['text_dim']};font-size:10px;font-weight:700;letter-spacing:1px;"
                          f"border-bottom:1px solid {C['border']};padding-bottom:4px;margin-top:8px;")
        ov_l.addWidget(sep)

        tbl = QTableWidget(); tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["Parameter", "Value"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.setRowCount(len(stats))
        for r, (k, v) in enumerate(stats.items()):
            ki = QTableWidgetItem(str(k))
            ki.setForeground(QColor(C['text_secondary']))
            vi = QTableWidgetItem(str(v))
            vi.setForeground(QColor(C['text_primary']))
            if k in highlight_keys:
                ki.setFont(QFont("Segoe UI", 11, QFont.Bold))
                vi.setFont(QFont("Segoe UI", 11, QFont.Bold))
                vi.setForeground(QColor(C['accent']))
            tbl.setItem(r, 0, ki); tbl.setItem(r, 1, vi)
        tbl.setFixedHeight(300)
        ov_l.addWidget(tbl)
        ov_l.addStretch()
        tabs.addTab(ov_w, "📊  Survey Overview")

        # ── Tab 2: Binary File Header ─────────────────────────────────
        bh_w = QWidget(); bh_l = QVBoxLayout(bh_w)
        bh_l.setContentsMargins(16,16,16,16); bh_l.setSpacing(8)
        lbl2 = QLabel("Binary File Header (SEG-Y Standard Fields)")
        lbl2.setStyleSheet(f"color:{C['text_primary']};font-size:13px;font-weight:700;")
        bh_l.addWidget(lbl2)
        bh_lbl = QLabel("Contains survey-wide acquisition parameters encoded in the 400-byte binary header.")
        bh_lbl.setStyleSheet(f"color:{C['text_secondary']};font-size:11px;")
        bh_l.addWidget(bh_lbl)

        bh_tbl = QTableWidget(); bh_tbl.setColumnCount(2)
        bh_tbl.setHorizontalHeaderLabels(["Field", "Value"])
        bh_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        bh_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        bh_tbl.setAlternatingRowColors(True)
        bh = {**self.cube.file_headers, **self.cube.binary_header}
        bh_tbl.setRowCount(len(bh))
        for r, (k, v) in enumerate(bh.items()):
            ki = QTableWidgetItem(str(k)); ki.setForeground(QColor(C['text_secondary']))
            vi = QTableWidgetItem(str(v)); vi.setForeground(QColor(C['text_primary']))
            bh_tbl.setItem(r, 0, ki); bh_tbl.setItem(r, 1, vi)
        bh_l.addWidget(bh_tbl)
        tabs.addTab(bh_w, "📄  Binary Header")

        # ── Tab 3: Trace Headers ──────────────────────────────────────
        th_w = QWidget(); th_l = QVBoxLayout(th_w)
        th_l.setContentsMargins(16,16,16,16); th_l.setSpacing(8)

        th_info_row = QHBoxLayout()
        lbl3 = QLabel(f"Trace Headers  (first {min(500, len(self.cube.trace_headers))} of {self.cube.n_inline * self.cube.n_crossline} traces)")
        lbl3.setStyleSheet(f"color:{C['text_primary']};font-size:13px;font-weight:700;")
        th_info_row.addWidget(lbl3); th_info_row.addStretch()
        # search
        th_search = QLineEdit(); th_search.setPlaceholderText("🔍  Filter traces…")
        th_search.setFixedWidth(200)
        th_info_row.addWidget(th_search)
        th_l.addLayout(th_info_row)

        th_tbl = QTableWidget()
        th_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        th_tbl.setAlternatingRowColors(True)
        if self.cube.trace_headers:
            cols = list(self.cube.trace_headers[0].keys())
            th_tbl.setColumnCount(len(cols))
            th_tbl.setHorizontalHeaderLabels(cols)
            th_tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            th_tbl.setRowCount(len(self.cube.trace_headers))
            for r, h in enumerate(self.cube.trace_headers):
                for c2, col in enumerate(cols):
                    it = QTableWidgetItem(str(h.get(col, "")))
                    it.setForeground(QColor(C['text_primary']))
                    th_tbl.setItem(r, c2, it)
        th_l.addWidget(th_tbl)

        def filter_traces(text):
            for row in range(th_tbl.rowCount()):
                match = any(text.lower() in (th_tbl.item(row, c) and th_tbl.item(row, c).text() or "").lower()
                            for c in range(th_tbl.columnCount()))
                th_tbl.setRowHidden(row, not match and bool(text))
        th_search.textChanged.connect(filter_traces)
        tabs.addTab(th_w, "📋  Trace Headers")

        # ── Tab 4: Amplitude Statistics ───────────────────────────────
        amp_w = QWidget(); amp_l = QVBoxLayout(amp_w)
        amp_l.setContentsMargins(16,16,16,16); amp_l.setSpacing(12)
        lbl4 = QLabel("Amplitude Statistics  &  Distribution")
        lbl4.setStyleSheet(f"color:{C['text_primary']};font-size:13px;font-weight:700;")
        amp_l.addWidget(lbl4)

        # Stats grid
        d = self.cube.cube.ravel()
        pcts = [1,5,10,25,50,75,90,95,99]
        pct_data = [(f"P{p}", f"{float(np.percentile(d,p)):.5f}") for p in pcts]
        amp_grid = QGridLayout(); amp_grid.setSpacing(6)
        for i, (k, v) in enumerate(pct_data):
            fr = QFrame()
            fr.setStyleSheet(f"background:{C['bg_white']};border:1px solid {C['border']};"
                             f"border-radius:6px;padding:2px;")
            fl = QVBoxLayout(fr); fl.setContentsMargins(10,6,10,6); fl.setSpacing(1)
            lk = QLabel(k); lk.setStyleSheet(f"color:{C['text_dim']};font-size:10px;font-weight:600;")
            lv = QLabel(v); lv.setStyleSheet(f"color:{C['text_primary']};font-size:12px;font-weight:700;")
            fl.addWidget(lk); fl.addWidget(lv)
            amp_grid.addWidget(fr, i//5, i%5)
        amp_l.addLayout(amp_grid)

        # Histogram hint
        hist_frame = QFrame()
        hist_frame.setStyleSheet(f"background:{C['bg_header']};border:1px solid {C['border_med']};"
                                  f"border-radius:8px;padding:12px;")
        hfl = QVBoxLayout(hist_frame); hfl.setContentsMargins(12,10,12,10)
        hl2 = QLabel("📈  Amplitude Histogram")
        hl2.setStyleSheet(f"color:{C['accent']};font-weight:700;font-size:12px;")
        hfl.addWidget(hl2)
        n_bins = 80
        hist_data = np.histogram(d[np.abs(d) < float(np.percentile(np.abs(d),99))], bins=n_bins)
        bar_max = max(hist_data[0]) or 1
        bar_w = QWidget(); bar_row = QHBoxLayout(bar_w)
        bar_row.setSpacing(1); bar_row.setContentsMargins(0,0,0,0)
        for count in hist_data[0]:
            bar = QFrame()
            h_px = max(2, int(60 * count / bar_max))
            col_idx = count / bar_max
            r = int(37 + (220-37)*col_idx)
            g = int(99 + (60-99)*col_idx)
            b = int(235 + (50-235)*col_idx)
            bar.setStyleSheet(f"background:rgb({r},{g},{b});border-radius:1px;")
            bar.setFixedSize(6, h_px)
            bar.setToolTip(f"Count: {count}")
            bar_row.addWidget(bar)
        hfl.addWidget(bar_w)
        amp_l.addWidget(hist_frame)
        amp_l.addStretch()
        tabs.addTab(amp_w, "📉  Amplitude Statistics")

        # ── Bottom close button ───────────────────────────────────────
        btm = QFrame()
        btm.setStyleSheet(f"background:{C['bg_app']};border-top:1px solid {C['border']};")
        btm.setFixedHeight(52)
        bl2 = QHBoxLayout(btm); bl2.setContentsMargins(16,0,16,0)
        bl2.addStretch()
        btn_close = QPushButton("  Close")
        btn_close.setFixedWidth(100); btn_close.setMinimumHeight(34)
        btn_close.clicked.connect(self.accept)
        bl2.addWidget(btn_close)
        root.addWidget(btm)

    def _export_csv(self):
        if not self.cube.trace_headers:
            QMessageBox.information(self, "Export", "No trace headers to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Trace Headers", "", "CSV (*.csv)")
        if not path: return
        import csv
        with open(path, 'w', newline='') as f:
            cols = list(self.cube.trace_headers[0].keys())
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(self.cube.trace_headers)
        QMessageBox.information(self, "Export", f"Saved to:\n{path}")


# ═══════════════════════════════════════════════════════════════════════
#  RIBBON SECTION
# ═══════════════════════════════════════════════════════════════════════
class RibbonSection(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 2, 4, 0); root.setSpacing(2)
        self.btns = QHBoxLayout(); self.btns.setSpacing(2)
        root.addLayout(self.btns)
        lbl = QLabel(title.upper())
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color:{C['text_dim']};font-size:9px;letter-spacing:0.6px;"
                          f"border-top:1px solid {C['border']};padding-top:2px;")
        root.addWidget(lbl)

    def add(self, char, text, big=False, checkable=False, tooltip="") -> QToolButton:
        b = QToolButton()
        pix = QPixmap(18, 18); pix.fill(Qt.transparent)
        p = QPainter(pix); p.setFont(QFont("Segoe UI Emoji", 10))
        p.setPen(QColor(C['text_primary'])); p.drawText(QRect(0,0,18,18), Qt.AlignCenter, char); p.end()
        b.setIcon(QIcon(pix)); b.setIconSize(QSize(18,18))
        b.setText(f"\n{text}" if big else text)
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon if big else Qt.ToolButtonTextBesideIcon)
        b.setCheckable(checkable); b.setToolTip(tooltip or text)
        b.setFixedHeight(52 if big else 26)
        if big: b.setMinimumWidth(50)
        self.btns.addWidget(b); return b

    def add_combo(self, items, w=130) -> QComboBox:
        cb = QComboBox(); cb.addItems(items); cb.setFixedWidth(w)
        self.btns.addWidget(cb); return cb

    def add_sep(self):
        s = QFrame(); s.setFrameShape(QFrame.VLine)
        s.setStyleSheet(f"color:{C['border_med']};"); s.setFixedSize(1, 38)
        self.btns.addWidget(s)


class RibbonTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._l = QHBoxLayout(self); self._l.setContentsMargins(6,2,6,0); self._l.setSpacing(0)
        self._l.addStretch()

    def section(self, title) -> RibbonSection:
        sec = RibbonSection(title, self)
        self._l.insertWidget(self._l.count()-1, sec)
        sep = QFrame(); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{C['border']};")
        self._l.insertWidget(self._l.count()-1, sep)
        return sec


class RibbonWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(94)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self._bar = QTabBar(); self._bar.setObjectName("ribbonBar")
        self._bar.setExpanding(False)
        self._bar.currentChanged.connect(lambda i: self._stack.setCurrentIndex(i))
        root.addWidget(self._bar)
        self._stack = QStackedWidget(); self._stack.setFixedHeight(68)
        self._stack.setObjectName("ribbonContent")
        self._stack.setStyleSheet(f"background:{C['bg_ribbon']};border-bottom:1px solid {C['border']};")
        root.addWidget(self._stack)
        self._tabs: list[RibbonTab] = []

    def add(self, name) -> RibbonTab:
        t = RibbonTab(); self._tabs.append(t); self._stack.addWidget(t); self._bar.addTab(name); return t

    def select(self, idx): self._bar.setCurrentIndex(idx)


# ═══════════════════════════════════════════════════════════════════════
#  PROJECT TREE
# ═══════════════════════════════════════════════════════════════════════
class ProjectTree(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(0)
        # search
        sf = QFrame(); sf.setStyleSheet(f"background:{C['bg_white']};border-bottom:1px solid {C['border']};")
        sfl = QHBoxLayout(sf); sfl.setContentsMargins(6,4,6,4)
        self.search = QLineEdit(); self.search.setPlaceholderText("🔍  Filter…")
        self.search.textChanged.connect(self._filter)
        sfl.addWidget(self.search); l.addWidget(sf)
        self.tree = QTreeWidget(); self.tree.setHeaderHidden(True); self.tree.setIndentation(14)
        l.addWidget(self.tree); self._populate()

    def _mk(self, parent, text, char="📄", col=None, check=None, bold=False):
        it = QTreeWidgetItem(parent if parent else self.tree, [text])
        pix = QPixmap(14,14); pix.fill(Qt.transparent)
        p = QPainter(pix); p.setFont(QFont("Segoe UI Emoji",8))
        p.setPen(QColor(col or C['text_primary'])); p.drawText(QRect(0,0,14,14),Qt.AlignCenter,char); p.end()
        it.setIcon(0, QIcon(pix))
        if check is not None: it.setCheckState(0, Qt.Checked if check else Qt.Unchecked)
        if bold: f=QFont(); f.setBold(True); it.setFont(0,f)
        return it

    def _populate(self):
        self.tree.clear()
        s = self._mk(None,"Seismic","🌊",C['accent2'],bold=True)
        self._mk(s,"Vintages","📅",C['text_dim'])
        self._mk(s,"Interp survey inclusion filters","🔧",C['text_dim'])

        ip = self._mk(None,"Interpretation Folder 1","📁",C['accent_gold'],bold=True)
        self._mk(ip,"3D Interp inclusion filters","🔧",C['text_dim'])
        self._mk(ip,"Seismic Horizon 1","📐",C['accent_green'])

        sv = self._mk(None,"Survey 1","🗺",C['accent'],bold=True)
        dt = self._mk(sv,"Synthetic_Survey_3D","🌐",C['accent2'],bold=True)
        self._mk(dt,"Inline 65","📊",C['accent'],check=True)
        self._mk(dt,"XLine 65","📊",C['accent_orange'],check=True)

        wl = self._mk(None,"Wells","⚡",C['accent_gold'],bold=True)
        for nm in ["Global well logs","Global completions","Global observed data","Well attributes","Well filters"]:
            self._mk(wl,nm,"·",C['text_dim'])

        for hw,col in [("HD-01",C['accent_green']),("HD-02",C['accent_orange']),("HD-03",C['accent2'])]:
            hd = self._mk(None,hw,"🔵",col,bold=True)
            sp = self._mk(hd,"Surveys and plans","📋",C['text_secondary'])
            self._mk(sp,"MD Incl Azim survey 1","📐",C['text_dim'])
            self._mk(hd,"Well logs","📈",C['text_secondary'])

        self.tree.expandAll()
        wl.setExpanded(False)

    def _filter(self, txt):
        def _h(it, t):
            vis = False
            for i in range(it.childCount()):
                ch = it.child(i); cv = _h(ch, t); ch.setHidden(not cv); vis = vis or cv
            own = t.lower() in it.text(0).lower()
            return own or vis
        for i in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(i)
            v = _h(it, txt); it.setHidden(not v and bool(txt))


# ═══════════════════════════════════════════════════════════════════════
#  PROPERTIES PANEL
# ═══════════════════════════════════════════════════════════════════════
class PropertiesPanel(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240); self.setMaximumWidth(280)
        root = QVBoxLayout(self); root.setContentsMargins(10,10,10,10); root.setSpacing(10)

        # ── Slice positions ──────────────────────────────────────────
        g1 = QGroupBox("SLICE POSITIONS"); f1 = QFormLayout(g1)
        f1.setSpacing(8); f1.setLabelAlignment(Qt.AlignRight)
        self.spn_il = QSpinBox(); self.spn_il.setMinimum(0)
        self.spn_xl = QSpinBox(); self.spn_xl.setMinimum(0)
        self.spn_t  = QSpinBox(); self.spn_t.setMinimum(0)
        self.chk_il = QCheckBox(); self.chk_il.setChecked(True)
        self.chk_xl = QCheckBox(); self.chk_xl.setChecked(True)
        self.chk_t  = QCheckBox(); self.chk_t.setChecked(True)
        for spn, chk, lbl in [(self.spn_il,self.chk_il,"Inline:"),
                               (self.spn_xl,self.chk_xl,"Crossline:"),
                               (self.spn_t, self.chk_t, "Time idx:")]:
            row = QHBoxLayout(); row.setSpacing(4)
            row.addWidget(chk); row.addWidget(spn)
            f1.addRow(lbl, row)
            spn.valueChanged.connect(self.changed); chk.stateChanged.connect(self.changed)
        root.addWidget(g1)

        # ── Display ──────────────────────────────────────────────────
        g2 = QGroupBox("DISPLAY"); f2 = QFormLayout(g2)
        f2.setSpacing(8); f2.setLabelAlignment(Qt.AlignRight)
        self.cbo_cs = QComboBox(); self.cbo_cs.addItems(COLORSCALES)
        self.cbo_cs.currentIndexChanged.connect(self.changed)
        f2.addRow("Colorscale:", self.cbo_cs)

        self.sld_clip = QSlider(Qt.Horizontal); self.sld_clip.setRange(50,100); self.sld_clip.setValue(98)
        self.lbl_clip = QLabel("98%"); self.lbl_clip.setStyleSheet(
            f"background:{C['badge_blue']};color:{C['accent']};border-radius:4px;"
            f"padding:1px 6px;font-size:10px;font-weight:700;min-width:30px;text-align:center;")
        self.sld_clip.valueChanged.connect(lambda v:(self.lbl_clip.setText(f"{v}%"),self.changed.emit()))
        r1=QHBoxLayout();r1.addWidget(self.sld_clip);r1.addWidget(self.lbl_clip)
        f2.addRow("Clip %:", r1)

        self.sld_op = QSlider(Qt.Horizontal); self.sld_op.setRange(20,100); self.sld_op.setValue(100)
        self.lbl_op = QLabel("1.0"); self.lbl_op.setStyleSheet(
            f"background:{C['badge_blue']};color:{C['accent']};border-radius:4px;"
            f"padding:1px 6px;font-size:10px;font-weight:700;min-width:30px;text-align:center;")
        self.sld_op.valueChanged.connect(lambda v:(self.lbl_op.setText(f"{v/100:.2f}"),self.changed.emit()))
        r2=QHBoxLayout();r2.addWidget(self.sld_op);r2.addWidget(self.lbl_op)
        f2.addRow("Opacity:", r2)

        self.sld_ds = QSlider(Qt.Horizontal); self.sld_ds.setRange(1,4); self.sld_ds.setValue(1)
        self.lbl_ds = QLabel("1×"); self.lbl_ds.setStyleSheet(
            f"background:{C['badge_blue']};color:{C['accent']};border-radius:4px;"
            f"padding:1px 6px;font-size:10px;font-weight:700;min-width:30px;text-align:center;")
        self.sld_ds.valueChanged.connect(lambda v:(self.lbl_ds.setText(f"{v}×"),self.changed.emit()))
        r3=QHBoxLayout();r3.addWidget(self.sld_ds);r3.addWidget(self.lbl_ds)
        f2.addRow("Downsample:", r3)
        root.addWidget(g2)

        # ── Processing ────────────────────────────────────────────────
        g3 = QGroupBox("PROCESSING"); f3 = QVBoxLayout(g3); f3.setSpacing(5)
        self.chk_agc  = QCheckBox("AGC  (Automatic Gain Control)")
        self.chk_norm = QCheckBox("Trace Normalise")
        self.chk_smth = QCheckBox("Gaussian Smooth")
        for c in [self.chk_agc,self.chk_norm,self.chk_smth]:
            c.stateChanged.connect(self.changed); f3.addWidget(c)
        root.addWidget(g3)

        # ── Action buttons ────────────────────────────────────────────
        self.btn_render = QPushButton("⟳  Render 3D")
        self.btn_render.setProperty("primary","true"); self.btn_render.setMinimumHeight(36)
        root.addWidget(self.btn_render)

        self.btn_browser = QPushButton("🌐  Open in Browser")
        self.btn_browser.setProperty("secondary","true"); self.btn_browser.setMinimumHeight(32)
        root.addWidget(self.btn_browser)

        root.addStretch()

    @property
    def il_idx(self):    return self.spn_il.value()
    @property
    def xl_idx(self):    return self.spn_xl.value()
    @property
    def t_idx(self):     return self.spn_t.value()
    @property
    def colorscale(self):return self.cbo_cs.currentText()
    @property
    def clip(self):      return float(self.sld_clip.value())
    @property
    def opacity(self):   return self.sld_op.value()/100.0
    @property
    def downsample(self):return self.sld_ds.value()
    @property
    def show_il(self):   return self.chk_il.isChecked()
    @property
    def show_xl(self):   return self.chk_xl.isChecked()
    @property
    def show_t(self):    return self.chk_t.isChecked()
    @property
    def agc(self):       return self.chk_agc.isChecked()
    @property
    def norm(self):      return self.chk_norm.isChecked()
    @property
    def smooth(self):    return self.chk_smth.isChecked()

    def update_for_cube(self, cube):
        for w in [self.spn_il,self.spn_xl,self.spn_t]: w.blockSignals(True)
        self.spn_il.setMaximum(cube.n_inline-1); self.spn_il.setValue(cube.n_inline//2)
        self.spn_xl.setMaximum(cube.n_crossline-1); self.spn_xl.setValue(cube.n_crossline//2)
        self.spn_t.setMaximum(cube.n_time-1); self.spn_t.setValue(cube.n_time//3)
        for w in [self.spn_il,self.spn_xl,self.spn_t]: w.blockSignals(False)


# ═══════════════════════════════════════════════════════════════════════
#  VIEWPORT INFO BAR
# ═══════════════════════════════════════════════════════════════════════
class ViewportInfoBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("infoBar"); self.setFixedHeight(34)
        hl = QHBoxLayout(self); hl.setContentsMargins(10,0,10,0); hl.setSpacing(8)

        self.lbl_il = self._pill("IL: –",  C['accent'])
        self.lbl_xl = self._pill("XL: –",  C['accent_orange'])
        self.lbl_t  = self._pill("T: –",   C['accent_green'])
        for w in [self.lbl_il, self.lbl_xl, self.lbl_t]: hl.addWidget(w)
        hl.addStretch()

        for ch, tip in [("🔍","Zoom"),("✋","Pan"),("⟳","Reset"),("📸","Screenshot")]:
            b = QToolButton(); b.setText(ch); b.setToolTip(tip)
            b.setStyleSheet(f"QToolButton{{background:transparent;border:none;font-size:14px;"
                            f"color:{C['text_dim']};padding:2px 4px;}}"
                            f"QToolButton:hover{{color:{C['accent']};background:{C['bg_hover']};border-radius:3px;}}")
            hl.addWidget(b)

    def _pill(self, txt, col):
        l = QLabel(txt)
        l.setStyleSheet(f"background:{C['bg_white']};color:{col};border:1.5px solid {col}40;"
                        f"border-radius:4px;padding:2px 10px;font-size:10px;font-weight:700;letter-spacing:0.3px;")
        return l

    def update(self, il, xl, t_ms):
        self.lbl_il.setText(f"IL: {il}")
        self.lbl_xl.setText(f"XL: {xl}")
        self.lbl_t.setText(f"T: {t_ms:.0f} ms")


# ═══════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cube: SeismicCube | None = None
        self.loader = None
        self.setWindowTitle("SeismicVision Pro  –  Seismic Interpretation Platform")
        self.resize(1580, 940); self.setMinimumSize(1100, 650)
        self.setStyleSheet(QSS)

        self._build_title_ribbon()
        self._build_left()
        self._build_central()
        self._build_right()
        self._build_status()

        self._timer = QTimer(self); self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._render_current)
        self._props.changed.connect(lambda: self._timer.start(380))
        self._props.btn_render.clicked.connect(self._render_3d)
        self._props.btn_browser.clicked.connect(lambda: self._vp3d.open_browser())

        self._load_demo()

    # ─── Title + Ribbon ──────────────────────────────────────────────
    def _build_title_ribbon(self):
        # Title bar
        tbar = QFrame()
        tbar.setFixedHeight(30)
        tbar.setStyleSheet(f"background:{C['bg_toolbar']};border-bottom:1px solid {C['border']};")
        tbl = QHBoxLayout(tbar); tbl.setContentsMargins(10,0,10,0); tbl.setSpacing(8)

        ico = QLabel("◈"); ico.setStyleSheet(f"color:{C['accent']};font-size:16px;font-weight:700;")
        tbl.addWidget(ico)
        proj_lbl = QLabel("SeismicVision Pro  –  [Synthetic_Survey_3D]")
        proj_lbl.setStyleSheet(f"color:{C['text_primary']};font-size:12px;font-weight:600;")
        tbl.addWidget(proj_lbl)
        tbl.addStretch()

        for ch, tip, cb in [("📂","Open SEG-Y",self._open_file),
                              ("💾","Save",lambda:None),
                              ("↩","Undo",lambda:None),("↪","Redo",lambda:None)]:
            b = QToolButton(); b.setText(ch); b.setToolTip(tip); b.clicked.connect(cb)
            b.setStyleSheet(f"QToolButton{{background:transparent;border:none;"
                            f"color:{C['text_secondary']};font-size:15px;padding:2px 5px;}}"
                            f"QToolButton:hover{{color:{C['accent']};background:{C['bg_hover']};border-radius:3px;}}")
            tbl.addWidget(b)

        # ── RIBBON (only relevant tabs) ──────────────────────────────
        self._ribbon = RibbonWidget()

        # Home
        h = self._ribbon.add("Home")
        hs = h.section("File")
        hs.add("📂","Open SEG-Y",big=True).clicked.connect(self._open_file)
        hs.add("🧪","Demo Data", big=True).clicked.connect(self._load_demo)
        hs.add_sep()
        hs2 = h.section("Windows")
        hs2.add("🧊","New 3D",big=True)
        hs2.add("📊","New 2D",big=True)
        hs2.add_sep()
        hs3 = h.section("Dataset")
        btn_info = hs3.add("📋","Data Info",big=True,tooltip="Open Data Information window")
        btn_info.clicked.connect(self._show_data_info)
        hs3.add("💾","Export",big=True).clicked.connect(self._export_fig)

        # Seismic Interpretation
        si = self._ribbon.add("Seismic Interpretation")
        s1 = si.section("Conditioning")
        s1.add("〰","Wavelet toolbox",big=True)
        s1.add("📋","Log conditioning",big=True)
        s1.add_sep()
        s2 = si.section("Interpretation")
        s2.add("➕","Insert slice",big=True)
        s2.add("🌊","Seismic interp.",big=True)
        s2.add_sep()
        s3 = si.section("2D / 3D View")
        s3.add("🗺","Surface attr.",big=True)
        s3.add("📊","Calculator",big=True)
        s3.add("🕸","Neural net",big=True)
        s3.add_sep()
        s4 = si.section("Data Info")
        btn_info2 = s4.add("📋","Data Info",big=True,tooltip="Open Data Information window")
        btn_info2.clicked.connect(self._show_data_info)
        btn_info3 = s4.add("📈","Statistics",big=True,tooltip="Open Data Statistics")
        btn_info3.clicked.connect(self._show_data_info)

        # 3D
        td = self._ribbon.add("3D")
        t1 = td.section("3D View Controls")
        t1.add("🧊","Reset Camera",big=True)
        t1.add("🔍","Zoom In",big=True)
        t1.add("⚙","Render Settings",big=True)
        t1.add_sep()
        t2 = td.section("Slice Tools")
        t2.add("📊","Add Inline",big=True)
        t2.add("📊","Add Xline",big=True)
        t2.add("🗺","Add TimeSlice",big=True)
        t2.add_sep()
        t3 = td.section("Data Info")
        btn_info4 = t3.add("📋","Data Info",big=True)
        btn_info4.clicked.connect(self._show_data_info)
        t3.add("📸","Screenshot",big=True)

        # Window
        wt = self._ribbon.add("Window")
        w1 = wt.section("Layout")
        w1.add("🔲","Tile Windows",big=True)
        w1.add("🗗","Float All",big=True)
        w1.add_sep()
        w2 = wt.section("Open")
        w2.add("📋","Data Info",big=True).clicked.connect(self._show_data_info)
        w2.add("🌐","In Browser",big=True).clicked.connect(lambda: self._vp3d.open_browser())

        self._ribbon.select(1)   # default: Seismic Interpretation

        # Assemble title + ribbon into a toolbar container
        container = QWidget()
        cv = QVBoxLayout(container); cv.setContentsMargins(0,0,0,0); cv.setSpacing(0)
        cv.addWidget(tbar)
        # Menu bar embedded in title bar area
        mb = QMenuBar()
        mb.setStyleSheet(f"QMenuBar{{background:{C['bg_toolbar']};border:none;"
                         f"color:{C['text_secondary']};font-size:12px;}}"
                         f"QMenuBar::item{{padding:0 10px;border-radius:3px;}}"
                         f"QMenuBar::item:selected{{background:{C['bg_hover']};color:{C['accent']};}}")
        for mn in ["File","Home","Seismic Interpretation","3D","Window","Help"]:
            m = mb.addMenu(mn)
            if mn == "File":
                m.addAction("Open SEG-Y…", self._open_file, "Ctrl+O")
                m.addAction("Load Demo Data", self._load_demo)
                m.addSeparator()
                m.addAction("Data Information…", self._show_data_info, "Ctrl+I")
                m.addSeparator()
                m.addAction("Export Figure…", self._export_fig, "Ctrl+E")
                m.addSeparator()
                m.addAction("Quit", self.close, "Ctrl+Q")
            elif mn == "Help":
                m.addAction("About SeismicVision Pro", self._about)
        cv.addWidget(mb)
        cv.addWidget(self._ribbon)

        tb = QToolBar("Top"); tb.setMovable(False); tb.setFloatable(False)
        tb.setStyleSheet("QToolBar{background:transparent;border:none;padding:0;margin:0;}")
        tb.addWidget(container)
        self.addToolBar(Qt.TopToolBarArea, tb)

    # ─── Left Dock ───────────────────────────────────────────────────
    def _build_left(self):
        dock = QDockWidget("", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        dock.setMinimumWidth(220); dock.setMaximumWidth(295)

        outer = QWidget(); outer.setObjectName("sidePanel")
        ov = QVBoxLayout(outer); ov.setContentsMargins(0,0,0,0); ov.setSpacing(0)

        tabs = QTabWidget(); tabs.setObjectName("panelTabs")
        tabs.tabBar().setObjectName("panelBar")
        tabs.tabBar().setStyleSheet(f"QTabBar{{background:{C['bg_white']};border-bottom:1px solid {C['border']};}}")

        self._proj_tree = ProjectTree()
        tabs.addTab(self._proj_tree, "Input")

        cases = QWidget(); cl = QVBoxLayout(cases); cl.setContentsMargins(10,10,10,10)
        cl.addWidget(QLabel("No cases defined.")); cl.addStretch()
        tabs.addTab(cases, "Cases")

        tmpl = QWidget(); tl = QVBoxLayout(tmpl); tl.setContentsMargins(10,10,10,10)
        tl.addWidget(QLabel("No templates.")); tl.addStretch()
        tabs.addTab(tmpl, "Templates")

        ov.addWidget(tabs)

        # Models strip
        mf = QFrame()
        mf.setStyleSheet(f"background:{C['bg_app']};border-top:1px solid {C['border']};")
        mf.setFixedHeight(42)
        mfl = QHBoxLayout(mf); mfl.setContentsMargins(10,0,10,0)
        ml = QLabel("Models"); ml.setStyleSheet(f"color:{C['accent']};font-size:10px;font-weight:700;letter-spacing:0.8px;")
        mfl.addWidget(ml); mfl.addStretch()
        ov.addWidget(mf)

        dock.setWidget(outer)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    # ─── Central ─────────────────────────────────────────────────────
    def _build_central(self):
        cw = QWidget(); self.setCentralWidget(cw)
        cv = QVBoxLayout(cw); cv.setContentsMargins(0,0,0,0); cv.setSpacing(0)

        # Viewport info bar
        self._vp_bar = ViewportInfoBar()
        cv.addWidget(self._vp_bar)

        # Viewport tabs
        self._vp_tabs = QTabWidget()
        self._vp_tabs.setObjectName("vpTabs"); self._vp_tabs.tabBar().setObjectName("vpBar")
        self._vp_tabs.setTabsClosable(True)
        self._vp_tabs.tabCloseRequested.connect(lambda i: i > 0 and self._vp_tabs.removeTab(i))
        cv.addWidget(self._vp_tabs)

        self._vp3d = PlotlyView()
        self._vp_tabs.addTab(self._vp3d, "🧊  3D Seismic View")
        
        # remove close button from first tab
        self._vp_tabs.tabBar().setTabButton(0, QTabBar.RightSide, None)

        self._vp_il = PlotlyView()
        self._vp_tabs.addTab(self._vp_il, "📊  Inline Section")

        self._vp_xl = PlotlyView()
        self._vp_tabs.addTab(self._vp_xl, "📊  Crossline Section")

        self._vp_ts = PlotlyView()
        self._vp_tabs.addTab(self._vp_ts, "🗺  Time Slice")

        self._vp_tabs.currentChanged.connect(self._on_tab)

    # ─── Right Dock ───────────────────────────────────────────────────
    def _build_right(self):
        dock = QDockWidget("", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        dock.setMinimumWidth(250); dock.setMaximumWidth(285)

        outer = QWidget(); outer.setObjectName("rightPanel")
        ov = QVBoxLayout(outer); ov.setContentsMargins(0,0,0,0); ov.setSpacing(0)

        tabs = QTabWidget(); tabs.setObjectName("panelTabs")
        tabs.tabBar().setObjectName("panelBar")

        scroll = QScrollArea(); scroll.setFrameShape(QFrame.NoFrame); scroll.setWidgetResizable(True)
        self._props = PropertiesPanel()
        scroll.setWidget(self._props)
        tabs.addTab(scroll, "Properties")

        # Quick stats tab
        stats_w = QWidget(); sl = QVBoxLayout(stats_w)
        sl.setContentsMargins(10,10,10,10); sl.setSpacing(8)
        self._stats_lbl = QLabel("Load data to see statistics.")
        self._stats_lbl.setWordWrap(True)
        self._stats_lbl.setStyleSheet(f"color:{C['text_secondary']};font-size:11px;")
        sl.addWidget(self._stats_lbl)
        btn_full = QPushButton("📋  Open Full Data Info")
        btn_full.setProperty("secondary","true"); btn_full.clicked.connect(self._show_data_info)
        sl.addWidget(btn_full); sl.addStretch()
        tabs.addTab(stats_w, "Statistics")

        ov.addWidget(tabs)
        dock.setWidget(outer)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    # ─── Status Bar ───────────────────────────────────────────────────
    def _build_status(self):
        sb = QStatusBar(); self.setStatusBar(sb)
        self._lbl_status = QLabel("Ready")
        self._lbl_status.setStyleSheet(f"color:{C['text_secondary']};")
        self._pb = QProgressBar(); self._pb.setFixedWidth(160); self._pb.setVisible(False)
        self._lbl_pos = QLabel("")
        self._lbl_pos.setStyleSheet(f"color:{C['accent']};font-size:11px;")
        self._lbl_ram = QLabel("RAM: –")
        self._lbl_ram.setStyleSheet(f"color:{C['text_dim']};font-size:11px;")
        sb.addWidget(self._lbl_status, 1)
        sb.addPermanentWidget(self._pb)
        sb.addPermanentWidget(self._lbl_pos)
        sb.addPermanentWidget(QLabel("  "))
        sb.addPermanentWidget(self._lbl_ram)
        t = QTimer(self); t.timeout.connect(self._ram_tick); t.start(3000)

    def _ram_tick(self):
        try:
            import psutil; mb = psutil.Process().memory_info().rss//1024//1024
            self._lbl_ram.setText(f"RAM: {mb} MB")
        except: pass

    # ─── FILE OPS ─────────────────────────────────────────────────────
    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(self,"Open SEG-Y","",
                    "SEG-Y Files (*.segy *.sgy *.seg *.SGY *.SEGY);;All (*.*)")
        if path: self._start_load(path)

    def _start_load(self, path):
        self._pb.setVisible(True); self._pb.setValue(0)
        self._lbl_status.setText(f"Loading  {os.path.basename(path)}…")
        self.loader = CubeLoader(path)
        self.loader.progress.connect(lambda p,m:(self._pb.setValue(p),self._lbl_status.setText(m)))
        self.loader.finished.connect(self._on_loaded)
        self.loader.error.connect(lambda m:(self._pb.setVisible(False),
            QMessageBox.critical(self,"Load Error",m)))
        self.loader.start()

    def _on_loaded(self, cube):
        self.cube = cube; self._pb.setVisible(False)
        self._props.update_for_cube(cube)
        self._update_stats_panel()
        self._vp_bar.update(cube.n_inline//2, cube.n_crossline//2,
                            cube.n_time//3 * cube.sample_rate_ms)
        self._render_all()
        self._lbl_status.setText(
            f"Loaded: {cube.filename}  |  "
            f"{cube.n_inline} IL × {cube.n_crossline} XL × {cube.n_time} T  |  "
            f"{cube.sample_rate_ms:.2f} ms/sample")

    def _load_demo(self):
        self._lbl_status.setText("Generating synthetic 3D demo…")
        self.cube = make_demo_cube()
        self._props.update_for_cube(self.cube)
        self._update_stats_panel()
        self._vp_bar.update(65, 65, 65*self.cube.sample_rate_ms)
        self._render_all()
        c = self.cube
        self._lbl_status.setText(f"Demo  |  {c.n_inline} IL × {c.n_crossline} XL × {c.n_time} T  |  {c.sample_rate_ms:.2f} ms/sample")

    def _update_stats_panel(self):
        if not self.cube: return
        c = self.cube; d = c.cube.ravel()
        lines = [
            f"<b>{c.filename}</b>",
            f"<br><span style='color:{C['text_dim']};'>Loaded: {c.loaded_at}</span>",
            f"<hr style='border:none;border-top:1px solid {C['border']};margin:6px 0;'>",
            f"<b style='color:{C['accent']};'>Cube Dimensions</b><br>",
            f"Inlines: <b>{c.n_inline}</b>  ·  Crosslines: <b>{c.n_crossline}</b><br>",
            f"Time Samples: <b>{c.n_time}</b>  ·  Duration: <b>{c.duration_ms:.0f} ms</b><br>",
            f"Sample Rate: <b>{c.sample_rate_ms:.2f} ms</b>",
            f"<hr style='border:none;border-top:1px solid {C['border']};margin:6px 0;'>",
            f"<b style='color:{C['accent']};'>Amplitude</b><br>",
            f"Min: <b>{d.min():.3f}</b>  Max: <b>{d.max():.3f}</b><br>",
            f"RMS: <b>{np.sqrt(np.mean(d**2)):.4f}</b>  Mean: <b>{d.mean():.4f}</b>",
        ]
        self._stats_lbl.setText("".join(lines))
        self._stats_lbl.setTextFormat(Qt.RichText)

    # ─── DATA INFO POPUP ──────────────────────────────────────────────
    def _show_data_info(self):
        if not self.cube:
            QMessageBox.information(self,"No Data","Load a SEG-Y file first.")
            return
        dlg = DataInfoDialog(self.cube, self)
        dlg.exec_()

    # ─── PROCESSING ───────────────────────────────────────────────────
    def _proc(self):
        p = self._props
        if not (p.agc or p.norm or p.smooth): return self.cube
        out = SeismicCube(); out.__dict__.update(self.cube.__dict__)
        d = self.cube.cube.copy()
        if p.norm:
            mx = np.max(np.abs(d),axis=2,keepdims=True)+1e-12; d /= mx
        if p.agc and SCIPY:
            win=30
            for ii in range(d.shape[0]):
                for ix in range(d.shape[1]):
                    tr=d[ii,ix].astype(np.float64)
                    env=np.abs(sp_signal.hilbert(tr))
                    env=np.convolve(env,np.ones(win)/win,'same')+1e-12
                    d[ii,ix]=(tr/env).astype(np.float32)
        if p.smooth and SCIPY: d=gaussian_filter(d,sigma=0.8)
        out.cube=d.astype(np.float32); return out

    # ─── RENDER ───────────────────────────────────────────────────────
    def _render_3d(self):
        if not (self.cube and PLOTLY): return
        p = self._props; cube = self._proc()
        self._lbl_status.setText("Rendering 3D scene…")
        html = build_3d_html(cube, p.il_idx, p.xl_idx, p.t_idx,
                             p.clip, p.colorscale, p.show_il, p.show_xl,
                             p.show_t, p.opacity, p.downsample)
        self._vp3d.set_html(html)
        self._vp_bar.update(p.il_idx, p.xl_idx, p.t_idx*self.cube.sample_rate_ms)
        self._lbl_status.setText("3D scene ready.")

    def _render_il(self):
        if not (self.cube and PLOTLY): return
        p=self._props; html=build_2d_html(self._proc(),"inline",p.il_idx,p.colorscale,p.clip)
        self._vp_il.set_html(html)

    def _render_xl(self):
        if not (self.cube and PLOTLY): return
        p=self._props; html=build_2d_html(self._proc(),"crossline",p.xl_idx,p.colorscale,p.clip)
        self._vp_xl.set_html(html)

    def _render_ts(self):
        if not (self.cube and PLOTLY): return
        p=self._props; html=build_2d_html(self._proc(),"time",p.t_idx,p.colorscale,p.clip)
        self._vp_ts.set_html(html)

    def _render_all(self):
        if not self.cube: return
        self._render_3d(); self._render_il(); self._render_xl(); self._render_ts()

    def _render_current(self):
        {0:self._render_3d,1:self._render_il,2:self._render_xl,3:self._render_ts
         }.get(self._vp_tabs.currentIndex(),lambda:None)()

    def _on_tab(self, idx):
        if self.cube:
            {0:self._render_3d,1:self._render_il,2:self._render_xl,3:self._render_ts
             }.get(idx,lambda:None)()

    # ─── EXPORT ───────────────────────────────────────────────────────
    def _export_fig(self):
        if not self.cube:
            QMessageBox.information(self,"Export","No data loaded."); return
        path, _ = QFileDialog.getSaveFileName(self,"Export","","HTML (*.html);;PNG (*.png)")
        if not path: return
        if path.endswith(".html"):
            p = self._props
            html = build_3d_html(self._proc(),p.il_idx,p.xl_idx,p.t_idx,p.clip,
                                  p.colorscale,p.show_il,p.show_xl,p.show_t,p.opacity,p.downsample)
            with open(path,'w',encoding='utf-8') as f: f.write(html)
        else:
            QMessageBox.information(self,"PNG Export","Switch to in-app viewport and use the camera icon,\nor export as HTML for best quality.")
            return
        self._lbl_status.setText(f"Exported → {path}")

    # ─── ABOUT ────────────────────────────────────────────────────────
    def _about(self):
        QMessageBox.about(self,"About SeismicVision Pro",
            f"<h2 style='color:{C['accent']}'>SeismicVision Pro</h2>"
            f"<p>Professional SEG-Y Seismic Interpretation Platform<br><br>"
            f"Stack:  PyQt5  ·  Plotly  ·  QWebEngine  ·  NumPy  ·  SciPy  ·  segyio</p>"
            f"<p>Features:<br>"
            f"• Interactive 3D surface viewer (Inline + Crossline + Time Slice)<br>"
            f"• Full Data Info popup (headers, trace headers, statistics)<br>"
            f"• AGC, Trace Normalise, Gaussian Smooth processing<br>"
            f"• Export to HTML / PNG<br>"
            f"• SEG-Y Rev 1 &amp; 2  |  Raw binary fallback</p>")


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SeismicVision Pro")
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(C['bg_app']))
    pal.setColor(QPalette.WindowText,      QColor(C['text_primary']))
    pal.setColor(QPalette.Base,            QColor(C['bg_white']))
    pal.setColor(QPalette.AlternateBase,   QColor(C['bg_panel']))
    pal.setColor(QPalette.Text,            QColor(C['text_primary']))
    pal.setColor(QPalette.Button,          QColor(C['bg_white']))
    pal.setColor(QPalette.ButtonText,      QColor(C['text_primary']))
    pal.setColor(QPalette.Highlight,       QColor(C['accent']))
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    pal.setColor(QPalette.ToolTipBase,     QColor(C['bg_white']))
    pal.setColor(QPalette.ToolTipText,     QColor(C['text_primary']))
    pal.setColor(QPalette.Light,           QColor(C['bg_white']))
    pal.setColor(QPalette.Midlight,        QColor(C['bg_panel']))
    pal.setColor(QPalette.Mid,             QColor(C['border_med']))
    pal.setColor(QPalette.Dark,            QColor(C['text_dim']))
    app.setPalette(pal)

    win = MainWindow()
    win.show()

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        win._start_load(sys.argv[1])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()