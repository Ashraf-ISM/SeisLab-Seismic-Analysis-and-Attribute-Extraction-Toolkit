"""
Well Log Viewer - Professional Petrophysics Analysis Tool
Inspired by Petrel / Interactive Petrophysics style
Requirements: pip install PyQt5 lasio matplotlib numpy pandas scipy
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import colors as mcolors
from scipy import stats

try:
    import lasio
    HAS_LASIO = True
except ImportError:
    HAS_LASIO = False

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTabWidget, QToolBar,
    QAction, QFileDialog, QLabel, QStatusBar, QDockWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QFormLayout, QLineEdit, QSpinBox, QCheckBox, QColorDialog,
    QMessageBox, QDialog, QDialogButtonBox, QScrollArea,
    QSizePolicy, QFrame, QGridLayout, QDoubleSpinBox, QMenu,
    QAction, QToolButton, QAbstractItemView, QTextEdit
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QPixmap


# ─────────────────────────────────────────────
#  COLOUR PALETTE (light petroleum-style theme)
# ─────────────────────────────────────────────
DARK_BG    = "#f4f6fb"
PANEL_BG   = "#ffffff"
ACCENT     = "#1976d2"
ACCENT2    = "#ef6c00"
TEXT_LIGHT = "#1f2937"
TEXT_DIM   = "#5f6b7a"
GRID_CLR   = "#d5dbe5"
TRACK_COLORS = [
    "#00bfff", "#ff6b35", "#4caf50", "#ffeb3b",
    "#e91e63", "#9c27b0", "#00e5ff", "#ff9800",
    "#76ff03", "#f44336"
]
FIG_FONT_DELTA = 2


def fs(points):
    """Consistent +2 pt size bump for all matplotlib figure text."""
    return points + FIG_FONT_DELTA


STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_LIGHT};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 9pt;
}}
QMenuBar {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    border-bottom: 1px solid {GRID_CLR};
}}
QMenuBar::item:selected {{ background-color: {ACCENT}; color: #fff; }}
QMenu {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
}}
QMenu::item:selected {{ background-color: {ACCENT}; color: #fff; }}
QToolBar {{
    background-color: {PANEL_BG};
    border-bottom: 1px solid {GRID_CLR};
    spacing: 4px;
    padding: 2px;
}}
QToolBar QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    color: {TEXT_LIGHT};
}}
QToolBar QToolButton:hover {{ background-color: {ACCENT}; color: #fff; border-color: {ACCENT}; }}
QToolBar QToolButton:pressed {{ background-color: #1565c0; }}
QDockWidget {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
}}
QDockWidget::title {{
    background-color: {ACCENT};
    color: #fff;
    padding: 4px;
    font-weight: bold;
}}
QTreeWidget {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
    alternate-background-color: {DARK_BG};
}}
QTreeWidget::item:selected {{ background-color: {ACCENT}; color: #fff; }}
QTreeWidget::item:hover {{ background-color: #e8f1fb; }}
QTabWidget::pane {{
    border: 1px solid {GRID_CLR};
    background-color: {PANEL_BG};
}}
QTabBar::tab {{
    background-color: {DARK_BG};
    color: {TEXT_DIM};
    border: 1px solid {GRID_CLR};
    padding: 6px 14px;
    border-bottom: none;
}}
QTabBar::tab:selected {{
    background-color: {PANEL_BG};
    color: {ACCENT};
    border-top: 2px solid {ACCENT};
}}
QTabBar::tab:hover {{ color: {TEXT_LIGHT}; }}
QTableWidget {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    gridline-color: {GRID_CLR};
    border: 1px solid {GRID_CLR};
}}
QTableWidget::item:selected {{ background-color: {ACCENT}; color: #fff; }}
QHeaderView::section {{
    background-color: {DARK_BG};
    color: {ACCENT};
    border: 1px solid {GRID_CLR};
    padding: 4px;
    font-weight: bold;
}}
QGroupBox {{
    border: 1px solid {GRID_CLR};
    border-radius: 4px;
    margin-top: 8px;
    color: {ACCENT};
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}
QPushButton {{
    background-color: {ACCENT};
    color: #fff;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: #1e88e5; }}
QPushButton:pressed {{ background-color: #1565c0; }}
QPushButton#secondary {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
}}
QPushButton#secondary:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QComboBox {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
    border-radius: 3px;
    padding: 3px 8px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    selection-background-color: {ACCENT};
}}
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {DARK_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
    border-radius: 3px;
    padding: 3px 6px;
}}
QLineEdit:focus, QSpinBox:focus {{ border-color: {ACCENT}; }}
QScrollBar:vertical {{
    background: {DARK_BG};
    width: 8px;
}}
QScrollBar::handle:vertical {{ background: {GRID_CLR}; border-radius: 4px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QStatusBar {{
    background-color: {PANEL_BG};
    color: {TEXT_DIM};
    border-top: 1px solid {GRID_CLR};
}}
QListWidget {{
    background-color: {PANEL_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
}}
QListWidget::item:selected {{ background-color: {ACCENT}; color: #fff; }}
QTextEdit {{
    background-color: {DARK_BG};
    color: {TEXT_LIGHT};
    border: 1px solid {GRID_CLR};
    font-family: 'Courier New', monospace;
}}
QCheckBox {{ color: {TEXT_LIGHT}; }}
QCheckBox::indicator:checked {{ background-color: {ACCENT}; border: 1px solid {ACCENT}; }}
QSplitter::handle {{ background: {GRID_CLR}; }}
"""


# ─────────────────────────────────────────────
#  MATPLOTLIB STYLE
# ─────────────────────────────────────────────
def apply_mpl_style():
    plt.rcParams.update({
        'figure.facecolor':  DARK_BG,
        'axes.facecolor':    PANEL_BG,
        'axes.edgecolor':    GRID_CLR,
        'axes.labelcolor':   TEXT_LIGHT,
        'axes.grid':         True,
        'grid.color':        GRID_CLR,
        'grid.linewidth':    0.5,
        'xtick.color':       TEXT_DIM,
        'ytick.color':       TEXT_DIM,
        'text.color':        TEXT_LIGHT,
        'legend.facecolor':  PANEL_BG,
        'legend.edgecolor':  GRID_CLR,
        'savefig.facecolor': DARK_BG,
        'font.size':         fs(10),
        'axes.titlesize':    fs(11),
        'axes.labelsize':    fs(10),
        'xtick.labelsize':   fs(8),
        'ytick.labelsize':   fs(8),
        'legend.fontsize':   fs(8),
    })

apply_mpl_style()


# ─────────────────────────────────────────────
#  DATA MODEL
# ─────────────────────────────────────────────
class WellData:
    def __init__(self):
        self.name       = ""
        self.filename   = ""
        self.df         = pd.DataFrame()
        self.header     = {}
        self.curves     = {}      # {mnem: {'unit':'', 'desc':''}}
        self.depth_col  = None

    @property
    def curve_names(self):
        return list(self.df.columns) if not self.df.empty else []

    def stats(self):
        if self.df.empty:
            return pd.DataFrame()
        return self.df.describe().round(4)


def load_las(filepath) -> WellData:
    if not HAS_LASIO:
        raise ImportError("lasio is not installed. pip install lasio")
    las = lasio.read(filepath)
    well = WellData()
    well.filename = filepath
    well.name = las.well.WELL.value or os.path.basename(filepath)

    # Header
    for item in las.well:
        well.header[item.mnemonic] = {'value': item.value, 'unit': item.unit, 'desc': item.descr}

    # Curves metadata
    for c in las.curves:
        well.curves[c.mnemonic] = {'unit': c.unit, 'desc': c.descr}

    well.df = las.df().reset_index()
    well.depth_col = well.df.columns[0]          # first col = DEPT
    well.df.replace(-999.25, np.nan, inplace=True)
    return well


def load_csv(filepath) -> WellData:
    well = WellData()
    well.filename = filepath
    well.name = os.path.basename(filepath)
    df = pd.read_csv(filepath)
    df.replace([-999.25, -9999.0], np.nan, inplace=True)
    well.df = df
    # guess depth column
    for col in df.columns:
        if col.upper() in ('DEPT', 'DEPTH', 'MD', 'TVD', 'TVDSS'):
            well.depth_col = col
            break
    if well.depth_col is None:
        well.depth_col = df.columns[0]
    return well


# ─────────────────────────────────────────────
#  CANVAS WRAPPER
# ─────────────────────────────────────────────
class PlotCanvas(QWidget):
    def __init__(self, parent=None, figsize=(12, 8)):
        super().__init__(parent)
        self.fig = Figure(figsize=figsize, facecolor=DARK_BG, tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet(f"background:{PANEL_BG}; color:{TEXT_LIGHT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def clear(self):
        self.fig.clear()
        self.canvas.draw()


# ─────────────────────────────────────────────
#  WELL EXPLORER (left tree)
# ─────────────────────────────────────────────
class WellExplorer(QDockWidget):
    well_selected   = pyqtSignal(object)       # WellData
    curve_selected  = pyqtSignal(object, str)  # WellData, curve

    def __init__(self, parent=None):
        super().__init__("Well Explorer", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.wells = {}   # name -> WellData

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        # buttons
        btn_row = QHBoxLayout()
        self.btn_load_las = QPushButton("+ LAS")
        self.btn_load_csv = QPushButton("+ CSV")
        self.btn_remove   = QPushButton("Remove")
        self.btn_remove.setObjectName("secondary")
        btn_row.addWidget(self.btn_load_las)
        btn_row.addWidget(self.btn_load_csv)
        btn_row.addWidget(self.btn_remove)
        layout.addLayout(btn_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Unit"])
        self.tree.setColumnWidth(0, 160)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

        self.setWidget(container)

        self.btn_load_las.clicked.connect(lambda: parent.load_file('las') if parent else None)
        self.btn_load_csv.clicked.connect(lambda: parent.load_file('csv') if parent else None)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.tree.itemClicked.connect(self._on_item_click)

    def add_well(self, well: WellData):
        self.wells[well.name] = well
        root = QTreeWidgetItem(self.tree, [well.name, ""])
        root.setData(0, Qt.UserRole, ('well', well.name))
        root.setForeground(0, QColor(ACCENT))
        root.setFont(0, QFont("Segoe UI", 9, QFont.Bold))

        # Depth info
        if well.depth_col:
            d = well.df[well.depth_col].dropna()
            if len(d):
                info = QTreeWidgetItem(root, [f"  Depth: {d.min():.1f}–{d.max():.1f}", "m"])
                info.setForeground(0, QColor(TEXT_DIM))

        # Curves group
        curves_node = QTreeWidgetItem(root, ["📊 Curves", ""])
        curves_node.setForeground(0, QColor(TEXT_DIM))
        for i, col in enumerate(well.curve_names):
            if col == well.depth_col:
                continue
            unit = well.curves.get(col, {}).get('unit', '')
            child = QTreeWidgetItem(curves_node, [f"  {col}", unit])
            child.setData(0, Qt.UserRole, ('curve', well.name, col))
            child.setForeground(0, QColor(TRACK_COLORS[i % len(TRACK_COLORS)]))

        root.setExpanded(True)
        curves_node.setExpanded(True)

    def rebuild_tree(self):
        wells = list(self.wells.values())
        self.tree.clear()
        self.wells = {}
        for well in wells:
            self.add_well(well)

    def remove_selected(self):
        items = self.tree.selectedItems()
        if not items:
            return
        item = items[0]
        data = item.data(0, Qt.UserRole)
        if data and data[0] == 'well':
            wname = data[1]
            self.wells.pop(wname, None)
            idx = self.tree.indexOfTopLevelItem(item)
            self.tree.takeTopLevelItem(idx)

    def _on_item_click(self, item, col):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        if data[0] == 'well':
            well = self.wells.get(data[1])
            if well:
                self.well_selected.emit(well)
        elif data[0] == 'curve':
            well = self.wells.get(data[1])
            if well:
                self.curve_selected.emit(well, data[2])


# ─────────────────────────────────────────────
#  HEADER INFO TAB
# ─────────────────────────────────────────────
class HeaderTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Mnemonic", "Value", "Unit", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(QLabel("Well Header Information"), )
        layout.addWidget(self.table)

    def load(self, well: WellData):
        self.table.setRowCount(0)
        if not well.header:
            # CSV – show basic info
            rows = [
                ("WELL", well.name, "", "Well Name"),
                ("FILE", well.filename, "", "Source File"),
                ("CURVES", str(len(well.curve_names)), "", "Number of curves"),
                ("DEPTH", well.depth_col, "", "Depth column"),
            ]
            if well.depth_col and well.depth_col in well.df:
                d = well.df[well.depth_col].dropna()
                rows += [
                    ("STRT", f"{d.min():.2f}", "m", "Start Depth"),
                    ("STOP", f"{d.max():.2f}", "m", "Stop Depth"),
                    ("STEP", f"{(d.max()-d.min())/max(len(d)-1,1):.4f}", "m", "Step"),
                ]
        else:
            rows = [(k, str(v['value']), v['unit'], v['desc'])
                    for k, v in well.header.items()]
        self.table.setRowCount(len(rows))
        for r, (m, val, unit, desc) in enumerate(rows):
            for c, txt in enumerate([m, val, unit, desc]):
                item = QTableWidgetItem(str(txt))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(r, c, item)


# ─────────────────────────────────────────────
#  STATISTICS TAB
# ─────────────────────────────────────────────
class StatsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Well Log Statistics"), )
        layout.addWidget(self.table)

    def load(self, well: WellData):
        if well.df.empty:
            return
        stats_df = well.df.describe().T.round(4)
        self.table.setRowCount(len(stats_df))
        self.table.setColumnCount(len(stats_df.columns))
        self.table.setHorizontalHeaderLabels(list(stats_df.columns))
        self.table.setVerticalHeaderLabels(list(stats_df.index))
        for r, row in enumerate(stats_df.values):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                if r % 2 == 0:
                    item.setForeground(QColor(ACCENT))
                self.table.setItem(r, c, item)


# ─────────────────────────────────────────────
#  RAW DATA TAB
# ─────────────────────────────────────────────
class DataTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.table)

    def load(self, well: WellData):
        df = well.df.head(500)
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))
        for r, row in df.iterrows():
            for c, val in enumerate(row):
                item = QTableWidgetItem("" if pd.isna(val) else f"{val:.4g}" if isinstance(val, float) else str(val))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(r - df.index[0], c, item)


# ─────────────────────────────────────────────
#  MULTI-TRACK PLOT
# ─────────────────────────────────────────────
class MultiTrackPlot(PlotCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, figsize=(14, 10))

    def plot(self, well: WellData, selected_curves=None, depth_range=None):
        self.fig.clear()
        if well.df.empty or well.depth_col is None:
            self.canvas.draw()
            return

        depth = well.df[well.depth_col].values
        curves = selected_curves or [c for c in well.curve_names if c != well.depth_col]
        curves = curves[:10]
        if not curves:
            return

        n = len(curves)
        axes = self.fig.subplots(1, n, sharey=True)
        if n == 1:
            axes = [axes]
        self.fig.subplots_adjust(wspace=0.05, left=0.06, right=0.99, top=0.92, bottom=0.05)

        if depth_range:
            mask = (depth >= depth_range[0]) & (depth <= depth_range[1])
        else:
            mask = np.ones(len(depth), dtype=bool)

        d = depth[mask]
        self.fig.suptitle(f"Multi-Track Log  |  {well.name}", color=ACCENT,
                          fontsize=fs(11), fontweight='bold')

        for i, (ax, curve) in enumerate(zip(axes, curves)):
            if curve not in well.df.columns:
                continue
            vals = well.df[curve].values[mask]
            color = TRACK_COLORS[i % len(TRACK_COLORS)]
            valid = ~np.isnan(vals)
            ax.plot(vals[valid], d[valid], color=color, linewidth=0.8, label=curve)
            ax.invert_yaxis()
            ax.set_title(curve, color=color, fontsize=fs(8), fontweight='bold', pad=2)
            ax.tick_params(axis='x', labelsize=fs(6), colors=TEXT_DIM)
            ax.tick_params(axis='y', labelsize=fs(6), colors=TEXT_DIM)
            ax.set_facecolor(PANEL_BG)
            ax.xaxis.set_label_position('top')
            ax.xaxis.tick_top()
            unit = well.curves.get(curve, {}).get('unit', '')
            xlabel = f"{curve} [{unit}]" if unit else curve
            ax.set_xlabel(xlabel, fontsize=fs(6), color=TEXT_DIM)
            if i == 0:
                ax.set_ylabel("Depth (m)", color=TEXT_DIM, fontsize=fs(8))
            # shade fill
            x_min = np.nanmin(vals) if valid.any() else 0
            ax.fill_betweenx(d[valid], x_min, vals[valid], alpha=0.15, color=color)

        self.canvas.draw()


# ─────────────────────────────────────────────
#  TRIPLE COMBO PLOT  (GR | Resistivity | Porosity)
# ─────────────────────────────────────────────
TRIPLE_PRESETS = {
    'GR': ['GR', 'GAMMARAY', 'GRC', 'GR_EDTC'],
    'SP': ['SP'],
    'CAL': ['CAL', 'CALI'],
    'VSH': ['VSH', 'VCL'],
    'RES_DEEP': ['LLD', 'RT', 'RILD', 'RD', 'ILD', 'RDEEP', 'RES_DEEP'],
    'RES_SHA': ['LLS', 'RFOC', 'RS', 'ILS', 'RSHA', 'MSFL', 'RXO'],
    'RHOB': ['RHOB', 'RHOZ', 'DEN', 'DENSITY'],
    'NPHI': ['NPHI', 'TNPH', 'CNL'],
    'DT': ['DT', 'DTCO', 'AC', 'DTC'],
    'SW': ['SW', 'SWT', 'SWE'],
}

def find_curve(well, keys):
    cols_up = {c.upper(): c for c in well.curve_names}
    for k in keys:
        if k.upper() in cols_up:
            return cols_up[k.upper()]
    return None

class TripleComboPlot(PlotCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, figsize=(14, 10))

    def plot(self, well: WellData, depth_range=None):
        self.fig.clear()
        if well.df.empty:
            self.canvas.draw()
            return

        depth = well.df[well.depth_col].values
        if depth_range:
            mask = (depth >= depth_range[0]) & (depth <= depth_range[1])
        else:
            mask = np.ones(len(depth), dtype=bool)
        d = depth[mask]

        gs = gridspec.GridSpec(1, 3, figure=self.fig, wspace=0.08,
                               left=0.07, right=0.99, top=0.90, bottom=0.05)

        self.fig.suptitle(f"Triple Combo  |  {well.name}", color=ACCENT,
                          fontsize=fs(11), fontweight='bold')

        axes = [self.fig.add_subplot(gs[0, i]) for i in range(3)]
        for ax in axes:
            ax.set_facecolor(PANEL_BG)
            ax.invert_yaxis()
            ax.tick_params(axis='x', labelsize=fs(6), colors=TEXT_DIM)
            ax.tick_params(axis='y', labelsize=fs(6), colors=TEXT_DIM)
            ax.xaxis.set_label_position('top')
            ax.xaxis.tick_top()
            ax.grid(True, axis='x', color=GRID_CLR, linewidth=0.5, alpha=0.8)

        # ---- Track 0 : GR
        gr_curve = self._plot_curve(axes[0], well, d, mask, 'GR', "#00a83b", fill=False, label="GR")
        if gr_curve:
            g = well.df[gr_curve].values[mask]
            g = g[np.isfinite(g)]
            if len(g):
                lo, hi = self._padded_limits(g, default=(0, 200), hard=(0, None))
                axes[0].set_xlim(lo, hi)
            unit = well.curves.get(gr_curve, {}).get('unit', 'API') or 'API'
            axes[0].set_xlabel(f"{gr_curve} ({unit})", color="#00a83b", fontsize=fs(7))
        else:
            axes[0].set_xlabel("GR (API)", color="#00a83b", fontsize=fs(7))
        axes[0].set_title("Correlation", color=TEXT_LIGHT, fontsize=fs(8), pad=2)
        axes[0].set_ylabel("Depth (m)", color=TEXT_DIM, fontsize=fs(8))

        # ---- Track 1 : Resistivity
        res_deep = find_curve(well, TRIPLE_PRESETS['RES_DEEP'])
        res_sha = find_curve(well, TRIPLE_PRESETS['RES_SHA'])
        for curve, color in ((res_deep, "#f44336"), (res_sha, "#1e88e5")):
            if not curve:
                continue
            vals = well.df[curve].values[mask]
            valid = np.isfinite(vals) & (vals > 0)
            if valid.any():
                axes[1].plot(vals[valid], d[valid], color=color, linewidth=0.9, label=curve)
        axes[1].set_xscale('log')
        res_vals = []
        for curve in (res_deep, res_sha):
            if curve:
                v = well.df[curve].values[mask]
                v = v[np.isfinite(v) & (v > 0)]
                if len(v):
                    res_vals.append(v)
        if res_vals:
            merged = np.concatenate(res_vals)
            lo = max(0.2, float(np.nanpercentile(merged, 2)))
            hi = max(lo * 10.0, float(np.nanpercentile(merged, 98)))
            axes[1].set_xlim(lo, hi)
        else:
            axes[1].set_xlim(0.2, 200)
        axes[1].set_title("Resistivity", color=TEXT_LIGHT, fontsize=fs(8), pad=2)
        axes[1].set_xlabel("RT (ohm.m)", color="#f44336", fontsize=fs(7))

        # ---- Track 2 : Nuclear (RHOB + NPHI with independent x-axes)
        nphi_ax = None
        rhob_curve = self._plot_curve(axes[2], well, d, mask, 'RHOB', "#e53935", label="RHOB", fill=False)
        if rhob_curve:
            rv = well.df[rhob_curve].values[mask]
            rv = rv[np.isfinite(rv)]
            if len(rv):
                lo, hi = self._padded_limits(rv, default=(1.95, 2.95), hard=(None, None))
                axes[2].set_xlim(lo, hi)
            unit = well.curves.get(rhob_curve, {}).get('unit', 'g/cc') or 'g/cc'
            axes[2].set_xlabel(f"{rhob_curve} ({unit})", color="#e53935", fontsize=fs(7))
        else:
            axes[2].set_xlabel("RHOB (g/cc)", color="#e53935", fontsize=fs(7))

        nphi_curve = find_curve(well, TRIPLE_PRESETS['NPHI'])
        if nphi_curve:
            nphi_ax = axes[2].twiny()
            nphi_ax.set_facecolor('none')
            nphi_ax.set_ylim(axes[2].get_ylim())
            nphi_ax.xaxis.set_label_position('top')
            nphi_ax.xaxis.tick_top()
            nphi_ax.spines['top'].set_position(('outward', 16))
            nphi_ax.tick_params(axis='x', labelsize=fs(6), colors="#5e35b1")

            nv = well.df[nphi_curve].values[mask]
            valid = np.isfinite(nv)
            if valid.any():
                nphi_ax.plot(nv[valid], d[valid], color="#5e35b1", linewidth=0.9, linestyle='--', label=nphi_curve)
                # Typical neutron axis is reversed left->right
                n_lo, n_hi = self._padded_limits(nv[valid], default=(-0.15, 0.45), hard=(None, None))
                nphi_ax.set_xlim(max(n_hi, n_lo), min(n_hi, n_lo))
            else:
                nphi_ax.set_xlim(0.45, -0.15)
            unit = well.curves.get(nphi_curve, {}).get('unit', 'dec') or 'dec'
            nphi_ax.set_xlabel(f"{nphi_curve} ({unit})", color="#5e35b1", fontsize=fs(7))

            if rhob_curve:
                r = well.df[rhob_curve].values[mask]
                good = np.isfinite(r) & np.isfinite(nv)
                if good.any():
                    # Visual crossover fill between RHOB and NPHI in RHOB axis domain.
                    nr = np.interp(nv[good], [nphi_ax.get_xlim()[1], nphi_ax.get_xlim()[0]], axes[2].get_xlim())
                    axes[2].fill_betweenx(d[good], r[good], nr, where=(r[good] > nr), color="#ffeb3b", alpha=0.28)

        axes[2].set_title("Nuclear", color=TEXT_LIGHT, fontsize=fs(8), pad=2)

        for ax in axes[:2]:
            if ax.lines:
                ax.legend(loc='best', fontsize=fs(6), framealpha=0.85)
        h, l = axes[2].get_legend_handles_labels()
        if nphi_ax is not None:
            h2, l2 = nphi_ax.get_legend_handles_labels()
            h.extend(h2)
            l.extend(l2)
        if h:
            axes[2].legend(h, l, loc='best', fontsize=fs(6), framealpha=0.85)

        self.canvas.draw()

    def _plot_curve(self, ax, well, d, mask, preset_key, color, log=False, fill=False, label=None):
        c = find_curve(well, TRIPLE_PRESETS.get(preset_key, [preset_key]))
        if c is None:
            return
        v = well.df[c].values[mask]
        valid = ~np.isnan(v)
        if not valid.any():
            return
        ax.plot(v[valid], d[valid], color=color, linewidth=0.8, label=label or c)
        if fill:
            xmin = np.nanmin(v)
            ax.fill_betweenx(d[valid], xmin, v[valid], alpha=0.15, color=color)
        return c

    def _padded_limits(self, vals, default=(0.0, 1.0), hard=(None, None)):
        vals = np.asarray(vals, dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            return default
        lo = float(np.nanpercentile(vals, 2))
        hi = float(np.nanpercentile(vals, 98))
        if lo == hi:
            lo -= 0.5
            hi += 0.5
        pad = (hi - lo) * 0.08
        lo -= pad
        hi += pad
        if hard[0] is not None:
            lo = max(hard[0], lo)
        if hard[1] is not None:
            hi = min(hard[1], hi)
        return lo, hi


# ─────────────────────────────────────────────
#  HISTOGRAM PLOT
# ─────────────────────────────────────────────
class HistogramPlot(PlotCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, figsize=(10, 7))

    def plot(self, well: WellData, curve: str, bins=50, log_scale=False):
        self.fig.clear()
        if curve not in well.df.columns:
            self.canvas.draw()
            return

        vals = well.df[curve].dropna().values
        ax = self.fig.add_subplot(111)
        color = TRACK_COLORS[0]

        n, bins_out, patches = ax.hist(vals, bins=bins, color=color, alpha=0.75,
                                        edgecolor=DARK_BG, linewidth=0.5)
        # KDE
        if len(vals) > 5:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(vals)
            xs = np.linspace(vals.min(), vals.max(), 300)
            ax2 = ax.twinx()
            ax2.plot(xs, kde(xs), color=ACCENT2, linewidth=1.5, label='KDE')
            ax2.set_ylabel("Density", color=ACCENT2, fontsize=fs(9))
            ax2.tick_params(axis='y', colors=ACCENT2, labelsize=fs(7))
            ax2.set_facecolor(PANEL_BG)

        if log_scale:
            ax.set_yscale('log')

        ax.tick_params(axis='both', labelsize=fs(8), colors=TEXT_DIM)
        unit = well.curves.get(curve, {}).get('unit', '')
        ax.set_xlabel(f"{curve}  [{unit}]" if unit else curve, color=TEXT_LIGHT, fontsize=fs(10))
        ax.set_ylabel("Count", color=TEXT_LIGHT, fontsize=fs(10))
        ax.set_title(f"Histogram  –  {curve}  |  {well.name}", color=ACCENT,
                     fontsize=fs(11), fontweight='bold')

        # Stats annotation
        txt = (f"n = {len(vals):,}\n"
               f"μ = {np.mean(vals):.4g}\n"
               f"σ = {np.std(vals):.4g}\n"
               f"P10 = {np.percentile(vals,10):.4g}\n"
               f"P50 = {np.percentile(vals,50):.4g}\n"
               f"P90 = {np.percentile(vals,90):.4g}")
        ax.text(0.98, 0.97, txt, transform=ax.transAxes, fontsize=fs(8),
                verticalalignment='top', horizontalalignment='right',
                color=TEXT_LIGHT,
                bbox=dict(facecolor=DARK_BG, alpha=0.8, edgecolor=GRID_CLR, boxstyle='round'))
        self.canvas.draw()


# ─────────────────────────────────────────────
#  CROSS PLOT
# ─────────────────────────────────────────────
class CrossPlot(PlotCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, figsize=(9, 8))

    def plot(self, well: WellData, x_curve: str, y_curve: str,
             color_curve: str = None, size_curve: str = None):
        self.fig.clear()
        df = well.df[[c for c in [x_curve, y_curve, color_curve, size_curve,
                                   well.depth_col]
                       if c and c in well.df.columns]].dropna(subset=[x_curve, y_curve])
        if df.empty:
            self.canvas.draw()
            return

        ax = self.fig.add_subplot(111)
        x = df[x_curve].values
        y = df[y_curve].values
        ax.tick_params(axis='both', labelsize=fs(8), colors=TEXT_DIM)

        c_vals = df[color_curve].values if color_curve and color_curve in df else None
        s_vals = None
        if size_curve and size_curve in df:
            sv = df[size_curve].values
            sv = (sv - sv.min()) / (sv.max() - sv.min() + 1e-9) * 40 + 5
            s_vals = sv

        scatter = ax.scatter(x, y, c=c_vals if c_vals is not None else ACCENT,
                             s=s_vals if s_vals is not None else 8,
                             cmap='rainbow', alpha=0.6, linewidths=0,
                             vmin=np.nanmin(c_vals) if c_vals is not None else None,
                             vmax=np.nanmax(c_vals) if c_vals is not None else None)

        if c_vals is not None:
            cb = self.fig.colorbar(scatter, ax=ax, pad=0.01)
            cb.set_label(color_curve, color=TEXT_LIGHT, fontsize=fs(8))
            cb.ax.yaxis.set_tick_params(color=TEXT_DIM, labelsize=fs(7))
            plt.setp(cb.ax.yaxis.get_ticklabels(), color=TEXT_DIM)

        # regression line
        if len(x) > 2:
            slope, intercept, r, p, _ = stats.linregress(x, y)
            xs = np.linspace(x.min(), x.max(), 100)
            ax.plot(xs, slope * xs + intercept, color=ACCENT2, linewidth=1.5,
                    linestyle='--', label=f'R²={r**2:.3f}')
            ax.legend(fontsize=fs(8))

        ux = well.curves.get(x_curve, {}).get('unit', '')
        uy = well.curves.get(y_curve, {}).get('unit', '')
        ax.set_xlabel(f"{x_curve}  [{ux}]" if ux else x_curve, color=TEXT_LIGHT, fontsize=fs(10))
        ax.set_ylabel(f"{y_curve}  [{uy}]" if uy else y_curve, color=TEXT_LIGHT, fontsize=fs(10))
        ax.set_title(f"Cross Plot  {x_curve} vs {y_curve}  |  {well.name}",
                     color=ACCENT, fontsize=fs(11), fontweight='bold')
        self.canvas.draw()


# ─────────────────────────────────────────────
#  CONTROL PANELS (right dock)
# ─────────────────────────────────────────────
class MultiTrackControls(QWidget):
    plot_requested = pyqtSignal(list, tuple)   # curves, depth_range

    def __init__(self, well=None):
        super().__init__()
        self.well = well
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        g = QGroupBox("Curve Selection")
        gl = QVBoxLayout(g)
        self.curve_list = QListWidget()
        self.curve_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.curve_list.setMaximumHeight(220)
        gl.addWidget(self.curve_list)
        layout.addWidget(g)

        g2 = QGroupBox("Depth Range")
        g2l = QFormLayout(g2)
        self.depth_min = QDoubleSpinBox(); self.depth_min.setRange(-99999, 99999); self.depth_min.setDecimals(1)
        self.depth_max = QDoubleSpinBox(); self.depth_max.setRange(-99999, 99999); self.depth_max.setDecimals(1)
        self.depth_max.setValue(99999)
        g2l.addRow("Min Depth:", self.depth_min)
        g2l.addRow("Max Depth:", self.depth_max)
        layout.addWidget(g2)

        btn = QPushButton("▶  Plot Tracks")
        btn.clicked.connect(self._emit)
        layout.addWidget(btn)
        layout.addStretch()

    def set_well(self, well):
        self.well = well
        self.curve_list.clear()
        if well:
            for c in well.curve_names:
                if c != well.depth_col:
                    self.curve_list.addItem(c)
            if well.depth_col and well.depth_col in well.df:
                d = well.df[well.depth_col].dropna()
                self.depth_min.setValue(float(d.min()))
                self.depth_max.setValue(float(d.max()))

    def _emit(self):
        selected = [item.text() for item in self.curve_list.selectedItems()]
        if not selected and self.well:
            selected = [c for c in self.well.curve_names
                        if c != self.well.depth_col][:8]
        self.plot_requested.emit(selected, (self.depth_min.value(), self.depth_max.value()))


class HistogramControls(QWidget):
    plot_requested = pyqtSignal(str, int, bool)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        g = QGroupBox("Histogram Settings")
        gl = QFormLayout(g)
        self.curve_cb = QComboBox()
        self.bins_sb  = QSpinBox(); self.bins_sb.setRange(5, 500); self.bins_sb.setValue(50)
        self.log_cb   = QCheckBox("Log Y-scale")
        gl.addRow("Curve:", self.curve_cb)
        gl.addRow("Bins:", self.bins_sb)
        gl.addRow("", self.log_cb)
        layout.addWidget(g)

        btn = QPushButton("▶  Plot Histogram")
        btn.clicked.connect(self._emit)
        layout.addWidget(btn)
        layout.addStretch()

    def set_well(self, well):
        self.curve_cb.clear()
        if well:
            for c in well.curve_names:
                if c != well.depth_col:
                    self.curve_cb.addItem(c)

    def _emit(self):
        self.plot_requested.emit(self.curve_cb.currentText(),
                                  self.bins_sb.value(),
                                  self.log_cb.isChecked())


class CrossPlotControls(QWidget):
    plot_requested = pyqtSignal(str, str, str, str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        g = QGroupBox("Cross Plot Settings")
        gl = QFormLayout(g)
        self.x_cb   = QComboBox()
        self.y_cb   = QComboBox()
        self.col_cb = QComboBox()
        self.col_cb.addItem("None")
        self.sz_cb  = QComboBox()
        self.sz_cb.addItem("None")
        gl.addRow("X Axis:", self.x_cb)
        gl.addRow("Y Axis:", self.y_cb)
        gl.addRow("Color by:", self.col_cb)
        gl.addRow("Size by:", self.sz_cb)
        layout.addWidget(g)

        btn = QPushButton("▶  Plot Cross Plot")
        btn.clicked.connect(self._emit)
        layout.addWidget(btn)
        layout.addStretch()

    def set_well(self, well):
        for cb in (self.x_cb, self.y_cb, self.col_cb, self.sz_cb):
            cb.clear()
        self.col_cb.addItem("None")
        self.sz_cb.addItem("None")
        if well:
            curves = [c for c in well.curve_names if c != well.depth_col]
            for c in curves:
                self.x_cb.addItem(c)
                self.y_cb.addItem(c)
                self.col_cb.addItem(c)
                self.sz_cb.addItem(c)
            if len(curves) >= 2:
                self.y_cb.setCurrentIndex(1)

    def _emit(self):
        col = self.col_cb.currentText()
        sz  = self.sz_cb.currentText()
        self.plot_requested.emit(
            self.x_cb.currentText(),
            self.y_cb.currentText(),
            "" if col == "None" else col,
            "" if sz  == "None" else sz
        )


# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
class WellLogViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Well Log Viewer  –  Petrophysics Analysis")
        self.resize(1440, 900)
        self.setStyleSheet(STYLESHEET)
        self.current_well = None
        self._build_ui()

    # ── build ─────────────────────────────────
    def _build_ui(self):
        # Menu
        self._build_menu()

        # Toolbar
        self._build_toolbar()

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready  –  Load a LAS or CSV file to begin")

        # Left dock – Well Explorer
        self.explorer = WellExplorer(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.explorer)
        self.explorer.well_selected.connect(self._on_well_selected)

        # Right dock – Controls
        self.ctrl_dock = QDockWidget("Plot Controls", self)
        self.ctrl_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.ctrl_widget = QWidget()
        self.ctrl_layout = QVBoxLayout(self.ctrl_widget)
        self.ctrl_layout.setContentsMargins(0, 0, 0, 0)
        self.ctrl_dock.setWidget(self.ctrl_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ctrl_dock)

        # Central tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # ── Tabs ──
        # 1. Header
        self.header_tab = HeaderTab()
        self.tabs.addTab(self.header_tab, "📋 Header")

        # 2. Statistics
        self.stats_tab = StatsTab()
        self.tabs.addTab(self.stats_tab, "📊 Statistics")

        # 3. Data table
        self.data_tab = DataTab()
        self.tabs.addTab(self.data_tab, "🗃 Raw Data")

        # 4. Multi-track
        self.track_canvas = MultiTrackPlot()
        self.tabs.addTab(self.track_canvas, "📈 Multi-Track")

        # 5. Triple Combo
        self.triple_canvas = TripleComboPlot()
        self.tabs.addTab(self.triple_canvas, "🔗 Triple Combo")

        # 6. Histogram
        self.hist_canvas = HistogramPlot()
        self.tabs.addTab(self.hist_canvas, "📉 Histogram")

        # 7. Cross Plot
        self.xplot_canvas = CrossPlot()
        self.tabs.addTab(self.xplot_canvas, "✖ Cross Plot")

        # Controls per tab
        self.track_ctrl = MultiTrackControls()
        self.hist_ctrl  = HistogramControls()
        self.xplot_ctrl = CrossPlotControls()
        for w in (self.track_ctrl, self.hist_ctrl, self.xplot_ctrl):
            self.ctrl_layout.addWidget(w)
            w.hide()

        self.tabs.currentChanged.connect(self._tab_changed)
        self._tab_changed(0)

        # wire controls
        self.track_ctrl.plot_requested.connect(self._plot_multitrack)
        self.hist_ctrl.plot_requested.connect(self._plot_histogram)
        self.xplot_ctrl.plot_requested.connect(self._plot_crossplot)

    # ── menu ──────────────────────────────────
    def _build_menu(self):
        mb = self.menuBar()
        fm = mb.addMenu("&File")
        fm.addAction("Load LAS File…",   lambda: self.load_file('las'), "Ctrl+O")
        fm.addAction("Load CSV File…",   lambda: self.load_file('csv'), "Ctrl+Shift+O")
        fm.addSeparator()
        fm.addAction("Export Plot…",     self._export_plot, "Ctrl+S")
        fm.addSeparator()
        fm.addAction("Exit",             self.close, "Ctrl+Q")

        vm = mb.addMenu("&View")
        vm.addAction("Well Explorer",    lambda: self.explorer.show())
        vm.addAction("Plot Controls",    lambda: self.ctrl_dock.show())

        wm = mb.addMenu("&Window")
        wm.addAction("Minimize", self._minimize_window, "Ctrl+M")
        wm.addAction("Maximize", self._maximize_window)
        wm.addAction("Restore", self._restore_window)
        wm.addAction("Toggle Full Screen", self._toggle_fullscreen, "F11")

        # Facies classification workflows
        facies_menu = mb.addMenu("&Facies")
        facies_menu.addAction("Run Facies Classification", self._run_facies)
        facies_menu.addAction("Supervised Classification", self._supervised_facies)
        facies_menu.addAction("Unsupervised Classification", self._unsupervised_facies)
        facies_menu.addSeparator()

        hm = mb.addMenu("&Help")
        hm.addAction("About",            self._about)

    # ── toolbar ───────────────────────────────
    def _build_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setIconSize(QSize(24, 24))
        self.addToolBar(tb)

        def _btn(label, tip, slot):
            a = QAction(label, self)
            a.setStatusTip(tip)
            a.triggered.connect(slot)
            tb.addAction(a)
            return a

        _btn("📂 LAS",  "Load LAS file",  lambda: self.load_file('las'))
        _btn("📂 CSV",  "Load CSV file",  lambda: self.load_file('csv'))
        tb.addSeparator()
        _btn("📈 Multi-Track",   "Multi-track plot",   lambda: self.tabs.setCurrentIndex(3))
        _btn("🔗 Triple Combo",  "Triple combo plot",  lambda: self.tabs.setCurrentIndex(4))
        _btn("📉 Histogram",     "Histogram",          lambda: self.tabs.setCurrentIndex(5))
        _btn("✖ Cross Plot",    "Cross plot",          lambda: self.tabs.setCurrentIndex(6))
        tb.addSeparator()
        _btn("💾 Export",   "Export current plot",  self._export_plot)
        tb.addSeparator()
        _btn("🗕 Min", "Minimize window", self._minimize_window)
        _btn("🗖 Max", "Maximize window", self._maximize_window)
        _btn("🗗 Restore", "Restore window", self._restore_window)
        _btn("⛶ Full", "Toggle full screen", self._toggle_fullscreen)

    # ── slots ──────────────────────────────────
    def load_file(self, fmt='las'):
        if fmt == 'las':
            path, _ = QFileDialog.getOpenFileName(
                self, "Open LAS File", "", "LAS Files (*.las *.LAS);;All Files (*)")
            if not path: return
            try:
                well = load_las(path)
            except ImportError:
                QMessageBox.warning(self, "Missing library",
                    "lasio is not installed.\n\nRun:  pip install lasio")
                return
            except Exception as e:
                QMessageBox.critical(self, "Error loading LAS", str(e))
                return
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Open CSV File", "", "CSV Files (*.csv *.txt);;All Files (*)")
            if not path: return
            try:
                well = load_csv(path)
            except Exception as e:
                QMessageBox.critical(self, "Error loading CSV", str(e))
                return

        self.explorer.add_well(well)
        self._on_well_selected(well)
        self.status.showMessage(f"Loaded: {well.name}  ({len(well.curve_names)} curves, "
                                f"{len(well.df)} samples)")

    def _on_well_selected(self, well: WellData):
        self.current_well = well
        self.header_tab.load(well)
        self.stats_tab.load(well)
        self.data_tab.load(well)
        self.track_ctrl.set_well(well)
        self.hist_ctrl.set_well(well)
        self.xplot_ctrl.set_well(well)

        # auto-plot current tab
        idx = self.tabs.currentIndex()
        if idx == 3:
            self._plot_multitrack([], (None, None))
        elif idx == 4:
            self.triple_canvas.plot(well)
        self.status.showMessage(f"Active well: {well.name}")

    def _tab_changed(self, idx):
        for w in (self.track_ctrl, self.hist_ctrl, self.xplot_ctrl):
            w.hide()
        if idx == 3:
            self.track_ctrl.show()
        elif idx == 4:
            # triple combo – auto plot
            if self.current_well:
                self.triple_canvas.plot(self.current_well)
        elif idx == 5:
            self.hist_ctrl.show()
        elif idx == 6:
            self.xplot_ctrl.show()

    def _plot_multitrack(self, curves, depth_range):
        if not self.current_well:
            return
        dr = depth_range if depth_range and depth_range[0] < depth_range[1] else None
        self.track_canvas.plot(self.current_well, curves or None, dr)

    def _plot_histogram(self, curve, bins, log_scale):
        if not self.current_well or not curve:
            return
        self.hist_canvas.plot(self.current_well, curve, bins, log_scale)

    def _plot_crossplot(self, x, y, col, sz):
        if not self.current_well or not x or not y:
            return
        self.xplot_canvas.plot(self.current_well, x, y,
                                col or None, sz or None)

    def _ensure_active_well(self, action_name):
        if self.current_well is not None:
            return True
        QMessageBox.warning(self, action_name, "Load a LAS or CSV well before running facies classification.")
        return False

    def _refresh_current_well_views(self):
        if not self.current_well:
            return
        self.explorer.rebuild_tree()
        self._on_well_selected(self.current_well)

    def _format_facies_mapping(self, label_mapping):
        if not label_mapping:
            return ""
        entries = [f"{code}={label}" for code, label in label_mapping.items()]
        if len(entries) > 8:
            entries = entries[:8] + ["..."]
        return "\nCode mapping: " + ", ".join(entries)

    def _run_facies(self):
        if not self._ensure_active_well("Facies Classification"):
            return

        chooser = QMessageBox(self)
        chooser.setWindowTitle("Facies Classification")
        chooser.setText("Choose the facies-classification workflow to run.")
        supervised_btn = chooser.addButton("Supervised", QMessageBox.AcceptRole)
        unsupervised_btn = chooser.addButton("Unsupervised", QMessageBox.AcceptRole)
        chooser.addButton(QMessageBox.Cancel)
        chooser.exec_()

        clicked = chooser.clickedButton()
        if clicked is supervised_btn:
            self._supervised_facies()
        elif clicked is unsupervised_btn:
            self._unsupervised_facies()

    def _supervised_facies(self):
        if not self._ensure_active_well("Supervised Classification"):
            return

        from gui.facies_supervised import SupervisedFaciesDialog

        dialog = SupervisedFaciesDialog(self.current_well, self)
        if dialog.exec_() != QDialog.Accepted:
            return

        result = dialog.get_result()
        if result is None:
            return

        self.current_well.df[result.output_column] = result.prediction_codes
        self.current_well.curves[result.output_column] = {
            'unit': 'class',
            'desc': f"Supervised facies codes generated with {result.model_name}",
        }
        self._refresh_current_well_views()
        self.status.showMessage(
            f"Created facies curve: {result.output_column} ({result.model_name})"
        )

        QMessageBox.information(
            self,
            "Supervised Classification Complete",
            (
                f"Output column: {result.output_column}\n"
                f"Method: {result.model_name}\n"
                f"Rows classified: {result.used_rows}\n"
                f"Training rows: {result.train_rows}\n"
                f"Validation rows: {result.validation_rows}\n"
                f"Train accuracy: {result.train_accuracy:.3f}\n"
                f"Validation accuracy: {result.validation_accuracy:.3f}"
                f"{self._format_facies_mapping(result.label_mapping)}"
            ),
        )

    def _unsupervised_facies(self):
        if not self._ensure_active_well("Unsupervised Classification"):
            return

        from gui.facies_unsupervised import UnsupervisedFaciesDialog

        dialog = UnsupervisedFaciesDialog(self.current_well, self)
        if dialog.exec_() != QDialog.Accepted:
            return

        result = dialog.get_result()
        if result is None:
            return

        self.current_well.df[result.output_column] = result.prediction_codes
        self.current_well.curves[result.output_column] = {
            'unit': 'class',
            'desc': f"Unsupervised facies codes generated with {result.model_name}",
        }
        self._refresh_current_well_views()
        self.status.showMessage(
            f"Created facies curve: {result.output_column} ({result.model_name})"
        )

        QMessageBox.information(
            self,
            "Unsupervised Classification Complete",
            (
                f"Output column: {result.output_column}\n"
                f"Method: {result.model_name}\n"
                f"Rows classified: {result.used_rows}\n"
                f"Clusters found: {result.cluster_count}\n"
                f"Noise samples: {result.noise_points}"
            ),
        )

    def _minimize_window(self):
        self.showMinimized()

    def _maximize_window(self):
        self.showMaximized()

    def _restore_window(self):
        self.showNormal()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _export_plot(self):
        idx = self.tabs.currentIndex()
        canvases = {3: self.track_canvas, 4: self.triple_canvas,
                    5: self.hist_canvas,  6: self.xplot_canvas}
        canvas = canvases.get(idx)
        if canvas is None:
            QMessageBox.information(self, "Export", "Switch to a plot tab first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Plot", "well_log_plot.png",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Vector (*.svg)")
        if path:
            canvas.fig.savefig(path, dpi=150, bbox_inches='tight')
            self.status.showMessage(f"Saved: {path}")

    def _about(self):
        QMessageBox.about(self, "Well Log Viewer",
            "<h2>Well Log Viewer</h2>"
            "<p>Professional Petrophysics Analysis Tool</p>"
            "<p><b>Features:</b><br>"
            "• Load LAS and CSV well log files<br>"
            "• Header / curve metadata viewer<br>"
            "• Statistical summary table<br>"
            "• Multi-track depth plot<br>"
            "• Triple combo plot (GR | RES | POR)<br>"
            "• Histogram with KDE<br>"
            "• Cross plot with regression<br>"
            "• Export plots as PNG / PDF / SVG</p>"
            "<p>Built with PyQt5 + Matplotlib + lasio</p>")


class WellDataWindow(WellLogViewer):
    """Compatibility wrapper used by SeisLab main window."""

    well_loaded = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        if parent is not None:
            self.setParent(parent, Qt.Window)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)

    def open_las_dialog(self):
        before = self.current_well.filename if self.current_well else ""
        self.load_file('las')
        after = self.current_well.filename if self.current_well else ""
        if after and after != before:
            self.well_loaded.emit(after)
            return True
        return False


# ─────────────────────────────────────────────
#  SAMPLE DATA GENERATOR  (for demo without a real file)
# ─────────────────────────────────────────────
def generate_demo_well() -> WellData:
    """Creates a synthetic well for demonstration."""
    np.random.seed(42)
    n = 1000
    depth = np.linspace(2000, 3000, n)

    # Fake lithology transitions
    vsh = np.clip(0.3 + 0.4 * np.sin(depth / 50) + 0.15 * np.random.randn(n), 0, 1)
    gr  = 20 + 120 * vsh + 5 * np.random.randn(n)
    nphi= np.clip(0.35 - 0.25 * vsh + 0.02 * np.random.randn(n), 0, 0.5)
    rhob= 2.1  + 0.7 * (1 - nphi) + 0.03 * np.random.randn(n)
    rt  = np.exp(2 + 3 * (1 - vsh) * nphi + 0.3 * np.random.randn(n))
    dt  = 190  - 90 * (1 - vsh) * (1 - nphi) + 3 * np.random.randn(n)
    sw  = np.clip(0.1 + 0.6 * vsh + 0.1 * np.random.randn(n), 0.05, 1.0)
    sp  = -80 + 60 * vsh + 3 * np.random.randn(n)
    cal = 8.5  + 0.5 * np.random.randn(n)

    df = pd.DataFrame({
        'DEPT': depth, 'GR': gr, 'SP': sp, 'CAL': cal,
        'VSH': vsh, 'LLD': rt, 'LLS': rt * 0.7,
        'RHOB': rhob, 'NPHI': nphi, 'DT': dt, 'SW': sw,
    })
    # add some NaN patches
    for col in ['RHOB', 'NPHI', 'LLD']:
        idx = np.random.choice(n, 30, replace=False)
        df.loc[idx, col] = np.nan

    well = WellData()
    well.name = "DEMO-WELL-1"
    well.filename = "synthetic"
    well.depth_col = "DEPT"
    well.df = df
    well.curves = {
        'GR':   {'unit': 'API', 'desc': 'Gamma Ray'},
        'SP':   {'unit': 'mV',  'desc': 'Spontaneous Potential'},
        'CAL':  {'unit': 'in',  'desc': 'Caliper'},
        'VSH':  {'unit': 'v/v', 'desc': 'Volume of Shale'},
        'LLD':  {'unit': 'ohm.m', 'desc': 'Deep Resistivity'},
        'LLS':  {'unit': 'ohm.m', 'desc': 'Shallow Resistivity'},
        'RHOB': {'unit': 'g/cc', 'desc': 'Bulk Density'},
        'NPHI': {'unit': 'v/v',  'desc': 'Neutron Porosity'},
        'DT':   {'unit': 'us/ft','desc': 'Sonic Travel Time'},
        'SW':   {'unit': 'v/v',  'desc': 'Water Saturation'},
    }
    return well


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Well Log Viewer")
    app.setStyle("Fusion")

    window = WellLogViewer()
    window.show()

    # Load demo well so the app is immediately usable
    demo = generate_demo_well()
    window.explorer.add_well(demo)
    window._on_well_selected(demo)
    window.triple_canvas.plot(demo)
    window.track_canvas.plot(demo, None, None)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
