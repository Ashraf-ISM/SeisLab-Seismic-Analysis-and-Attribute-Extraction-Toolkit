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
from scipy import stats

from PyQt5 import uic
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
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QPixmap

from gui.backend.well_data_models import (
    WellData, load_las, load_csv, detect_well_format, 
    available_curve_names, ensure_well_list, depth_limits_for_wells,
    summarize_well_names, apply_mpl_style,
    DARK_BG, PANEL_BG, ACCENT, ACCENT2, TEXT_LIGHT, TEXT_DIM, GRID_CLR, TRACK_COLORS, fs, STYLESHEET
)

apply_mpl_style()

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
class WellExplorer(QObject):
    well_selected   = pyqtSignal(object)       # WellData
    curve_selected  = pyqtSignal(object, str)  # WellData, curve
    well_removed    = pyqtSignal(str)          # well name

    def __init__(self, ui, parent=None):
        super().__init__()
        self.wells = {}   # name -> WellData
        self.ui = ui
        self.tree = ui.well_tree
        self.ui.btn_load_las.clicked.connect(lambda: parent.load_file('las') if parent else None)
        self.ui.btn_load_csv.clicked.connect(lambda: parent.load_file('csv') if parent else None)
        self.ui.btn_load_multi.clicked.connect(lambda: parent.load_file('mixed', multiple=True) if parent else None)
        self.ui.btn_remove.clicked.connect(self.remove_selected)
        self.tree.itemClicked.connect(self._on_item_click)

    def unique_well_name(self, name):
        base_name = (name or "").strip() or "Untitled Well"
        if base_name not in self.wells:
            return base_name

        suffix = 2
        while f"{base_name} ({suffix})" in self.wells:
            suffix += 1
        return f"{base_name} ({suffix})"

    # def add_well(self, well: WellData):
    #     self.wells[well.name] = well
    #     root = QTreeWidgetItem(self.tree, [well.name, ""])
    #     root.setData(0, Qt.UserRole, ('well', well.name))
    #     root.setForeground(0, QColor(ACCENT))
    #     root.setFont(0, QFont("Segoe UI", 9, QFont.Bold))

    #     # Depth info
    #     if well.depth_col:
    #         d = well.df[well.depth_col].dropna()
    #         if len(d):
    #             info = QTreeWidgetItem(root, [f"  Depth: {d.min():.1f}–{d.max():.1f}", "m"])
    #             info.setForeground(0, QColor(TEXT_DIM))
    def add_well(self, well: WellData):
        well.name = self.unique_well_name(well.name or os.path.basename(well.filename))

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
    
        # ── Curves group ──────────────────────────────────────────────────────────
        curves_node = QTreeWidgetItem(root, [""])
        curves_node.setForeground(0, QColor(TEXT_DIM))
    
        # Custom header widget for the curves node
        curves_header = QWidget()
        curves_header.setStyleSheet("background: transparent;")
        curves_layout = QHBoxLayout(curves_header)
        curves_layout.setContentsMargins(4, 6, 4, 6)
        curves_layout.setSpacing(8)
    
        # Icon label
        icon_lbl = QLabel("📊")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
        icon_lbl.setStyleSheet("background: transparent;")
    
        # Title label
        title_lbl = QLabel("Curves")
        title_lbl.setFont(QFont("Segoe UI Semibold", 13, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; letter-spacing: 1px;")
    
        # Count badge
        curve_count = sum(1 for col in well.curve_names if col != well.depth_col)
        badge_lbl = QLabel(f"  {curve_count}  ")
        badge_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        badge_lbl.setStyleSheet(
            "background: rgba(100,120,160,0.35);"
            "color: #aabbdd;"
            "border-radius: 8px;"
            "padding: 1px 4px;"
        )
    
        curves_layout.addWidget(icon_lbl)
        curves_layout.addWidget(title_lbl)
        curves_layout.addWidget(badge_lbl)
        curves_layout.addStretch()
    
        self.tree.setItemWidget(curves_node, 0, curves_header)
    
        # ── Individual curve children ─────────────────────────────────────────────
        for i, col in enumerate(well.curve_names):
            if col == well.depth_col:
                continue
    
            unit      = well.curves.get(col, {}).get('unit', '')
            col_color = TRACK_COLORS[i % len(TRACK_COLORS)]
    
            child = QTreeWidgetItem(curves_node, ["", unit])
            child.setData(0, Qt.UserRole, ('curve', well.name, col))
            child.setSizeHint(0, QSize(0, 32))
    
            # Unit column styling
            child.setFont(1, QFont("Consolas", 10))
            child.setForeground(1, QColor("#667799"))
    
            # Custom row widget: colour swatch + name
            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(10, 2, 4, 2)
            row_layout.setSpacing(8)
    
            # Colour swatch
            swatch = QLabel()
            swatch.setFixedSize(10, 10)
            swatch.setStyleSheet(
                f"background-color: {col_color};"
                "border-radius: 5px;"
                "min-width: 10px; min-height: 10px;"
            )
    
            # Curve name label — large, readable
            name_lbl = QLabel(col)
            name_lbl.setFont(QFont("Segoe UI", 12))
            name_lbl.setStyleSheet(
                f"color: {col_color};"
                "background: transparent;"
            )
    
            row_layout.addWidget(swatch)
            row_layout.addWidget(name_lbl)
            row_layout.addStretch()
    
            self.tree.setItemWidget(child, 0, row_widget)

        root.setExpanded(True)
        curves_node.setExpanded(True)
        return well

    def rebuild_tree(self):
        wells = list(self.wells.values())
        self.tree.clear()
        self.wells = {}
        for well in wells:
            self.add_well(well)

    def select_well(self, well_name):
        for idx in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(idx)
            data = item.data(0, Qt.UserRole)
            if data and data[0] == 'well' and data[1] == well_name:
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)
                return

    def remove_selected(self):
        items = self.tree.selectedItems()
        if not items:
            return
        item = items[0]
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data[0] == 'well':
            wname = data[1]
            root_item = item
        elif data[0] == 'curve':
            wname = data[1]
            root_item = item
            while root_item.parent() is not None:
                root_item = root_item.parent()
        else:
            return

        removed = self.wells.pop(wname, None)
        if removed is not None:
            idx = self.tree.indexOfTopLevelItem(root_item)
            self.tree.takeTopLevelItem(idx)
            self.well_removed.emit(wname)

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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Mnemonic", "Value", "Unit", "Description"])
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

    def load_comparison(self, wells):
        rows = []
        for well in ensure_well_list(wells):
            depth_min = ""
            depth_max = ""
            step = ""
            if well.depth_col and well.depth_col in well.df:
                depth = well.df[well.depth_col].dropna()
                if not depth.empty:
                    depth_min = f"{depth.min():.2f}"
                    depth_max = f"{depth.max():.2f}"
                    step = f"{(depth.max() - depth.min()) / max(len(depth) - 1, 1):.4f}"

            rows.extend([
                (well.name, "FILE", os.path.basename(well.filename), "", "Source file"),
                (well.name, "CURVES", str(len([curve for curve in well.curve_names if curve != well.depth_col])), "", "Curve count"),
                (well.name, "DEPTH", well.depth_col or "", "", "Depth column"),
                (well.name, "STRT", depth_min, "m" if depth_min else "", "Start depth"),
                (well.name, "STOP", depth_max, "m" if depth_max else "", "Stop depth"),
                (well.name, "STEP", step, "m" if step else "", "Average step"),
            ])

        self.table.clearContents()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Well", "Metric", "Value", "Unit", "Description"])
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, txt in enumerate(row):
                item = QTableWidgetItem(str(txt))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(r, c, item)

    def clear_view(self):
        self.table.clearContents()
        self.table.setRowCount(0)


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

    def load_comparison(self, wells):
        frames = []
        for well in ensure_well_list(wells):
            if well.df.empty:
                continue
            stats_df = well.df.describe().T.round(4).reset_index().rename(columns={'index': 'Curve'})
            stats_df.insert(0, 'Well', well.name)
            frames.append(stats_df)

        if not frames:
            self.clear_view()
            return

        display_df = pd.concat(frames, ignore_index=True)
        self.table.clearContents()
        self.table.setRowCount(len(display_df))
        self.table.setColumnCount(len(display_df.columns))
        self.table.setHorizontalHeaderLabels([str(column) for column in display_df.columns])
        self.table.setVerticalHeaderLabels([str(idx + 1) for idx in range(len(display_df))])
        for r, row in enumerate(display_df.itertuples(index=False, name=None)):
            for c, val in enumerate(row):
                item = QTableWidgetItem("" if pd.isna(val) else str(val))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                if r % 2 == 0:
                    item.setForeground(QColor(ACCENT))
                self.table.setItem(r, c, item)

    def clear_view(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)


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

    def load_comparison(self, wells):
        wells = ensure_well_list(wells)
        if not wells:
            self.clear_view()
            return

        rows_per_well = max(20, 500 // max(len(wells), 1))
        frames = []
        for well in wells:
            sample = well.df.head(rows_per_well).copy()
            if sample.empty:
                continue
            sample.insert(0, "WELL", well.name)
            frames.append(sample)

        if not frames:
            self.clear_view()
            return

        df = pd.concat(frames, ignore_index=True, sort=False)
        self.table.clearContents()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))
        for r, row in df.iterrows():
            for c, val in enumerate(row):
                item = QTableWidgetItem("" if pd.isna(val) else f"{val:.4g}" if isinstance(val, float) else str(val))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(r, c, item)

    def clear_view(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)


# ─────────────────────────────────────────────
#  MULTI-TRACK PLOT
# ─────────────────────────────────────────────
class MultiTrackPlot(PlotCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, figsize=(14, 10))

    def plot(self, wells, selected_curves=None, depth_range=None, log_scale=False, plot_style='Line'):
        self.fig.clear()
        wells = [
            well for well in ensure_well_list(wells)
            if not well.df.empty and well.depth_col is not None and well.depth_col in well.df
        ]
        if not wells:
            self.canvas.draw()
            return

        curves = selected_curves or available_curve_names(wells, mode='intersection')
        if not curves:
            curves = available_curve_names(wells, mode='union')
        curves = curves[:10]
        if not curves:
            self.canvas.draw()
            return

        if len(wells) == 1:
            self._plot_single_well(wells[0], curves, depth_range, log_scale=log_scale, plot_style=plot_style)
        else:
            self._plot_compare_wells(wells, curves, depth_range, log_scale=log_scale, plot_style=plot_style)
        self.canvas.draw()

    def _draw_track(self, ax, x, y, color, plot_style):
        """Draw one curve on ax using the requested style."""
        if plot_style == 'Filled Area':
            x_min = np.nanmin(x) if len(x) else 0
            ax.fill_betweenx(y, x_min, x, alpha=0.35, color=color)
            ax.plot(x, y, color=color, linewidth=0.6)
        elif plot_style == 'Step':
            ax.step(x, y, where='mid', color=color, linewidth=0.8)
        else:  # Line (default)
            ax.plot(x, y, color=color, linewidth=0.8)

    def _plot_single_well(self, well, curves, depth_range, log_scale=False, plot_style='Line'):
        depth = well.df[well.depth_col].values

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

            if log_scale:
                valid = valid & (vals > 0)
                if valid.any():
                    ax.set_xscale('log')

            if valid.any():
                self._draw_track(ax, vals[valid], d[valid], color, plot_style)
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

    def _plot_compare_wells(self, wells, curves, depth_range, log_scale=False, plot_style='Line'):
        rows = len(wells)
        cols = len(curves)
        self.fig.set_size_inches(max(12, cols * 2.8), max(8, rows * 2.8))
        axes = self.fig.subplots(rows, cols, squeeze=False, sharey='row')
        self.fig.subplots_adjust(wspace=0.08, hspace=0.18, left=0.08, right=0.99, top=0.93, bottom=0.05)
        self.fig.suptitle(
            f"Multi-Track Compare  |  {summarize_well_names(wells)}",
            color=ACCENT,
            fontsize=fs(11),
            fontweight='bold',
        )

        for row, well in enumerate(wells):
            depth = well.df[well.depth_col].values
            if depth_range:
                mask = (depth >= depth_range[0]) & (depth <= depth_range[1])
            else:
                mask = np.ones(len(depth), dtype=bool)
            d = depth[mask]

            for col, curve in enumerate(curves):
                ax = axes[row][col]
                ax.set_facecolor(PANEL_BG)
                ax.tick_params(axis='x', labelsize=fs(6), colors=TEXT_DIM)
                ax.tick_params(axis='y', labelsize=fs(6), colors=TEXT_DIM)
                ax.xaxis.set_label_position('top')
                ax.xaxis.tick_top()
                ax.invert_yaxis()

                if row == 0:
                    ax.set_title(curve, color=TRACK_COLORS[col % len(TRACK_COLORS)], fontsize=fs(8), fontweight='bold', pad=4)
                if col == 0:
                    ax.set_ylabel(f"{well.name}\nDepth (m)", color=TEXT_DIM, fontsize=fs(8))

                if curve not in well.df.columns:
                    ax.text(0.5, 0.5, "n/a", transform=ax.transAxes, ha='center', va='center', color=TEXT_DIM)
                    continue

                vals = well.df[curve].values[mask]
                color = TRACK_COLORS[col % len(TRACK_COLORS)]
                valid = np.isfinite(vals)
                if log_scale:
                    valid = valid & (vals > 0)
                    if valid.any():
                        ax.set_xscale('log')
                if not valid.any():
                    ax.text(0.5, 0.5, "empty", transform=ax.transAxes, ha='center', va='center', color=TEXT_DIM)
                    continue

                self._draw_track(ax, vals[valid], d[valid], color, plot_style)
                unit = well.curves.get(curve, {}).get('unit', '')
                ax.set_xlabel(f"{curve} [{unit}]" if unit else curve, fontsize=fs(6), color=TEXT_DIM)


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

    def plot(self, wells, depth_range=None, log_resistivity=True,
             track0_curve=None, track1_deep=None, track1_shallow=None,
             track2_density=None, track2_neutron=None):
        self.fig.clear()
        wells = [
            well for well in ensure_well_list(wells)
            if not well.df.empty and well.depth_col is not None and well.depth_col in well.df
        ]
        if not wells:
            self.canvas.draw()
            return

        track_cfg = dict(
            track0_curve=track0_curve,
            track1_deep=track1_deep,
            track1_shallow=track1_shallow,
            track2_density=track2_density,
            track2_neutron=track2_neutron,
        )

        if len(wells) == 1:
            self.fig.set_size_inches(14, 10)
            self.fig.suptitle(f"Triple Combo  |  {wells[0].name}", color=ACCENT,
                              fontsize=fs(11), fontweight='bold')
            gs = gridspec.GridSpec(1, 3, figure=self.fig, wspace=0.08,
                                   left=0.07, right=0.99, top=0.90, bottom=0.05)
            axes = [self.fig.add_subplot(gs[0, i]) for i in range(3)]
            self._plot_well_row(axes, wells[0], depth_range, show_titles=True,
                                log_resistivity=log_resistivity, **track_cfg)
        else:
            row_count = len(wells)
            self.fig.set_size_inches(14, max(10, row_count * 3.6))
            self.fig.suptitle(
                f"Triple Combo Compare  |  {summarize_well_names(wells)}",
                color=ACCENT,
                fontsize=fs(11),
                fontweight='bold',
            )
            gs = gridspec.GridSpec(row_count, 3, figure=self.fig, wspace=0.08, hspace=0.18,
                                   left=0.08, right=0.99, top=0.94, bottom=0.05)
            for row, well in enumerate(wells):
                axes = [self.fig.add_subplot(gs[row, i]) for i in range(3)]
                self._plot_well_row(axes, well, depth_range, show_titles=(row == 0),
                                    log_resistivity=log_resistivity, **track_cfg)

        self.canvas.draw()

    def _plot_well_row(self, axes, well, depth_range=None, show_titles=True, log_resistivity=True,
                       track0_curve=None, track1_deep=None, track1_shallow=None,
                       track2_density=None, track2_neutron=None):
        depth = well.df[well.depth_col].values
        if depth_range:
            mask = (depth >= depth_range[0]) & (depth <= depth_range[1])
        else:
            mask = np.ones(len(depth), dtype=bool)
        d = depth[mask]
        for ax in axes:
            ax.set_facecolor(PANEL_BG)
            ax.invert_yaxis()
            ax.tick_params(axis='x', labelsize=fs(6), colors=TEXT_DIM)
            ax.tick_params(axis='y', labelsize=fs(6), colors=TEXT_DIM)
            ax.xaxis.set_label_position('top')
            ax.xaxis.tick_top()
            ax.grid(True, axis='x', color=GRID_CLR, linewidth=0.5, alpha=0.8)

        # ---- Track 0 : Correlation (user-selectable, defaults to GR)
        if track0_curve and track0_curve != '-- (none) --' and track0_curve in well.df.columns:
            # Use the user-overridden curve directly
            vals0 = well.df[track0_curve].values[mask]
            valid0 = np.isfinite(vals0)
            if valid0.any():
                axes[0].plot(vals0[valid0], d[valid0], color="#00a83b", linewidth=0.8, label=track0_curve)
                lo, hi = self._padded_limits(vals0[valid0], default=(0, 200), hard=(0, None))
                axes[0].set_xlim(lo, hi)
            unit = well.curves.get(track0_curve, {}).get('unit', '') or ''
            axes[0].set_xlabel(f"{track0_curve} ({unit})", color="#00a83b", fontsize=fs(7))
            gr_curve = track0_curve
        else:
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
        axes[0].set_title("Correlation" if show_titles else "", color=TEXT_LIGHT, fontsize=fs(8), pad=2)
        axes[0].set_ylabel(f"{well.name}\nDepth (m)", color=TEXT_DIM, fontsize=fs(8))

        # ---- Track 1 : Resistivity (user-selectable deep + shallow)
        _res_deep = track1_deep if (track1_deep and track1_deep != '-- (none) --' and track1_deep in well.df.columns) else find_curve(well, TRIPLE_PRESETS['RES_DEEP'])
        _res_sha  = track1_shallow if (track1_shallow and track1_shallow != '-- (none) --' and track1_shallow in well.df.columns) else find_curve(well, TRIPLE_PRESETS['RES_SHA'])
        res_deep = _res_deep
        res_sha  = _res_sha
        for curve, color in ((_res_deep, "#f44336"), (_res_sha, "#1e88e5")):
            if not curve:
                continue
            vals = well.df[curve].values[mask]
            if log_resistivity:
                valid = np.isfinite(vals) & (vals > 0)
            else:
                valid = np.isfinite(vals)
            if valid.any():
                axes[1].plot(vals[valid], d[valid], color=color, linewidth=0.9, label=curve)
        if log_resistivity:
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
        axes[1].set_title("Resistivity" if show_titles else "", color=TEXT_LIGHT, fontsize=fs(8), pad=2)
        axes[1].set_xlabel("RT (ohm.m)", color="#f44336", fontsize=fs(7))

        # ---- Track 2 : Nuclear (RHOB + NPHI with independent x-axes)
        _rhob_curve = track2_density if (track2_density and track2_density != '-- (none) --' and track2_density in well.df.columns) else None
        _nphi_curve = track2_neutron if (track2_neutron and track2_neutron != '-- (none) --' and track2_neutron in well.df.columns) else None

        nphi_ax = None
        if _rhob_curve:
            rhob_curve = _rhob_curve
            vals_r = well.df[rhob_curve].values[mask]
            valid_r = np.isfinite(vals_r)
            if valid_r.any():
                axes[2].plot(vals_r[valid_r], d[valid_r], color="#e53935", linewidth=0.8, label=rhob_curve)
                lo, hi = self._padded_limits(vals_r[valid_r], default=(1.95, 2.95), hard=(None, None))
                axes[2].set_xlim(lo, hi)
            unit = well.curves.get(rhob_curve, {}).get('unit', 'g/cc') or 'g/cc'
            axes[2].set_xlabel(f"{rhob_curve} ({unit})", color="#e53935", fontsize=fs(7))
        else:
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

        nphi_curve = _nphi_curve or find_curve(well, TRIPLE_PRESETS['NPHI'])
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
        if not show_titles:
            axes[2].set_title("", color=TEXT_LIGHT, fontsize=fs(8), pad=2)

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

    def plot(self, wells, curve: str, bins=50, log_scale=False):
        self.fig.clear()
        wells = [well for well in ensure_well_list(wells) if curve in well.df.columns]
        if not wells:
            self.canvas.draw()
            return

        ax = self.fig.add_subplot(111)
        ax.tick_params(axis='both', labelsize=fs(8), colors=TEXT_DIM)
        unit = wells[0].curves.get(curve, {}).get('unit', '')
        ax.set_xlabel(f"{curve}  [{unit}]" if unit else curve, color=TEXT_LIGHT, fontsize=fs(10))

        if len(wells) == 1:
            well = wells[0]
            vals = well.df[curve].dropna().values
            if len(vals) == 0:
                ax.text(0.5, 0.5, "No valid samples", transform=ax.transAxes,
                        ha='center', va='center', color=TEXT_DIM)
                self.canvas.draw()
                return
            color = TRACK_COLORS[0]

            ax.hist(vals, bins=bins, color=color, alpha=0.75,
                    edgecolor=DARK_BG, linewidth=0.5)
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

            ax.set_ylabel("Count", color=TEXT_LIGHT, fontsize=fs(10))
            ax.set_title(f"Histogram  –  {curve}  |  {well.name}", color=ACCENT,
                         fontsize=fs(11), fontweight='bold')

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
        else:
            summary_lines = []
            plotted = False
            for idx, well in enumerate(wells):
                vals = well.df[curve].dropna().values
                if len(vals) == 0:
                    continue
                plotted = True
                color = TRACK_COLORS[idx % len(TRACK_COLORS)]
                ax.hist(vals, bins=bins, histtype='step', density=True, linewidth=1.5,
                        color=color, alpha=0.95, label=well.name)
                summary_lines.append(f"{well.name}: n={len(vals):,}, mean={np.mean(vals):.4g}")

            if not plotted:
                ax.text(0.5, 0.5, "No valid samples", transform=ax.transAxes,
                        ha='center', va='center', color=TEXT_DIM)
                self.canvas.draw()
                return

            if log_scale:
                ax.set_yscale('log')

            ax.set_ylabel("Density", color=TEXT_LIGHT, fontsize=fs(10))
            ax.set_title(f"Histogram Compare  –  {curve}", color=ACCENT,
                         fontsize=fs(11), fontweight='bold')
            if summary_lines:
                ax.legend(fontsize=fs(8), framealpha=0.85)
            if summary_lines:
                ax.text(0.98, 0.97, "\n".join(summary_lines[:6]), transform=ax.transAxes, fontsize=fs(8),
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

    def plot(self, wells, x_curve: str, y_curve: str,
             color_curve: str = None, size_curve: str = None):
        self.fig.clear()
        wells = ensure_well_list(wells)
        valid_wells = [well for well in wells if x_curve in well.df.columns and y_curve in well.df.columns]
        if not valid_wells:
            self.canvas.draw()
            return

        ax = self.fig.add_subplot(111)
        ax.tick_params(axis='both', labelsize=fs(8), colors=TEXT_DIM)

        if len(valid_wells) == 1:
            well = valid_wells[0]
            df = well.df[[c for c in [x_curve, y_curve, color_curve, size_curve,
                                       well.depth_col]
                           if c and c in well.df.columns]].dropna(subset=[x_curve, y_curve])
            if df.empty:
                self.canvas.draw()
                return

            x = df[x_curve].values
            y = df[y_curve].values
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
        else:
            plotted = False
            for idx, well in enumerate(valid_wells):
                columns = [column for column in [x_curve, y_curve, size_curve] if column and column in well.df.columns]
                df = well.df[columns].dropna(subset=[x_curve, y_curve])
                if df.empty:
                    continue
                plotted = True

                s_vals = None
                if size_curve and size_curve in df:
                    sv = df[size_curve].values
                    s_vals = (sv - sv.min()) / (sv.max() - sv.min() + 1e-9) * 40 + 8

                color = TRACK_COLORS[idx % len(TRACK_COLORS)]
                ax.scatter(
                    df[x_curve].values,
                    df[y_curve].values,
                    c=color,
                    s=s_vals if s_vals is not None else 10,
                    alpha=0.45,
                    linewidths=0,
                    label=well.name,
                )

                if len(df) > 2 and len(valid_wells) <= 5:
                    slope, intercept, r, p, _ = stats.linregress(df[x_curve].values, df[y_curve].values)
                    xs = np.linspace(df[x_curve].min(), df[x_curve].max(), 100)
                    ax.plot(xs, slope * xs + intercept, color=color, linewidth=1.2, linestyle='--')

            if not plotted:
                ax.text(0.5, 0.5, "No valid samples", transform=ax.transAxes,
                        ha='center', va='center', color=TEXT_DIM)
                self.canvas.draw()
                return

            ux = valid_wells[0].curves.get(x_curve, {}).get('unit', '')
            uy = valid_wells[0].curves.get(y_curve, {}).get('unit', '')
            ax.set_xlabel(f"{x_curve}  [{ux}]" if ux else x_curve, color=TEXT_LIGHT, fontsize=fs(10))
            ax.set_ylabel(f"{y_curve}  [{uy}]" if uy else y_curve, color=TEXT_LIGHT, fontsize=fs(10))
            ax.set_title(f"Cross Plot Compare  {x_curve} vs {y_curve}",
                         color=ACCENT, fontsize=fs(11), fontweight='bold')
            ax.legend(fontsize=fs(8), framealpha=0.85)

        self.canvas.draw()


# ─────────────────────────────────────────────
#  CONTROL PANELS (right dock)
# ─────────────────────────────────────────────
class WellSelectionControls(QObject):
    selection_changed = pyqtSignal()

    def __init__(self, ui):
        super().__init__()
        self.active_well_name = ""
        self.ui = ui
        self.compare_cb = ui.compare_cb
        self.well_list = ui.well_list
        self.active_btn = ui.active_btn
        self.all_btn = ui.all_btn
        
        self.compare_cb.toggled.connect(self._on_compare_toggled)
        self.well_list.itemSelectionChanged.connect(self.selection_changed.emit)
        self.active_btn.clicked.connect(self.use_active_only)
        self.all_btn.clicked.connect(self.select_all)
        self._apply_mode_state()

    def compare_enabled(self):
        return self.compare_cb.isChecked()

    def set_wells(self, wells, active_name=None, emit=False):
        wells = ensure_well_list(wells)
        if active_name is not None:
            self.active_well_name = active_name
        previous_selection = set(self.selected_well_names())

        self.well_list.blockSignals(True)
        self.well_list.clear()
        for well in wells:
            self.well_list.addItem(QListWidgetItem(well.name))
        self.well_list.blockSignals(False)

        if self.compare_enabled():
            names_to_select = previous_selection or {well.name for well in wells}
        else:
            names_to_select = {self.active_well_name} if self.active_well_name else set()
        self._select_names(names_to_select, emit=False)
        self._apply_mode_state()

        if emit:
            self.selection_changed.emit()

    def set_active_well(self, well_name, emit=False):
        self.active_well_name = well_name or ""
        if not self.compare_enabled():
            self._select_names([self.active_well_name], emit=False)
        if emit:
            self.selection_changed.emit()

    def selected_well_names(self):
        if not self.compare_enabled():
            return [self.active_well_name] if self.active_well_name else []
        return [item.text() for item in self.well_list.selectedItems()]

    def select_all(self, emit=True):
        self.compare_cb.blockSignals(True)
        self.compare_cb.setChecked(True)
        self.compare_cb.blockSignals(False)
        names = [self.well_list.item(index).text() for index in range(self.well_list.count())]
        self._select_names(names, emit=False)
        self._apply_mode_state()
        if emit:
            self.selection_changed.emit()

    def use_active_only(self, emit=True):
        self.compare_cb.blockSignals(True)
        self.compare_cb.setChecked(False)
        self.compare_cb.blockSignals(False)
        self._select_names([self.active_well_name], emit=False)
        self._apply_mode_state()
        if emit:
            self.selection_changed.emit()

    def _select_names(self, names, emit=False):
        selected = set(name for name in names if name)
        self.well_list.blockSignals(True)
        for index in range(self.well_list.count()):
            item = self.well_list.item(index)
            item.setSelected(item.text() in selected)
        self.well_list.blockSignals(False)
        if emit:
            self.selection_changed.emit()

    def _on_compare_toggled(self, enabled):
        if enabled and self.well_list.count() > 1 and len(self.selected_well_names()) <= 1:
            names = [self.well_list.item(index).text() for index in range(self.well_list.count())]
            self._select_names(names, emit=False)
        elif not enabled:
            self._select_names([self.active_well_name], emit=False)

        self._apply_mode_state()
        self.selection_changed.emit()

    def _apply_mode_state(self):
        compare_enabled = self.compare_enabled()
        self.well_list.setEnabled(compare_enabled)
        self.all_btn.setEnabled(compare_enabled)


class MultiTrackControls(QWidget):
    plot_requested = pyqtSignal(list, tuple, bool, str)   # curves, depth_range, log_scale, plot_style

    def __init__(self, well=None):
        super().__init__()
        self.wells = ensure_well_list(well)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        g = QGroupBox("Curve Selection")
        gl = QVBoxLayout(g)
        self.curve_list = QListWidget()
        self.curve_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.curve_list.setMaximumHeight(200)
        gl.addWidget(self.curve_list)
        layout.addWidget(g)

        g2 = QGroupBox("Plot Options")
        g2l = QFormLayout(g2)
        self.depth_min = QDoubleSpinBox()
        self.depth_min.setRange(-99999, 99999)
        self.depth_min.setDecimals(1)
        self.depth_max = QDoubleSpinBox()
        self.depth_max.setRange(-99999, 99999)
        self.depth_max.setDecimals(1)
        self.depth_max.setValue(99999)
        g2l.addRow("Min Depth:", self.depth_min)
        g2l.addRow("Max Depth:", self.depth_max)

        self.style_cb = QComboBox()
        self.style_cb.addItems(['Line', 'Filled Area', 'Step'])
        g2l.addRow("Plot Style:", self.style_cb)

        self.log_cb = QCheckBox("Logarithmic Scale")
        g2l.addRow("", self.log_cb)
        layout.addWidget(g2)

        btn = QPushButton("▶  Plot Tracks")
        btn.clicked.connect(self._emit)
        layout.addWidget(btn)
        layout.addStretch()

    def set_wells(self, wells):
        self.wells = ensure_well_list(wells)
        self.curve_list.clear()
        for curve in available_curve_names(self.wells, mode='union'):
            self.curve_list.addItem(curve)

        depth_min, depth_max = depth_limits_for_wells(self.wells)
        self.depth_min.setValue(depth_min)
        self.depth_max.setValue(depth_max)

    def set_well(self, well):
        self.set_wells([well] if well else [])

    def _emit(self):
        selected = [item.text() for item in self.curve_list.selectedItems()]
        if not selected:
            selected = available_curve_names(self.wells, mode='intersection')[:8]
        if not selected:
            selected = available_curve_names(self.wells, mode='union')[:8]
        self.plot_requested.emit(
            selected,
            (self.depth_min.value(), self.depth_max.value()),
            self.log_cb.isChecked(),
            self.style_cb.currentText(),
        )


class TripleComboControls(QWidget):
    # log_resistivity, track0_curve, track1_deep, track1_shallow, track2_density, track2_neutron
    plot_requested = pyqtSignal(bool, str, str, str, str, str)

    NONE_ITEM = '-- (auto) --'

    def __init__(self):
        super().__init__()
        self._wells = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Track 0 ──────────────────────────────────────────────
        g0 = QGroupBox("Track 1 – Correlation")
        g0l = QFormLayout(g0)
        self.t0_cb = QComboBox()
        g0l.addRow("Curve:", self.t0_cb)
        layout.addWidget(g0)

        # ── Track 1 ──────────────────────────────────────────────
        g1 = QGroupBox("Track 2 – Resistivity")
        g1l = QFormLayout(g1)
        self.t1_deep_cb   = QComboBox()
        self.t1_sha_cb    = QComboBox()
        self.log_cb       = QCheckBox("Log Scale")
        self.log_cb.setChecked(True)
        g1l.addRow("Deep:",    self.t1_deep_cb)
        g1l.addRow("Shallow:", self.t1_sha_cb)
        g1l.addRow("",         self.log_cb)
        layout.addWidget(g1)

        # ── Track 2 ──────────────────────────────────────────────
        g2 = QGroupBox("Track 3 – Nuclear")
        g2l = QFormLayout(g2)
        self.t2_den_cb  = QComboBox()
        self.t2_neu_cb  = QComboBox()
        g2l.addRow("Density:", self.t2_den_cb)
        g2l.addRow("Neutron:", self.t2_neu_cb)
        layout.addWidget(g2)

        btn = QPushButton("▶  Plot Triple Combo")
        btn.clicked.connect(self._emit)
        layout.addWidget(btn)
        layout.addStretch()

    def _populate_cb(self, cb, curves, default_keys=None):
        """Populate a combobox with auto + curves; pre-select the best default."""
        cb.blockSignals(True)
        cb.clear()
        cb.addItem(self.NONE_ITEM)
        for c in curves:
            cb.addItem(c)
        # Try to pre-select a sensible default
        if default_keys:
            for key in default_keys:
                for i in range(cb.count()):
                    if cb.itemText(i).upper() == key.upper():
                        cb.setCurrentIndex(i)
                        break
                else:
                    continue
                break
        cb.blockSignals(False)

    def set_wells(self, wells):
        self._wells = ensure_well_list(wells)
        curves = available_curve_names(self._wells, mode='union')
        self._populate_cb(self.t0_cb,       curves, ['GR', 'GAMMARAY', 'SP', 'CAL'])
        self._populate_cb(self.t1_deep_cb,  curves, ['LLD', 'RT', 'RILD', 'RD', 'ILD'])
        self._populate_cb(self.t1_sha_cb,   curves, ['LLS', 'RFOC', 'RS', 'ILS', 'MSFL'])
        self._populate_cb(self.t2_den_cb,   curves, ['RHOB', 'RHOZ', 'DEN'])
        self._populate_cb(self.t2_neu_cb,   curves, ['NPHI', 'TNPH', 'CNL'])

    def set_well(self, well):
        self.set_wells([well] if well else [])

    def _val(self, cb):
        """Return the curve text, or '' if auto."""
        v = cb.currentText()
        return '' if v == self.NONE_ITEM else v

    def _emit(self):
        self.plot_requested.emit(
            self.log_cb.isChecked(),
            self._val(self.t0_cb),
            self._val(self.t1_deep_cb),
            self._val(self.t1_sha_cb),
            self._val(self.t2_den_cb),
            self._val(self.t2_neu_cb),
        )


class HistogramControls(QWidget):
    plot_requested = pyqtSignal(str, int, bool)

    def __init__(self):
        super().__init__()
        self.wells = []
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

    def set_wells(self, wells):
        self.wells = ensure_well_list(wells)
        self.curve_cb.clear()
        for curve in available_curve_names(self.wells, mode='union'):
            self.curve_cb.addItem(curve)

    def set_well(self, well):
        self.set_wells([well] if well else [])

    def _emit(self):
        self.plot_requested.emit(
            self.curve_cb.currentText(),
            self.bins_sb.value(),
            self.log_cb.isChecked(),
        )


class CrossPlotControls(QWidget):
    plot_requested = pyqtSignal(str, str, str, str)

    def __init__(self):
        super().__init__()
        self.wells = []
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

    def set_wells(self, wells):
        self.wells = ensure_well_list(wells)
        for cb in (self.x_cb, self.y_cb, self.col_cb, self.sz_cb):
            cb.clear()
        self.col_cb.addItem("None")
        self.sz_cb.addItem("None")

        curves = available_curve_names(self.wells, mode='union')
        for curve in curves:
            self.x_cb.addItem(curve)
            self.y_cb.addItem(curve)
            self.col_cb.addItem(curve)
            self.sz_cb.addItem(curve)
        if len(curves) >= 2:
            self.y_cb.setCurrentIndex(1)

    def set_well(self, well):
        self.set_wells([well] if well else [])

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
        ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "well_data_panel.ui")
        uic.loadUi(ui_path, self)
        
        self.setStyleSheet(STYLESHEET)
        self.current_well = None

        # Left dock – Well Explorer
        self.explorer = WellExplorer(self, self)
        self.explorer.well_selected.connect(self._on_well_selected)
        self.explorer.well_removed.connect(self._on_well_removed)

        # Right dock – Controls
        self.scope_ctrl = WellSelectionControls(self)
        
        # Tabs
        self.header_tab = HeaderTab()
        self.verticalLayout_header.addWidget(self.header_tab)

        self.stats_tab = StatsTab()
        self.verticalLayout_stats.addWidget(self.stats_tab)

        self.data_tab = DataTab()
        self.verticalLayout_data.addWidget(self.data_tab)

        self.track_canvas = MultiTrackPlot()
        self.verticalLayout_multitrack.addWidget(self.track_canvas)

        self.triple_canvas = TripleComboPlot()
        self.verticalLayout_triplecombo.addWidget(self.triple_canvas)

        self.hist_canvas = HistogramPlot()
        self.verticalLayout_histogram.addWidget(self.hist_canvas)

        self.xplot_canvas = CrossPlot()
        self.verticalLayout_crossplot.addWidget(self.xplot_canvas)

        # Controls per tab
        self.track_ctrl = MultiTrackControls()
        self.stackedControls.addWidget(self.track_ctrl)
        
        self.triple_ctrl = TripleComboControls()
        self.stackedControls.addWidget(self.triple_ctrl)
        
        self.hist_ctrl  = HistogramControls()
        self.stackedControls.addWidget(self.hist_ctrl)
        
        self.xplot_ctrl = CrossPlotControls()
        self.stackedControls.addWidget(self.xplot_ctrl)

        self.tabs.currentChanged.connect(self._tab_changed)
        self._tab_changed(0)

        # wire controls
        self.scope_ctrl.selection_changed.connect(self._on_well_scope_changed)
        self.track_ctrl.plot_requested.connect(
            lambda curves, dr, log, style: self._plot_multitrack(curves, dr, log, style)
        )
        self.triple_ctrl.plot_requested.connect(
            lambda log, t0, t1d, t1s, t2d, t2n: self._plot_triple_combo(log, t0, t1d, t1s, t2d, t2n)
        )
        self.hist_ctrl.plot_requested.connect(self._plot_histogram)
        self.xplot_ctrl.plot_requested.connect(self._plot_crossplot)

        # Actions connection
        self.actionLoad_LAS_File.triggered.connect(lambda: self.load_file('las'))
        self.actionLoad_CSV_File.triggered.connect(lambda: self.load_file('csv'))
        self.actionLoad_Multiple_Wells.triggered.connect(lambda: self.load_file('mixed', multiple=True))
        self.actionExport_Plot.triggered.connect(self._export_plot)
        self.actionExit.triggered.connect(self.close)
        self.actionWell_Explorer.triggered.connect(lambda: self.explorerDock.show())
        self.actionPlot_Controls.triggered.connect(lambda: self.ctrlDock.show())
        self.actionMinimize.triggered.connect(self._minimize_window)
        self.actionMaximize.triggered.connect(self._maximize_window)
        self.actionRestore.triggered.connect(self._restore_window)
        self.actionToggle_Full_Screen.triggered.connect(self._toggle_fullscreen)
        self.actionRun_Facies_Classification.triggered.connect(self._run_facies)
        self.actionSupervised_Classification.triggered.connect(self._supervised_facies)
        self.actionUnsupervised_Classification.triggered.connect(self._unsupervised_facies)
        self.actionAbout.triggered.connect(self._about)

        self.actionLoad_LAS_File_TB.triggered.connect(lambda: self.load_file('las'))
        self.actionLoad_CSV_File_TB.triggered.connect(lambda: self.load_file('csv'))
        self.actionLoad_Multiple_Wells_TB.triggered.connect(lambda: self.load_file('mixed', multiple=True))
        self.actionMulti_Track_TB.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        self.actionTriple_Combo_TB.triggered.connect(lambda: self.tabs.setCurrentIndex(4))
        self.actionHistogram_TB.triggered.connect(lambda: self.tabs.setCurrentIndex(5))
        self.actionCross_Plot_TB.triggered.connect(lambda: self.tabs.setCurrentIndex(6))
        self.actionExport_Plot_TB.triggered.connect(self._export_plot)
        self.actionMinimize_TB.triggered.connect(self._minimize_window)
        self.actionMaximize_TB.triggered.connect(self._maximize_window)
        self.actionRestore_TB.triggered.connect(self._restore_window)
        self.actionToggle_Full_Screen_TB.triggered.connect(self._toggle_fullscreen)

        self.status = self.statusbar
        self.status.showMessage("Ready  –  Load one or more LAS/CSV files to begin")
    def _pick_well_paths(self, fmt='las', multiple=False):
        if fmt == 'las':
            title = "Open LAS Files" if multiple else "Open LAS File"
            file_filter = "LAS Files (*.las *.LAS);;All Files (*)"
        elif fmt == 'csv':
            title = "Open CSV Files" if multiple else "Open CSV File"
            file_filter = "CSV Files (*.csv *.CSV *.txt *.TXT);;All Files (*)"
        else:
            title = "Open Well Files"
            file_filter = (
                "Well Files (*.las *.LAS *.csv *.CSV *.txt *.TXT);;"
                "LAS Files (*.las *.LAS);;"
                "CSV Files (*.csv *.CSV *.txt *.TXT);;"
                "All Files (*)"
            )

        if multiple:
            paths, _ = QFileDialog.getOpenFileNames(self, title, "", file_filter)
            return paths

        path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        return [path] if path else []

    def _load_well_path(self, path, fmt=None):
        detected_fmt = fmt if fmt in ('las', 'csv') else detect_well_format(path)
        if detected_fmt == 'las':
            return load_las(path)
        if detected_fmt == 'csv':
            return load_csv(path)
        raise ValueError(f"Unsupported well file format: {os.path.basename(path)}")

    def _show_load_issues(self, loaded_wells, errors):
        if not errors:
            return

        preview = "\n".join(f"- {error}" for error in errors[:8])
        if len(errors) > 8:
            preview += f"\n- ... and {len(errors) - 8} more"

        QMessageBox.warning(
            self,
            "Well import completed with issues",
            (
                f"Loaded {len(loaded_wells)} well(s).\n"
                f"Failed {len(errors)} file(s).\n\n"
                f"{preview}"
            ),
        )

    def load_file(self, fmt='las', multiple=False):
        paths = self._pick_well_paths(fmt, multiple)
        if not paths:
            return []

        requested_fmt = fmt if fmt in ('las', 'csv') else None
        loaded_wells = []
        errors = []

        for path in paths:
            try:
                well = self._load_well_path(path, requested_fmt)
            except ImportError:
                errors.append(f"{os.path.basename(path)}: lasio is not installed. Run `pip install lasio`.")
            except Exception as exc:
                errors.append(f"{os.path.basename(path)}: {exc}")
            else:
                loaded_wells.append(self.explorer.add_well(well))

        if not loaded_wells:
            title = "Error loading wells" if multiple or fmt == 'mixed' else (
                "Error loading LAS" if fmt == 'las' else "Error loading CSV"
            )
            QMessageBox.critical(self, title, "\n".join(errors) if errors else "No well files were loaded.")
            return []

        active_well = loaded_wells[-1]
        self._sync_scope_controls()
        self._on_well_selected(active_well)

        if len(loaded_wells) == 1:
            well = loaded_wells[0]
            self.status.showMessage(
                f"Loaded: {well.name}  ({len(well.curve_names)} curves, {len(well.df)} samples)"
            )
        else:
            self.status.showMessage(
                f"Loaded {len(loaded_wells)} wells. Active well: {active_well.name}"
            )

        self._show_load_issues(loaded_wells, errors)
        return loaded_wells

    def _all_loaded_wells(self):
        return list(self.explorer.wells.values())

    def _selected_wells(self):
        if not self.explorer.wells:
            return []

        selected_names = self.scope_ctrl.selected_well_names()
        wells = [self.explorer.wells[name] for name in selected_names if name in self.explorer.wells]
        if wells:
            return wells
        if self.current_well and self.current_well.name in self.explorer.wells:
            return [self.current_well]
        return [next(iter(self.explorer.wells.values()))]

    def _sync_scope_controls(self, emit=False):
        self.scope_ctrl.set_wells(
            self._all_loaded_wells(),
            self.current_well.name if self.current_well else "",
            emit=emit,
        )

    def _refresh_context_views(self):
        wells = self._selected_wells()
        if not wells:
            self._clear_active_well()
            return

        if len(wells) == 1:
            well = wells[0]
            self.header_tab.load(well)
            self.stats_tab.load(well)
            self.data_tab.load(well)
        else:
            self.header_tab.load_comparison(wells)
            self.stats_tab.load_comparison(wells)
            self.data_tab.load_comparison(wells)

        self.track_ctrl.set_wells(wells)
        self.triple_ctrl.set_wells(wells)
        self.hist_ctrl.set_wells(wells)
        self.xplot_ctrl.set_wells(wells)

        idx = self.tabs.currentIndex()
        if idx == 3:
            self._plot_multitrack([], (self.track_ctrl.depth_min.value(), self.track_ctrl.depth_max.value()),
                                  self.track_ctrl.log_cb.isChecked(), self.track_ctrl.style_cb.currentText())
        elif idx == 4:
            self._plot_triple_combo(
                self.triple_ctrl.log_cb.isChecked(),
                self.triple_ctrl._val(self.triple_ctrl.t0_cb),
                self.triple_ctrl._val(self.triple_ctrl.t1_deep_cb),
                self.triple_ctrl._val(self.triple_ctrl.t1_sha_cb),
                self.triple_ctrl._val(self.triple_ctrl.t2_den_cb),
                self.triple_ctrl._val(self.triple_ctrl.t2_neu_cb),
            )

        if len(wells) == 1:
            self.status.showMessage(f"Active well: {wells[0].name}")
        else:
            self.status.showMessage(f"Comparing {len(wells)} wells: {summarize_well_names(wells)}")

    def _on_well_selected(self, well: WellData):
        self.current_well = well
        self.explorer.select_well(well.name)
        self.scope_ctrl.set_active_well(well.name)
        self._refresh_context_views()

    def _on_well_scope_changed(self):
        wells = self._selected_wells()
        if wells:
            selected_names = {well.name for well in wells}
            if self.current_well is None or self.current_well.name not in selected_names:
                self.current_well = wells[0]
                self.explorer.select_well(self.current_well.name)
                self.scope_ctrl.set_active_well(self.current_well.name)
        self._refresh_context_views()

    def _on_well_removed(self, well_name):
        if self.current_well is not None and self.current_well.name == well_name:
            remaining_wells = self._all_loaded_wells()
            self.current_well = remaining_wells[-1] if remaining_wells else None

        self._sync_scope_controls()
        if self.current_well:
            self.explorer.select_well(self.current_well.name)
            self.scope_ctrl.set_active_well(self.current_well.name)
            self._refresh_context_views()
            self.status.showMessage(f"Removed: {well_name}. Active context updated.")
        else:
            self._clear_active_well()
            self.status.showMessage(f"Removed: {well_name}. No wells loaded.")

    def _tab_changed(self, idx):
        if idx == 3:
            self.stackedControls.setCurrentWidget(self.track_ctrl)
            if self._selected_wells():
                self._plot_multitrack([], (self.track_ctrl.depth_min.value(), self.track_ctrl.depth_max.value()),
                                      self.track_ctrl.log_cb.isChecked(), self.track_ctrl.style_cb.currentText())
        elif idx == 4:
            self.stackedControls.setCurrentWidget(self.triple_ctrl)
            if self._selected_wells():
                self._plot_triple_combo(
                    self.triple_ctrl.log_cb.isChecked(),
                    self.triple_ctrl._val(self.triple_ctrl.t0_cb),
                    self.triple_ctrl._val(self.triple_ctrl.t1_deep_cb),
                    self.triple_ctrl._val(self.triple_ctrl.t1_sha_cb),
                    self.triple_ctrl._val(self.triple_ctrl.t2_den_cb),
                    self.triple_ctrl._val(self.triple_ctrl.t2_neu_cb),
                )
        elif idx == 5:
            self.stackedControls.setCurrentWidget(self.hist_ctrl)
        elif idx == 6:
            self.stackedControls.setCurrentWidget(self.xplot_ctrl)
        else:
            self.stackedControls.setCurrentIndex(0)

    def _plot_multitrack(self, curves, depth_range, log_scale=False, plot_style='Line'):
        wells = self._selected_wells()
        if not wells:
            return
        dr = depth_range if depth_range and depth_range[0] < depth_range[1] else None
        self.track_canvas.plot(wells, curves or None, dr, log_scale, plot_style)

    def _plot_triple_combo(self, log_resistivity, track0='', track1_deep='', track1_sha='', track2_den='', track2_neu=''):
        wells = self._selected_wells()
        if not wells:
            return
        self.triple_canvas.plot(
            wells,
            log_resistivity=log_resistivity,
            track0_curve=track0 or None,
            track1_deep=track1_deep or None,
            track1_shallow=track1_sha or None,
            track2_density=track2_den or None,
            track2_neutron=track2_neu or None,
        )
    
    def _plot_histogram(self, curve, bins, log_scale):
        wells = self._selected_wells()
        if not wells or not curve:
            return
    
        self.hist_canvas.plot(
            wells,
            curve,
            bins=bins,
            log_scale=log_scale,
        )

    def _plot_crossplot(self, x, y, col, sz):
        wells = self._selected_wells()
        if not wells or not x or not y:
            return
        self.xplot_canvas.plot(wells, x, y,
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
        self._sync_scope_controls()
        self.explorer.select_well(self.current_well.name)
        self.scope_ctrl.set_active_well(self.current_well.name)
        self._refresh_context_views()

    def _clear_active_well(self):
        self.current_well = None
        self.scope_ctrl.set_wells([], active_name="", emit=False)
        self.header_tab.clear_view()
        self.stats_tab.clear_view()
        self.data_tab.clear_view()
        self.track_ctrl.set_wells([])
        self.triple_ctrl.set_wells([])
        self.hist_ctrl.set_wells([])
        self.xplot_ctrl.set_wells([])
        self.track_canvas.clear()
        self.triple_canvas.clear()
        self.hist_canvas.clear()
        self.xplot_canvas.clear()

    def _format_facies_mapping(self, label_mapping):
        if not label_mapping:
            return ""
        entries = [f"{code}={label}" for code, label in label_mapping.items()]
        if len(entries) > 8:
            entries = entries[:8] + ["..."]
        return "\nCode mapping: " + ", ".join(entries)

    def _selected_processing_wells(self):
        wells = self._selected_wells()
        if wells:
            return wells
        return [self.current_well] if self.current_well else []

    def _apply_facies_curve(self, well, output_column, description, prediction_codes):
        well.df[output_column] = prediction_codes
        well.curves[output_column] = {
            'unit': 'class',
            'desc': description,
        }

    def _show_batch_result_summary(self, title, successes, errors):
        lines = successes[:8]
        if len(successes) > 8:
            lines.append(f"... and {len(successes) - 8} more successful well(s)")
        if errors:
            lines.append("")
            lines.append("Errors:")
            lines.extend(errors[:8])
            if len(errors) > 8:
                lines.append(f"... and {len(errors) - 8} more error(s)")

        QMessageBox.information(self, title, "\n".join(lines))

    def _run_facies(self):
        if not self._ensure_active_well("Facies Classification"):
            return

        chooser = QMessageBox(self)
        chooser.setWindowTitle("Facies Classification")
        target_wells = self._selected_processing_wells()
        scope_text = (
            f"Run the workflow on {len(target_wells)} selected wells."
            if len(target_wells) > 1 else
            "Run the workflow on the active well."
        )
        chooser.setText(f"Choose the facies-classification workflow to run.\n\n{scope_text}")
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

        from gui.facies_supervised import SupervisedFaciesDialog, SupervisedFaciesClassifier

        target_wells = self._selected_processing_wells()

        dialog = SupervisedFaciesDialog(self.current_well, self)
        if dialog.exec_() != QDialog.Accepted:
            return

        config = dialog.get_config()
        result = dialog.get_result()
        if result is None:
            return

        successes = []
        errors = []
        for well in target_wells:
            try:
                well_result = result if well is self.current_well else SupervisedFaciesClassifier(config).run(well.df)
                self._apply_facies_curve(
                    well,
                    well_result.output_column,
                    f"Supervised facies codes generated with {well_result.model_name}",
                    well_result.prediction_codes,
                )
                successes.append(
                    f"{well.name}: rows={well_result.used_rows}, train={well_result.train_accuracy:.3f}, "
                    f"validation={well_result.validation_accuracy:.3f}"
                )
            except Exception as exc:
                errors.append(f"{well.name}: {exc}")

        if not successes:
            QMessageBox.critical(self, "Supervised Classification", "\n".join(errors) if errors else "No wells were classified.")
            return

        self._refresh_current_well_views()
        self.status.showMessage(
            f"Created facies curve {result.output_column} on {len(successes)} well(s)"
        )
        self._show_batch_result_summary(
            "Supervised Classification Complete",
            [
                f"Output column: {result.output_column}",
                f"Method: {result.model_name}",
                f"Classified wells: {len(successes)}",
                *successes,
                self._format_facies_mapping(result.label_mapping).strip(),
            ],
            errors,
        )

    def _unsupervised_facies(self):
        if not self._ensure_active_well("Unsupervised Classification"):
            return

        from gui.facies_unsupervised import UnsupervisedFaciesDialog, UnsupervisedFaciesClassifier

        target_wells = self._selected_processing_wells()

        dialog = UnsupervisedFaciesDialog(self.current_well, self)
        if dialog.exec_() != QDialog.Accepted:
            return

        config = dialog.get_config()
        result = dialog.get_result()
        if result is None:
            return

        successes = []
        errors = []
        for well in target_wells:
            try:
                well_result = result if well is self.current_well else UnsupervisedFaciesClassifier(config).run(well.df)
                self._apply_facies_curve(
                    well,
                    well_result.output_column,
                    f"Unsupervised facies codes generated with {well_result.model_name}",
                    well_result.prediction_codes,
                )
                successes.append(
                    f"{well.name}: rows={well_result.used_rows}, clusters={well_result.cluster_count}, "
                    f"noise={well_result.noise_points}"
                )
            except Exception as exc:
                errors.append(f"{well.name}: {exc}")

        if not successes:
            QMessageBox.critical(self, "Unsupervised Classification", "\n".join(errors) if errors else "No wells were classified.")
            return

        self._refresh_current_well_views()
        self.status.showMessage(
            f"Created facies curve {result.output_column} on {len(successes)} well(s)"
        )
        self._show_batch_result_summary(
            "Unsupervised Classification Complete",
            [
                f"Output column: {result.output_column}",
                f"Method: {result.model_name}",
                f"Classified wells: {len(successes)}",
                *successes,
            ],
            errors,
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
            "• Load LAS and CSV well log files, including batch import<br>"
            "• Choose one, many, or all wells for comparison<br>"
            "• Header / curve metadata viewer<br>"
            "• Statistical summary table<br>"
            "• Multi-track and triple-combo comparison views<br>"
            "• Histogram and cross-plot comparison views<br>"
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

    def load_file(self, fmt='las', multiple=False):
        loaded_wells = super().load_file(fmt, multiple)
        for well in loaded_wells:
            self.well_loaded.emit(well.filename)
        return loaded_wells

    def open_las_dialog(self, multiple=False):
        return bool(self.load_file('las', multiple=multiple))


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
