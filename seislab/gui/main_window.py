"""
SeisLab Main Window - Professional Edition
Advanced GUI for seismic data analysis, visualization, and interpretation
Inspired by Petrel F&P and OpendTect workstation interfaces
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMenu, QAction, QStatusBar, QFileDialog, QMessageBox,
    QSplitter, QLabel, QPushButton, QComboBox, QSpinBox,
    QGroupBox, QFormLayout, QDoubleSpinBox, QProgressBar,
    QToolBar, QTreeWidget, QTreeWidgetItem, QSlider, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDockWidget,
    QFrame, QScrollArea, QSizePolicy, QToolButton, QActionGroup,
    QDialog, QDialogButtonBox, QTextEdit, QLineEdit, QRadioButton,
    QButtonGroup, QGridLayout, QStackedWidget, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont, QFontDatabase, QPixmap, QPainter
import os
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from gui.segy_viewer import SeismicViewer
from gui.attribute_panel import AttributePanel
from gui.processing_panel import ProcessingPanel
from gui.interpretation_panel import InterpretationPanel
from gui.info_panel import InfoPanel
from gui.well_data_panel import WellDataWindow
from seismic.segy_loader import SegyLoader


# ─────────────────────────────────────────────
#  Colour Palette  (dark workstation theme)
# ─────────────────────────────────────────────
DARK_BG       = "#1a1d21"
PANEL_BG      = "#21252b"
PANEL_ALT     = "#282c34"
BORDER        = "#3a3f47"
ACCENT        = "#0078d4"
ACCENT_HOVER  = "#106ebe"
ACCENT_GREEN  = "#4caf50"
ACCENT_ORANGE = "#ff8c00"
ACCENT_RED    = "#e53935"
TEXT_PRIMARY  = "#d4d8de"
TEXT_SECONDARY= "#8b9099"
TEXT_HEADER   = "#ffffff"
GROUP_TITLE   = "#61afef"
TAB_ACTIVE    = "#0078d4"
TOOLBAR_BG    = "#1e2228"
HIGHLIGHT     = "#264f78"
INPUT_BG      = "#2c313a"
SLIDER_GROOVE = "#3a3f47"
SLIDER_HANDLE = "#0078d4"


DARK_STYLESHEET = f"""
/* ── Global ── */
* {{
    font-family: "Segoe UI", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
    font-size: 12px;
    color: {TEXT_PRIMARY};
}}
QMainWindow, QWidget {{
    background-color: {DARK_BG};
}}

/* ── MenuBar ── */
QMenuBar {{
    background-color: {TOOLBAR_BG};
    border-bottom: 1px solid {BORDER};
    padding: 2px 0px;
    spacing: 2px;
}}
QMenuBar::item {{
    padding: 5px 12px;
    background: transparent;
    border-radius: 3px;
    color: {TEXT_PRIMARY};
}}
QMenuBar::item:selected, QMenuBar::item:pressed {{
    background: {HIGHLIGHT};
    color: {TEXT_HEADER};
}}
QMenu {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    padding: 4px 0px;
}}
QMenu::item {{
    padding: 7px 28px 7px 20px;
    color: {TEXT_PRIMARY};
}}
QMenu::item:selected {{
    background-color: {HIGHLIGHT};
    color: {TEXT_HEADER};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 3px 8px;
}}

/* ── ToolBar ── */
QToolBar {{
    background-color: {TOOLBAR_BG};
    border-bottom: 1px solid {BORDER};
    spacing: 3px;
    padding: 4px 6px;
}}
QToolBar::separator {{
    width: 1px;
    background: {BORDER};
    margin: 4px 6px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px 8px;
    color: {TEXT_PRIMARY};
    min-width: 28px;
}}
QToolButton:hover {{
    background: {PANEL_ALT};
    border-color: {BORDER};
}}
QToolButton:pressed, QToolButton:checked {{
    background: {HIGHLIGHT};
    border-color: {ACCENT};
    color: {TEXT_HEADER};
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background: {PANEL_BG};
    border-top: 2px solid {ACCENT};
}}
QTabBar {{
    background: {TOOLBAR_BG};
}}
QTabBar::tab {{
    background: {TOOLBAR_BG};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 8px 18px;
    margin-right: 2px;
    color: {TEXT_SECONDARY};
    font-weight: 500;
    letter-spacing: 0.3px;
}}
QTabBar::tab:selected {{
    background: {PANEL_BG};
    color: {TEXT_HEADER};
    border-top: 2px solid {ACCENT};
    font-weight: 700;
}}
QTabBar::tab:hover:!selected {{
    background: {PANEL_ALT};
    color: {TEXT_PRIMARY};
}}

/* ── GroupBox ── */
QGroupBox {{
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border: 1px solid {BORDER};
    border-radius: 5px;
    margin-top: 14px;
    padding-top: 10px;
    background-color: {PANEL_BG};
    color: {GROUP_TITLE};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: {GROUP_TITLE};
}}

/* ── TreeWidget ── */
QTreeWidget {{
    background: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    alternate-background-color: {PANEL_ALT};
    color: {TEXT_PRIMARY};
    outline: none;
}}
QTreeWidget::item {{
    padding: 4px 2px;
    border-radius: 3px;
}}
QTreeWidget::item:hover {{
    background: {PANEL_ALT};
}}
QTreeWidget::item:selected {{
    background: {HIGHLIGHT};
    color: {TEXT_HEADER};
}}
QTreeWidget::branch:has-children:closed {{
    border-image: none;
    image: none;
}}
QHeaderView::section {{
    background: {PANEL_ALT};
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 5px 8px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}}

/* ── Table ── */
QTableWidget {{
    background: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER};
    color: {TEXT_PRIMARY};
    outline: none;
}}
QTableWidget::item:selected {{
    background: {HIGHLIGHT};
    color: {TEXT_HEADER};
}}

/* ── Inputs ── */
QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
    background: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: {HIGHLIGHT};
}}
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {{
    border-color: {ACCENT};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: {PANEL_ALT};
    border: none;
    width: 18px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {BORDER};
}}
QComboBox::drop-down {{
    border: none;
    background: {PANEL_ALT};
    width: 22px;
    border-radius: 0 4px 4px 0;
}}
QComboBox QAbstractItemView {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    selection-background-color: {HIGHLIGHT};
    color: {TEXT_PRIMARY};
    padding: 2px;
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
    color: {TEXT_PRIMARY};
    letter-spacing: 0.2px;
}}
QPushButton:hover {{
    background-color: #32373f;
    border-color: {ACCENT};
    color: {TEXT_HEADER};
}}
QPushButton:pressed {{
    background-color: {HIGHLIGHT};
    border-color: {ACCENT};
}}
QPushButton:disabled {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    color: #4a4f56;
}}
QPushButton#accent_btn {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    color: white;
    font-weight: 700;
}}
QPushButton#accent_btn:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#success_btn {{
    background-color: #2d5a30;
    border-color: {ACCENT_GREEN};
    color: {ACCENT_GREEN};
    font-weight: 700;
}}
QPushButton#danger_btn {{
    background-color: #4a1c1c;
    border-color: {ACCENT_RED};
    color: {ACCENT_RED};
}}

/* ── Slider ── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {SLIDER_GROOVE};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {SLIDER_HANDLE};
    border: 2px solid {ACCENT};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}

/* ── CheckBox ── */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {BORDER};
    border-radius: 3px;
    background: {INPUT_BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

/* ── RadioButton ── */
QRadioButton {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 2px solid {BORDER};
    border-radius: 7px;
    background: {INPUT_BG};
}}
QRadioButton::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ── ProgressBar ── */
QProgressBar {{
    background: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 3px;
    text-align: center;
    color: {TEXT_PRIMARY};
    font-size: 11px;
    height: 14px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {ACCENT}, stop:1 #4fa3e0);
    border-radius: 2px;
}}

/* ── StatusBar ── */
QStatusBar {{
    background: {TOOLBAR_BG};
    border-top: 1px solid {BORDER};
    padding: 2px 6px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
}}
QStatusBar::item {{ border: none; }}

/* ── DockWidget ── */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background: {PANEL_ALT};
    padding: 7px 10px;
    border-bottom: 1px solid {BORDER};
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: {GROUP_TITLE};
}}

/* ── ScrollBar ── */
QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_SECONDARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {PANEL_BG};
    height: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {TEXT_SECONDARY};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}
QSplitter::handle:hover {{
    background: {ACCENT};
}}

/* ── Section Labels ── */
QLabel#section_label {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 2px 0;
}}
QLabel#value_label {{
    color: {ACCENT_GREEN};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
}}
QLabel#coords_label {{
    color: {ACCENT_ORANGE};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
}}

/* ── Frame separators ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
}}
"""


# ─────────────────────────────────────────────
#  Time-to-Depth Conversion Dialog
# ─────────────────────────────────────────────
class TimeDepthDialog(QDialog):
    """Dialog for time-to-depth conversion settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Time ↔ Depth Conversion")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 14)

        # Header
        hdr = QLabel("Time ↔ Depth Conversion")
        hdr.setFont(QFont("Segoe UI", 14, QFont.Bold))
        hdr.setStyleSheet(f"color: {TEXT_HEADER}; padding-bottom: 4px;")
        layout.addWidget(hdr)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {BORDER};"); layout.addWidget(sep)

        # Conversion direction
        dir_group = QGroupBox("Conversion Direction")
        dir_layout = QHBoxLayout(dir_group)
        self.radio_t2d = QRadioButton("Time → Depth")
        self.radio_d2t = QRadioButton("Depth → Time")
        self.radio_t2d.setChecked(True)
        dir_layout.addWidget(self.radio_t2d)
        dir_layout.addWidget(self.radio_d2t)
        layout.addWidget(dir_group)

        # Velocity model
        vel_group = QGroupBox("Velocity Model")
        vel_form = QFormLayout(vel_group)

        self.vel_model_combo = QComboBox()
        self.vel_model_combo.addItems([
            "Constant Velocity",
            "Linear Velocity Gradient",
            "Interval Velocity (V(t))",
            "RMS Velocity",
            "Load from File (.csv / .dat)",
        ])
        vel_form.addRow("Model Type:", self.vel_model_combo)

        self.const_vel = QDoubleSpinBox()
        self.const_vel.setRange(100, 10000)
        self.const_vel.setValue(2000.0)
        self.const_vel.setSuffix(" m/s")
        self.const_vel.setDecimals(1)
        vel_form.addRow("Constant Velocity:", self.const_vel)

        self.v0_spin = QDoubleSpinBox()
        self.v0_spin.setRange(100, 8000)
        self.v0_spin.setValue(1500.0)
        self.v0_spin.setSuffix(" m/s")
        self.v0_spin.setDecimals(1)
        vel_form.addRow("V₀ (Surface Vel.):", self.v0_spin)

        self.gradient_spin = QDoubleSpinBox()
        self.gradient_spin.setRange(0, 5)
        self.gradient_spin.setValue(0.6)
        self.gradient_spin.setSuffix(" m/s per m")
        self.gradient_spin.setDecimals(3)
        vel_form.addRow("Gradient (k):", self.gradient_spin)

        self.vel_file_row = QWidget()
        vf_layout = QHBoxLayout(self.vel_file_row)
        vf_layout.setContentsMargins(0,0,0,0)
        self.vel_file_edit = QLineEdit()
        self.vel_file_edit.setPlaceholderText("Path to velocity file...")
        vf_layout.addWidget(self.vel_file_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.setMaximumWidth(80)
        browse_btn.clicked.connect(self._browse_vel_file)
        vf_layout.addWidget(browse_btn)
        vel_form.addRow("Velocity File:", self.vel_file_row)

        layout.addWidget(vel_group)
        self.vel_model_combo.currentIndexChanged.connect(self._toggle_vel_inputs)
        self._toggle_vel_inputs(0)

        # Depth reference
        ref_group = QGroupBox("Depth Reference & Output")
        ref_form = QFormLayout(ref_group)

        self.datum_spin = QDoubleSpinBox()
        self.datum_spin.setRange(-5000, 5000)
        self.datum_spin.setValue(0.0)
        self.datum_spin.setSuffix(" m")
        ref_form.addRow("Datum Elevation:", self.datum_spin)

        self.water_depth_spin = QDoubleSpinBox()
        self.water_depth_spin.setRange(0, 5000)
        self.water_depth_spin.setValue(0.0)
        self.water_depth_spin.setSuffix(" m")
        ref_form.addRow("Water Bottom Depth:", self.water_depth_spin)

        self.depth_unit_combo = QComboBox()
        self.depth_unit_combo.addItems(["Meters (m)", "Feet (ft)", "Milliseconds (ms)"])
        ref_form.addRow("Output Units:", self.depth_unit_combo)

        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(0.1, 20.0)
        self.sample_rate_spin.setValue(1.0)
        self.sample_rate_spin.setSuffix(" ms")
        ref_form.addRow("Time Sample Rate:", self.sample_rate_spin)

        self.output_sample_spin = QDoubleSpinBox()
        self.output_sample_spin.setRange(0.5, 100.0)
        self.output_sample_spin.setValue(2.0)
        self.output_sample_spin.setSuffix(" m")
        ref_form.addRow("Output Sample Interval:", self.output_sample_spin)

        layout.addWidget(ref_group)

        # Output options
        out_group = QGroupBox("Output Options")
        out_layout = QVBoxLayout(out_group)
        self.chk_replace = QCheckBox("Replace current dataset in workspace")
        self.chk_new_vol = QCheckBox("Create new volume (depth domain)")
        self.chk_new_vol.setChecked(True)
        self.chk_horizon = QCheckBox("Convert picked horizons too")
        self.chk_horizon.setChecked(True)
        out_layout.addWidget(self.chk_replace)
        out_layout.addWidget(self.chk_new_vol)
        out_layout.addWidget(self.chk_horizon)
        layout.addWidget(out_group)

        # Buttons
        btn_box = QDialogButtonBox()
        run_btn = QPushButton("Run Conversion")
        run_btn.setObjectName("accent_btn")
        run_btn.setMinimumWidth(140)
        cancel_btn = QPushButton("Cancel")
        btn_box.addButton(run_btn, QDialogButtonBox.AcceptRole)
        btn_box.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _toggle_vel_inputs(self, idx):
        show_const = idx == 0
        show_linear = idx == 1
        show_file = idx == 4
        self.const_vel.setEnabled(show_const)
        self.v0_spin.setEnabled(show_linear or idx in [2, 3])
        self.gradient_spin.setEnabled(show_linear)
        self.vel_file_row.setEnabled(show_file)

    def _browse_vel_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Velocity File", "",
            "Velocity Files (*.csv *.dat *.txt);;All Files (*)")
        if path:
            self.vel_file_edit.setText(path)

    def get_params(self):
        """Return conversion parameters as a dict."""
        return {
            "direction": "t2d" if self.radio_t2d.isChecked() else "d2t",
            "model": self.vel_model_combo.currentText(),
            "const_vel": self.const_vel.value(),
            "v0": self.v0_spin.value(),
            "gradient": self.gradient_spin.value(),
            "vel_file": self.vel_file_edit.text(),
            "datum": self.datum_spin.value(),
            "water_depth": self.water_depth_spin.value(),
            "depth_unit": self.depth_unit_combo.currentText(),
            "sample_rate": self.sample_rate_spin.value(),
            "output_sample": self.output_sample_spin.value(),
            "replace": self.chk_replace.isChecked(),
            "new_vol": self.chk_new_vol.isChecked(),
            "convert_horizons": self.chk_horizon.isChecked(),
        }


# ─────────────────────────────────────────────
#  Coordinate Display Widget (status-bar style)
# ─────────────────────────────────────────────
class CoordDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        def _lbl(text, obj_name="section_label"):
            l = QLabel(text); l.setObjectName(obj_name); return l

        for label, attr in [("IL:", "il_val"), ("XL:", "xl_val"),
                             ("Z:", "z_val"), ("X:", "x_val"), ("Y:", "y_val"),
                             ("Amp:", "amp_val")]:
            layout.addWidget(_lbl(label))
            val = QLabel("—"); val.setObjectName("coords_label")
            setattr(self, attr, val)
            layout.addWidget(val)
            if attr != "amp_val":
                sep = QFrame(); sep.setFrameShape(QFrame.VLine)
                sep.setStyleSheet(f"color: {BORDER};")
                layout.addWidget(sep)

    def update_coords(self, il=None, xl=None, z=None, x=None, y=None, amp=None):
        if il is not None:  self.il_val.setText(str(il))
        if xl is not None:  self.xl_val.setText(str(xl))
        if z  is not None:  self.z_val.setText(f"{z:.1f}")
        if x  is not None:  self.x_val.setText(f"{x:.1f}")
        if y  is not None:  self.y_val.setText(f"{y:.1f}")
        if amp is not None: self.amp_val.setText(f"{amp:.4f}")


# ─────────────────────────────────────────────
#  Main Application Window
# ─────────────────────────────────────────────
class SeisLabApp(QMainWindow):
    """Main application window for SeisLab — Professional Edition."""

    def __init__(self):
        super().__init__()

        # Application state
        self.segy_loader   = None
        self.current_data  = None
        self.current_inline   = 0
        self.current_crossline = 0
        self.current_timeslice = 0
        self.depth_mode    = False          # False = time, True = depth
        self.well_data_window = None

        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.display_current_section)

        self.setup_ui()
        self.setup_menubar()
        self.setup_toolbar()
        self.setup_statusbar()
        self.connect_signals()
        self.apply_light_theme()

    # ──────────────────────────────────────────
    #  UI CONSTRUCTION
    # ──────────────────────────────────────────
    def setup_ui(self):
        self.setWindowTitle("SeisLab Pro  ·  Seismic Analysis & Interpretation Workstation")
        self.setGeometry(60, 40, 1920, 1060)
        self.setMinimumSize(1280, 720)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        self.left_panel   = self._build_left_panel()
        self.center_panel = self._build_center_panel()
        self.right_panel  = self._build_right_panel()

        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.center_panel)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 6)
        self.main_splitter.setStretchFactor(2, 2)
        self.main_splitter.setSizes([280, 1260, 380])

        root.addWidget(self.main_splitter)

    # ── LEFT PANEL ─────────────────────────────
    def _build_left_panel(self):
        panel = QWidget(); panel.setMaximumWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── Object tree ──
        obj_grp = QGroupBox("Objects")
        obj_lay = QVBoxLayout(obj_grp)
        obj_lay.setContentsMargins(6, 14, 6, 6)

        self.workspace_tree = QTreeWidget()
        self.workspace_tree.setHeaderLabels(["Name", "Type"])
        self.workspace_tree.setAlternatingRowColors(True)
        self.workspace_tree.setColumnWidth(0, 160)
        self.workspace_tree.setSelectionMode(QAbstractItemView.SingleSelection)

        self.tree_root          = QTreeWidgetItem(["Workspace", ""])
        self.tree_segy_imports  = QTreeWidgetItem(["SEGY Volumes", "folder"])
        self.tree_horizons      = QTreeWidgetItem(["Horizons", "folder"])
        self.tree_attributes    = QTreeWidgetItem(["Attributes", "folder"])
        self.tree_depth_vols    = QTreeWidgetItem(["Depth Volumes", "folder"])
        self.tree_wells         = QTreeWidgetItem(["Wells", "folder"])
        self.tree_scripts       = QTreeWidgetItem(["Scripts", "folder"])
        self.tree_root.addChildren([
            self.tree_segy_imports, self.tree_horizons,
            self.tree_attributes, self.tree_depth_vols,
            self.tree_wells, self.tree_scripts,
        ])
        self.workspace_tree.addTopLevelItem(self.tree_root)
        self.workspace_tree.expandAll()
        obj_lay.addWidget(self.workspace_tree)

        # Tree action buttons
        tree_btns = QHBoxLayout()
        for label, tip in [("＋", "Add item"), ("✕", "Remove"), ("↑", "Move up"), ("↓", "Move down")]:
            b = QPushButton(label); b.setMaximumWidth(32); b.setToolTip(tip)
            tree_btns.addWidget(b)
        tree_btns.addStretch()
        obj_lay.addLayout(tree_btns)
        layout.addWidget(obj_grp)

        # ── Info panel ──
        self.info_panel = InfoPanel()
        layout.addWidget(self.info_panel)

        # ── Navigation ──
        nav_grp = QGroupBox("Navigation")
        nav_lay = QFormLayout(nav_grp)
        nav_lay.setContentsMargins(8, 16, 8, 8)
        nav_lay.setSpacing(8)

        self.inline_spin     = self._make_spinbox(0, 9999)
        self.crossline_spin  = self._make_spinbox(0, 9999)
        self.timeslice_spin  = self._make_spinbox(0, 9999)

        self.view_mode = QComboBox()
        self.view_mode.addItems(["Inline View", "Crossline View", "Time Slice"])

        nav_lay.addRow(self._nav_label("Inline:"),    self.inline_spin)
        nav_lay.addRow(self._nav_label("Crossline:"), self.crossline_spin)
        nav_lay.addRow(self._nav_label("Z / Time:"),  self.timeslice_spin)
        nav_lay.addRow(self._nav_label("View Mode:"), self.view_mode)
        layout.addWidget(nav_grp)

        # ── Domain indicator ──
        domain_grp = QGroupBox("Data Domain")
        domain_lay = QHBoxLayout(domain_grp)
        self.domain_label = QLabel("⏱  TIME DOMAIN")
        self.domain_label.setStyleSheet(
            f"color: {ACCENT_ORANGE}; font-weight: 800; font-size: 12px; letter-spacing: 0.8px;")
        domain_lay.addWidget(self.domain_label)
        domain_lay.addStretch()
        self.btn_convert_domain = QPushButton("Convert…")
        self.btn_convert_domain.setObjectName("accent_btn")
        self.btn_convert_domain.setEnabled(False)
        domain_lay.addWidget(self.btn_convert_domain)
        layout.addWidget(domain_grp)

        # ── Quick actions ──
        qa_grp = QGroupBox("Quick Actions")
        qa_lay = QVBoxLayout(qa_grp)
        qa_lay.setSpacing(5)

        self.btn_compute_attributes = QPushButton("⬡  Compute Attributes")
        self.btn_apply_filter       = QPushButton("⧖  Apply Filter / Processing")
        self.btn_ml_classify        = QPushButton("◈  ML / AI Classification")
        self.btn_pick_horizons      = QPushButton("∿  Horizon Picking")

        for btn in [self.btn_compute_attributes, self.btn_apply_filter,
                    self.btn_ml_classify, self.btn_pick_horizons]:
            btn.setEnabled(False)
            qa_lay.addWidget(btn)
        layout.addWidget(qa_grp)

        layout.addStretch()
        return panel

    # ── CENTER PANEL ───────────────────────────
    def _build_center_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        vsplit = QSplitter(Qt.Vertical)
        vsplit.setChildrenCollapsible(False)

        # ── Top: main viewport tabs ──
        top = QWidget()
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(4, 4, 4, 0)
        top_lay.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)

        self.seismic_viewer      = SeismicViewer()
        self.attribute_panel     = AttributePanel()
        self.processing_panel    = ProcessingPanel()
        self.interpretation_panel= InterpretationPanel()

        # Mini matplotlib canvas for depth-converted preview
        self.depth_viewer_widget = self._build_depth_viewer()

        self.tabs.addTab(self.seismic_viewer,        "🖥  Viewport")
        self.tabs.addTab(self.attribute_panel,       "⚡  Attributes")
        self.tabs.addTab(self.processing_panel,      "⚙  Processing")
        self.tabs.addTab(self.interpretation_panel,  "✎  Interpretation")
        self.tabs.addTab(self.depth_viewer_widget,   "⬇  Depth Domain")

        top_lay.addWidget(self.tabs)

        # ── Bottom: cells + statistics ──
        bottom = QWidget()
        bot_lay = QHBoxLayout(bottom)
        bot_lay.setContentsMargins(4, 4, 4, 4)
        bot_lay.setSpacing(6)

        # Data table
        tbl_grp = QGroupBox("Sample Data (Cells)")
        tbl_lay = QVBoxLayout(tbl_grp)
        tbl_lay.setContentsMargins(6, 14, 6, 6)
        self.data_table = QTableWidget(0, 6)
        self.data_table.setHorizontalHeaderLabels(["IL", "XL", "Z/T", "Amplitude", "│Amp│", "Phase°"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl_lay.addWidget(self.data_table)
        bot_lay.addWidget(tbl_grp, 3)

        # Stats + histogram
        stat_grp = QGroupBox("Statistics & Amplitude Distribution")
        stat_lay = QVBoxLayout(stat_grp)
        stat_lay.setContentsMargins(6, 14, 6, 6)

        self.stats_grid = QGridLayout()
        for i, (key, attr) in enumerate([
            ("Min", "stat_min"), ("Max", "stat_max"),
            ("Mean", "stat_mean"), ("Std", "stat_std"),
            ("Median", "stat_med"), ("RMS", "stat_rms"),
        ]):
            lbl = QLabel(key + ":"); lbl.setObjectName("section_label")
            val = QLabel("—"); val.setObjectName("value_label")
            setattr(self, attr, val)
            row, col = divmod(i, 2)
            self.stats_grid.addWidget(lbl, row, col * 2)
            self.stats_grid.addWidget(val, row, col * 2 + 1)
        stat_lay.addLayout(self.stats_grid)

        self.hist_figure = Figure(figsize=(4, 2.2), facecolor=PANEL_BG)
        self.hist_canvas = FigureCanvas(self.hist_figure)
        self.hist_ax = self.hist_figure.add_subplot(111, facecolor=INPUT_BG)
        self._style_ax(self.hist_ax, "Amplitude Histogram")
        stat_lay.addWidget(self.hist_canvas)
        bot_lay.addWidget(stat_grp, 2)

        vsplit.addWidget(top)
        vsplit.addWidget(bottom)
        vsplit.setStretchFactor(0, 5)
        vsplit.setStretchFactor(1, 1)
        vsplit.setSizes([780, 200])

        layout.addWidget(vsplit)
        return panel

    def _build_depth_viewer(self):
        """Minimal depth-domain viewer placeholder."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)

        info = QLabel(
            "⬇  Depth-converted volume will appear here after running\n"
            "  Processing → Time-to-Depth Conversion."
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; padding: 20px;")
        lay.addWidget(info)

        self.depth_figure  = Figure(figsize=(8, 6), facecolor=PANEL_BG)
        self.depth_canvas  = FigureCanvas(self.depth_figure)
        self.depth_ax      = self.depth_figure.add_subplot(111, facecolor=INPUT_BG)
        self._style_ax(self.depth_ax, "Depth Section (TVD)")
        lay.addWidget(self.depth_canvas)
        return w

    # ── RIGHT PANEL ────────────────────────────
    def _build_right_panel(self):
        panel = QWidget(); panel.setMinimumWidth(320); panel.setMaximumWidth(420)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(8)
        scroll.setWidget(scroll_content)

        # ── Visual Parameters ──
        vp_grp = QGroupBox("Visual Parameters")
        vp_lay = QVBoxLayout(vp_grp)
        vp_lay.setSpacing(6)

        self.chk_show_grid = QCheckBox("Show Grid")
        self.chk_show_grid.setChecked(True)
        self.chk_show_axis = QCheckBox("Show Axis Labels")
        self.chk_show_axis.setChecked(True)
        self.chk_smooth    = QCheckBox("Smooth Interpolation")
        self.chk_wiggle    = QCheckBox("Wiggle Trace Overlay")
        self.chk_crosshair = QCheckBox("Crosshair Cursor")
        self.chk_crosshair.setChecked(True)

        for chk in [self.chk_show_grid, self.chk_show_axis,
                    self.chk_smooth, self.chk_wiggle, self.chk_crosshair]:
            vp_lay.addWidget(chk)
        scroll_layout.addWidget(vp_grp)

        # ── Sections ──
        sec_grp = QGroupBox("Section Slicers")
        sec_lay = QVBoxLayout(sec_grp)
        sec_lay.setContentsMargins(8, 16, 8, 8)
        sec_lay.setSpacing(10)

        self.u_check, self.u_spin, self.u_slider = self._section_row(sec_lay, "U  (Inline)")
        self.v_check, self.v_spin, self.v_slider = self._section_row(sec_lay, "V  (Crossline)")
        self.z_check, self.z_spin, self.z_slider = self._section_row(sec_lay, "Z  (Time/Depth)")
        scroll_layout.addWidget(sec_grp)

        # ── Display settings ──
        disp_grp = QGroupBox("Display Settings")
        disp_form = QFormLayout(disp_grp)
        disp_form.setContentsMargins(8, 16, 8, 8)
        disp_form.setSpacing(8)

        self.colormap = QComboBox()
        self.colormap.addItems([
            "seismic", "gray", "viridis", "RdBu", "bwr", "jet",
            "plasma", "inferno", "coolwarm", "PuOr",
        ])
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0.01, 20.0); self.gain_spin.setValue(1.0); self.gain_spin.setSingleStep(0.1)
        self.clip_spin = QDoubleSpinBox()
        self.clip_spin.setRange(0.1, 100.0); self.clip_spin.setValue(99.0); self.clip_spin.setSingleStep(1.0)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100); self.opacity_slider.setValue(100)

        disp_form.addRow("Colormap:",   self.colormap)
        disp_form.addRow("Gain:",       self.gain_spin)
        disp_form.addRow("Clip %:",     self.clip_spin)
        disp_form.addRow("Opacity:",    self.opacity_slider)
        scroll_layout.addWidget(disp_grp)

        # ── Depth conversion mini-panel ──
        td_grp = QGroupBox("Time ↔ Depth")
        td_lay = QVBoxLayout(td_grp)
        td_lay.setContentsMargins(8, 16, 8, 8)

        self.lbl_current_domain = QLabel("Domain: Time (ms)")
        self.lbl_current_domain.setObjectName("value_label")
        td_lay.addWidget(self.lbl_current_domain)

        self.lbl_vel_model = QLabel("Velocity Model: —")
        self.lbl_vel_model.setObjectName("section_label")
        td_lay.addWidget(self.lbl_vel_model)

        btn_row = QHBoxLayout()
        self.btn_td_quick = QPushButton("Quick Convert")
        self.btn_td_quick.setObjectName("success_btn")
        self.btn_td_quick.setEnabled(False)
        self.btn_td_advanced = QPushButton("Advanced…")
        self.btn_td_advanced.setEnabled(False)
        btn_row.addWidget(self.btn_td_quick)
        btn_row.addWidget(self.btn_td_advanced)
        td_lay.addLayout(btn_row)
        scroll_layout.addWidget(td_grp)

        # ── Wavelet display ──
        wav_grp = QGroupBox("Wavelet Inspector")
        wav_lay = QVBoxLayout(wav_grp)
        wav_lay.setContentsMargins(8, 16, 8, 8)
        self.wavelet_figure = Figure(figsize=(3, 1.6), facecolor=PANEL_BG)
        self.wavelet_canvas = FigureCanvas(self.wavelet_figure)
        self.wavelet_ax     = self.wavelet_figure.add_subplot(111, facecolor=INPUT_BG)
        self._style_ax(self.wavelet_ax, "Wavelet / Trace")
        wav_lay.addWidget(self.wavelet_canvas)
        scroll_layout.addWidget(wav_grp)

        scroll_layout.addStretch()
        layout.addWidget(scroll)
        return panel

    # ── HELPERS ────────────────────────────────
    def _make_spinbox(self, lo, hi):
        sb = QSpinBox(); sb.setRange(lo, hi); sb.setKeyboardTracking(False)
        return sb

    def _nav_label(self, text):
        l = QLabel(text); l.setObjectName("section_label"); return l

    def _section_row(self, parent_layout, label):
        row_widget = QWidget()
        row_lay    = QHBoxLayout(row_widget)
        row_lay.setContentsMargins(0, 0, 0, 0); row_lay.setSpacing(6)

        chk = QCheckBox(label); chk.setChecked(True); chk.setMinimumWidth(100)
        spin   = QSpinBox(); spin.setRange(0, 9999); spin.setKeyboardTracking(False)
        spin.setMaximumWidth(72)
        slider = QSlider(Qt.Horizontal); slider.setRange(0, 9999)

        row_lay.addWidget(chk)
        row_lay.addWidget(spin)
        row_lay.addWidget(slider, 1)
        parent_layout.addWidget(row_widget)
        return chk, spin, slider

    def _style_ax(self, ax, title):
        ax.set_facecolor(INPUT_BG)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        ax.set_title(title, fontsize=9, color=TEXT_SECONDARY, pad=4)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        ax.xaxis.label.set_color(TEXT_SECONDARY)
        ax.yaxis.label.set_color(TEXT_SECONDARY)
        ax.grid(True, alpha=0.2, color=BORDER)
        ax.figure.patch.set_facecolor(PANEL_BG)
        try:
            ax.figure.tight_layout(pad=0.5)
        except Exception:
            pass

    # ──────────────────────────────────────────
    #  MENU BAR
    # ──────────────────────────────────────────
    def setup_menubar(self):
        mb = self.menuBar()

        # File
        file_m = mb.addMenu("File")
        self.action_open = QAction("Open SEG-Y…", self, shortcut="Ctrl+O")
        self.action_open_multi = QAction("Open Multiple Volumes…", self)
        self.action_save_project = QAction("Save Project…", self, shortcut="Ctrl+S")
        self.action_export = QAction("Export Data…", self, shortcut="Ctrl+E")
        self.action_export.setEnabled(False)
        self.action_exit = QAction("Exit", self, shortcut="Ctrl+Q")
        for a in [self.action_open, self.action_open_multi, None,
                  self.action_save_project, None,
                  self.action_export, None, self.action_exit]:
            if a is None: file_m.addSeparator()
            else: file_m.addAction(a)

        # View
        view_m = mb.addMenu("View")
        self.action_reset_view  = QAction("Reset View", self)
        self.action_fullscreen  = QAction("Full Screen", self, shortcut="F11", checkable=True)
        self.action_dark_theme  = QAction("Dark Theme", self, checkable=True); self.action_dark_theme.setChecked(True)
        for a in [self.action_reset_view, self.action_fullscreen, None, self.action_dark_theme]:
            if a is None: view_m.addSeparator()
            else: view_m.addAction(a)

        # Survey
        survey_m = mb.addMenu("Survey")
        self.action_survey_open = QAction("Open SEG-Y Survey…", self)
        self.action_survey_setup = QAction("Survey Setup…", self)
        self.action_well_import  = QAction("Import Well Data…", self)
        self.action_horizon_import = QAction("Import Horizons…", self)
        for a in [self.action_survey_open, self.action_survey_setup, None,
                  self.action_well_import, self.action_horizon_import]:
            if a is None: survey_m.addSeparator()
            else: survey_m.addAction(a)

        # Processing
        proc_m = mb.addMenu("Processing")
        self.action_bandpass  = QAction("Bandpass Filter…", self)
        self.action_gain_corr = QAction("Gain Correction…", self)
        self.action_normalize = QAction("Normalize", self)
        self.action_deconvolve = QAction("Deconvolution…", self)
        self.action_t2d = QAction("Time → Depth Conversion…", self)
        self.action_d2t = QAction("Depth → Time Conversion…", self)
        self.action_t2d.setEnabled(False)
        self.action_d2t.setEnabled(False)
        for a in [self.action_bandpass, self.action_gain_corr,
                  self.action_normalize, self.action_deconvolve,
                  None, self.action_t2d, self.action_d2t]:
            if a is None: proc_m.addSeparator()
            else: proc_m.addAction(a)

        # Attributes
        attr_m = mb.addMenu("Attributes")
        self.action_rms        = QAction("RMS Amplitude", self)
        self.action_inst_amp   = QAction("Instantaneous Amplitude", self)
        self.action_inst_phase = QAction("Instantaneous Phase", self)
        self.action_inst_freq  = QAction("Instantaneous Frequency", self)
        self.action_semblance  = QAction("Semblance / Coherence", self)
        self.action_curvature  = QAction("Curvature", self)
        for a in [self.action_rms, self.action_inst_amp,
                  self.action_inst_phase, self.action_inst_freq,
                  None, self.action_semblance, self.action_curvature]:
            if a is None: attr_m.addSeparator()
            else: attr_m.addAction(a)

        # Interpretation
        interp_m = mb.addMenu("Interpretation")
        self.action_pick_horizons = QAction("Horizon Picking", self)
        self.action_fault_detect  = QAction("Fault Detection…", self)
        self.action_facies        = QAction("Facies Classification…", self)
        for a in [self.action_pick_horizons, self.action_fault_detect, self.action_facies]:
            interp_m.addAction(a)

        # Machine Learning
        ml_m = mb.addMenu("Machine Learning")
        self.action_kmeans = QAction("K-Means Clustering", self)
        self.action_dbscan = QAction("DBSCAN", self)
        self.action_cnn    = QAction("CNN Facies Predictor…", self)
        for a in [self.action_kmeans, self.action_dbscan, None, self.action_cnn]:
            if a is None: ml_m.addSeparator()
            else: ml_m.addAction(a)

        # Help
        help_m = mb.addMenu("Help")
        self.action_about = QAction("About SeisLab Pro", self)
        self.action_docs  = QAction("Documentation", self)
        for a in [self.action_docs, None, self.action_about]:
            if a is None: help_m.addSeparator()
            else: help_m.addAction(a)

    # ──────────────────────────────────────────
    #  TOOLBAR
    # ──────────────────────────────────────────
    def setup_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(tb)

        for action in [self.action_t2d, self.action_bandpass]:
            tb.addAction(action)
        tb.addSeparator()

        for action in [self.action_rms, self.action_inst_amp]:
            tb.addAction(action)
        tb.addSeparator()

        tb.addAction(self.action_reset_view)
        tb.addAction(self.action_fullscreen)

        # Spacer
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # Domain indicator in toolbar
        self.toolbar_domain_lbl = QLabel("  ⏱ TIME  ")
        self.toolbar_domain_lbl.setStyleSheet(
            f"color: {ACCENT_ORANGE}; font-weight: 800; font-size: 12px; padding: 0 8px; "
            f"border: 1px solid {ACCENT_ORANGE}; border-radius: 3px;")
        tb.addWidget(self.toolbar_domain_lbl)
        tb.addSeparator()

        # Memory / info
        self.toolbar_info_lbl = QLabel("No data loaded  ")
        self.toolbar_info_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        tb.addWidget(self.toolbar_info_lbl)

    # ──────────────────────────────────────────
    #  STATUS BAR
    # ──────────────────────────────────────────
    def setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("Ready  ·  No data loaded")
        self.statusbar.addWidget(self.status_label)

        sep1 = QFrame(); sep1.setFrameShape(QFrame.VLine); sep1.setStyleSheet(f"color:{BORDER};")
        self.statusbar.addWidget(sep1)

        self.coord_display = CoordDisplay()
        self.statusbar.addWidget(self.coord_display)

        self.statusbar.addPermanentWidget(QLabel("  "))
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200); self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

        self.mem_label = QLabel("[mem: —]  ")
        self.mem_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.statusbar.addPermanentWidget(self.mem_label)

        # Memory update timer
        mem_timer = QTimer(self); mem_timer.timeout.connect(self._update_mem)
        mem_timer.start(5000)

    def _update_mem(self):
        try:
            import psutil
            mem = psutil.virtual_memory()
            self.mem_label.setText(
                f"[mem: {mem.used/1e9:.1f}/{mem.total/1e9:.1f} GB]  ")
        except ImportError:
            pass

    # ──────────────────────────────────────────
    #  SIGNAL CONNECTIONS
    # ──────────────────────────────────────────
    def connect_signals(self):
        self.action_open.triggered.connect(self.load_segy)
        self.action_survey_open.triggered.connect(self.load_segy)
        self.action_export.triggered.connect(self.export_data)
        self.action_exit.triggered.connect(self.close)
        self.action_reset_view.triggered.connect(self.reset_view)
        self.action_fullscreen.triggered.connect(self.toggle_fullscreen)

        self.action_t2d.triggered.connect(self.show_time_depth_dialog)
        self.action_d2t.triggered.connect(self.show_depth_time_dialog)
        self.action_well_import.triggered.connect(self.import_well_data)
        self.btn_convert_domain.clicked.connect(self.show_time_depth_dialog)
        self.btn_td_quick.clicked.connect(self._quick_t2d)
        self.btn_td_advanced.clicked.connect(self.show_time_depth_dialog)

        self.inline_spin.valueChanged.connect(self.update_inline)
        self.crossline_spin.valueChanged.connect(self.update_crossline)
        self.timeslice_spin.valueChanged.connect(self._set_timeslice_from_left)
        self.view_mode.currentIndexChanged.connect(self.change_view_mode)

        self.u_spin.valueChanged.connect(self._set_inline_from_right)
        self.u_slider.valueChanged.connect(self._set_inline_from_right)
        self.v_spin.valueChanged.connect(self._set_crossline_from_right)
        self.v_slider.valueChanged.connect(self._set_crossline_from_right)
        self.z_spin.valueChanged.connect(self._set_timeslice_from_right)
        self.z_slider.valueChanged.connect(self._set_timeslice_from_right)

        for chk in [self.u_check, self.v_check, self.z_check,
                    self.chk_show_grid, self.chk_show_axis, self.chk_smooth,
                    self.chk_wiggle, self.chk_crosshair]:
            chk.stateChanged.connect(self.change_view_mode)

        self.colormap.currentTextChanged.connect(self.update_colormap)
        self.gain_spin.valueChanged.connect(self.update_gain)
        self.clip_spin.valueChanged.connect(self.update_clip)

        self.btn_compute_attributes.clicked.connect(self.show_attributes_tab)
        self.btn_apply_filter.clicked.connect(self.show_processing_tab)
        self.btn_ml_classify.clicked.connect(self.show_ml_dialog)
        self.btn_pick_horizons.clicked.connect(
            lambda: self.tabs.setCurrentWidget(self.interpretation_panel))

        self.action_rms.triggered.connect(lambda: self.compute_attribute("rms"))
        self.action_inst_amp.triggered.connect(lambda: self.compute_attribute("inst_amp"))
        self.action_inst_phase.triggered.connect(lambda: self.compute_attribute("inst_phase"))
        self.action_inst_freq.triggered.connect(lambda: self.compute_attribute("inst_freq"))

        self.action_about.triggered.connect(self.show_about)

    # ──────────────────────────────────────────
    #  SYNC HELPERS
    # ──────────────────────────────────────────
    def _sync(self, spin, slider, value):
        for w in (spin, slider):
            w.blockSignals(True); w.setValue(value); w.blockSignals(False)

    def _set_inline_from_right(self, v):
        self.current_inline = int(v)
        self._sync(self.u_spin, self.u_slider, self.current_inline)
        self.inline_spin.blockSignals(True)
        self.inline_spin.setValue(self.current_inline)
        self.inline_spin.blockSignals(False)
        self.render_timer.start(35)

    def _set_crossline_from_right(self, v):
        self.current_crossline = int(v)
        self._sync(self.v_spin, self.v_slider, self.current_crossline)
        self.crossline_spin.blockSignals(True)
        self.crossline_spin.setValue(self.current_crossline)
        self.crossline_spin.blockSignals(False)
        self.render_timer.start(35)

    def _set_timeslice_from_right(self, v):
        self.current_timeslice = int(v)
        self._sync(self.z_spin, self.z_slider, self.current_timeslice)
        self.timeslice_spin.blockSignals(True)
        self.timeslice_spin.setValue(self.current_timeslice)
        self.timeslice_spin.blockSignals(False)
        self.render_timer.start(35)

    def _set_timeslice_from_left(self, v):
        self.current_timeslice = int(v)
        self._sync(self.z_spin, self.z_slider, self.current_timeslice)
        self.render_timer.start(35)

    # ──────────────────────────────────────────
    #  DATA LOADING
    # ──────────────────────────────────────────
    def load_segy(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open SEG-Y File", "",
            "SEG-Y Files (*.sgy *.segy);;All Files (*)")
        if not filepath:
            return
        try:
            self.status_label.setText("Loading SEG-Y file…")
            self.progress_bar.setVisible(True); self.progress_bar.setRange(0, 0)

            self.segy_loader = SegyLoader(filepath)
            self.segy_loader.load_data()

            self.current_inline = self.current_crossline = self.current_timeslice = 0
            self.depth_mode = False
            self._update_domain_ui()
            self.update_file_info()
            self.enable_controls()
            self.display_current_section()

            name = os.path.basename(filepath)
            self.status_label.setText(f"Loaded: {name}")
            self.toolbar_info_lbl.setText(f"  {name}  ")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load SEG-Y:\n{e}")
            self.status_label.setText("Load failed")
        finally:
            self.progress_bar.setVisible(False)

    def import_well_data(self):
        """Open standalone well-data workspace and import LAS."""
        if not self._has_loaded_segy():
            reply = QMessageBox.question(
                self,
                "Survey Data Required",
                "No SEG-Y survey is loaded.\n\n"
                "Do you want to load SEG-Y survey data first?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                self.load_segy()
                if not self._has_loaded_segy():
                    self.status_label.setText("SEG-Y load canceled or failed; well import skipped.")
                    return
            else:
                self.status_label.setText("Continuing with well import without SEG-Y survey.")

        if self.well_data_window is None:
            self.well_data_window = WellDataWindow(self)
            self.well_data_window.well_loaded.connect(self._on_well_loaded)

        if self.well_data_window.isMinimized():
            self.well_data_window.showNormal()
        self.well_data_window.show()
        self.well_data_window.raise_()
        self.well_data_window.activateWindow()
        self.well_data_window.open_las_dialog()

    def _has_loaded_segy(self):
        return bool(self.segy_loader is not None and getattr(self.segy_loader, "data", None) is not None)

    def _on_well_loaded(self, filepath):
        """Update UI elements after successful LAS load."""
        filename = os.path.basename(filepath)
        if not any(self.tree_wells.child(i).text(0) == filename
                   for i in range(self.tree_wells.childCount())):
            self.tree_wells.addChild(QTreeWidgetItem([filename, "LAS"]))
            self.workspace_tree.expandAll()
        self.status_label.setText(f"Loaded well data: {filename}")

    def update_file_info(self):
        if not self.segy_loader:
            return
        info = self.segy_loader.get_info()
        self.info_panel.update_info(info)

        ni  = max(1, info.get("n_inlines", 1))
        nxl = max(1, info.get("n_crosslines", 1))
        ns  = max(1, info.get("n_samples", 1))

        for spin, slider, val, mx in [
            (self.inline_spin,    None,         self.current_inline,    ni - 1),
            (self.crossline_spin, None,         self.current_crossline, nxl - 1),
            (self.timeslice_spin, None,         self.current_timeslice, ns - 1),
            (self.u_spin,         self.u_slider, self.current_inline,   ni - 1),
            (self.v_spin,         self.v_slider, self.current_crossline,nxl - 1),
            (self.z_spin,         self.z_slider, self.current_timeslice,ns - 1),
        ]:
            spin.setMaximum(mx)
            if slider: slider.setMaximum(mx)
            self._sync(spin, slider or spin, val)

        filename = os.path.basename(info.get("filepath", "unknown.segy"))
        self.tree_segy_imports.addChild(QTreeWidgetItem([filename, "SEGY"]))
        self.workspace_tree.expandAll()

    def enable_controls(self):
        self.action_export.setEnabled(True)
        self.action_t2d.setEnabled(True)
        self.action_d2t.setEnabled(True)
        self.btn_convert_domain.setEnabled(True)
        self.btn_td_quick.setEnabled(True)
        self.btn_td_advanced.setEnabled(True)
        for btn in [self.btn_compute_attributes, self.btn_apply_filter,
                    self.btn_ml_classify, self.btn_pick_horizons]:
            btn.setEnabled(True)

    # ──────────────────────────────────────────
    #  DISPLAY
    # ──────────────────────────────────────────
    def display_current_section(self):
        if not self.segy_loader:
            return
        try:
            ni  = len(self.segy_loader.inlines)   if self.segy_loader.inlines   is not None else 0
            nxl = len(self.segy_loader.crosslines) if self.segy_loader.crosslines is not None else 0
            ns  = int(self.segy_loader.n_samples or 0)

            self.current_inline    = max(0, min(self.current_inline,    max(0, ni - 1)))
            self.current_crossline = max(0, min(self.current_crossline, max(0, nxl - 1)))
            self.current_timeslice = max(0, min(self.current_timeslice, max(0, ns - 1)))

            for spin, val in [(self.inline_spin, self.current_inline),
                               (self.crossline_spin, self.current_crossline)]:
                spin.blockSignals(True); spin.setValue(val); spin.blockSignals(False)

            self._sync(self.u_spin, self.u_slider, self.current_inline)
            self._sync(self.v_spin, self.v_slider, self.current_crossline)
            self._sync(self.z_spin, self.z_slider, self.current_timeslice)

            vm = self.view_mode.currentText()
            if vm in ["Inline View", "Crossline View"]:
                self.current_data = self.segy_loader.get_inline(self.current_inline)
                self.seismic_viewer.display_inline_crossline(
                    self.segy_loader.data,
                    self.current_inline, self.current_crossline,
                    timeslice_index=self.current_timeslice,
                    show_inline=self.u_check.isChecked(),
                    show_crossline=self.v_check.isChecked(),
                    show_timeslice=self.z_check.isChecked(),
                    colormap=self.colormap.currentText(),
                    gain=self.gain_spin.value(),
                    clip=self.clip_spin.value(),
                    show_grid=self.chk_show_grid.isChecked(),
                    show_axis=self.chk_show_axis.isChecked(),
                )
            else:
                self.current_data = self.segy_loader.get_timeslice(self.current_timeslice)
                self.seismic_viewer.display_section(
                    self.current_data,
                    colormap=self.colormap.currentText(),
                    gain=self.gain_spin.value(),
                    clip=self.clip_spin.value(),
                )

            self.attribute_panel.set_data(
                self.current_data,
                sample_rate_ms=self.segy_loader.sample_rate if self.segy_loader else None,
                sample_axis=1,
            )
            self._refresh_data_panels(self.current_data)
            self._update_wavelet_panel(self.current_data)
            self.coord_display.update_coords(
                il=self.current_inline, xl=self.current_crossline, z=float(self.current_timeslice))

        except Exception as e:
            QMessageBox.warning(self, "Display Warning", f"Could not render section:\n{e}")

    def _refresh_data_panels(self, data):
        if data is None: return
        arr  = np.asarray(data)
        flat = arr.reshape(-1)
        if flat.size == 0: return

        # Stats
        mn, mx, mu, sd = np.min(flat), np.max(flat), np.mean(flat), np.std(flat)
        med = float(np.median(flat))
        rms = float(np.sqrt(np.mean(flat ** 2)))
        self.stat_min.setText(f"{mn:.4f}")
        self.stat_max.setText(f"{mx:.4f}")
        self.stat_mean.setText(f"{mu:.4f}")
        self.stat_std.setText(f"{sd:.4f}")
        self.stat_med.setText(f"{med:.4f}")
        self.stat_rms.setText(f"{rms:.4f}")

        # Histogram
        self.hist_ax.clear()
        self.hist_ax.hist(flat, bins=80, color=ACCENT, alpha=0.7, linewidth=0)
        self.hist_ax.axvline(mu, color=ACCENT_ORANGE, lw=1.2, linestyle="--", label="Mean")
        self._style_ax(self.hist_ax, "Amplitude Distribution")
        self.hist_canvas.draw_idle()

        # Table
        rows = min(150, flat.size)
        self.data_table.setRowCount(rows)
        nt = arr.shape[1] if arr.ndim == 2 else 1
        idx = np.linspace(0, flat.size - 1, rows, dtype=int)
        for r, k in enumerate(idx):
            i, t = (k // nt, k % nt) if arr.ndim == 2 else (0, k)
            amp = float(arr[i, t]) if arr.ndim == 2 else float(flat[k])
            ph  = float(np.angle(amp + 1j * abs(amp), deg=True))
            for c, v in enumerate([str(i), str(i), str(t),
                                    f"{amp:.4f}", f"{abs(amp):.4f}", f"{ph:.1f}°"]):
                self.data_table.setItem(r, c, QTableWidgetItem(v))

    def _update_wavelet_panel(self, data):
        if data is None: return
        try:
            arr = np.asarray(data)
            trace = arr[arr.shape[0] // 2] if arr.ndim == 2 else arr
            self.wavelet_ax.clear()
            self.wavelet_ax.plot(trace, color=ACCENT, lw=1.2)
            self.wavelet_ax.fill_between(range(len(trace)), trace, 0,
                                          where=(trace > 0), color=ACCENT, alpha=0.35)
            self.wavelet_ax.fill_between(range(len(trace)), trace, 0,
                                          where=(trace < 0), color=ACCENT_RED, alpha=0.25)
            self._style_ax(self.wavelet_ax, "Centre Trace")
            self.wavelet_canvas.draw_idle()
        except Exception:
            pass

    # ──────────────────────────────────────────
    #  TIME ↔ DEPTH CONVERSION
    # ──────────────────────────────────────────
    def show_time_depth_dialog(self):
        dlg = TimeDepthDialog(self)
        dlg.radio_t2d.setChecked(True)
        self._style_dialog(dlg)
        if dlg.exec_() == QDialog.Accepted:
            self._run_time_depth_conversion(dlg.get_params())

    def show_depth_time_dialog(self):
        dlg = TimeDepthDialog(self)
        dlg.radio_d2t.setChecked(True)
        self._style_dialog(dlg)
        if dlg.exec_() == QDialog.Accepted:
            self._run_time_depth_conversion(dlg.get_params())

    def _style_dialog(self, dlg):
        dlg.setStyleSheet(self.styleSheet())

    def _quick_t2d(self):
        """Quick time-to-depth with default 2000 m/s constant velocity."""
        if self.current_data is None:
            QMessageBox.warning(self, "No Data", "Load seismic data first.")
            return
        params = {
            "direction": "t2d",
            "model": "Constant Velocity",
            "const_vel": 2000.0,
            "datum": 0.0,
            "sample_rate": 1.0,
            "output_sample": 2.0,
        }
        self._run_time_depth_conversion(params)

    def _run_time_depth_conversion(self, params):
        """Execute time-to-depth (or depth-to-time) conversion on loaded data."""
        if not self.segy_loader or self.current_data is None:
            QMessageBox.warning(self, "No Data", "Load seismic data first.")
            return

        try:
            self.status_label.setText("Running conversion…")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            data = np.asarray(self.segy_loader.data, dtype=np.float32)
            direction = params.get("direction", "t2d")

            # Build velocity model
            model = params.get("model", "Constant Velocity")
            if model == "Constant Velocity":
                vel = float(params.get("const_vel", 2000.0))
                v_func = lambda t_ms: vel                              # noqa: E731
            elif model == "Linear Velocity Gradient":
                v0 = float(params.get("v0", 1500.0))
                k  = float(params.get("gradient", 0.6))
                v_func = lambda t_ms: v0 + k * (t_ms / 1000.0) * v0   # noqa: E731
            else:
                # Fallback to constant
                vel = float(params.get("const_vel", 2000.0))
                v_func = lambda t_ms: vel                              # noqa: E731

            dt_ms = float(params.get("sample_rate", 1.0))
            dz    = float(params.get("output_sample", 2.0))
            datum = float(params.get("datum", 0.0))

            n_inlines, n_xl, n_t = (data.shape if data.ndim == 3
                                    else (1, *data.shape) if data.ndim == 2
                                    else (1, 1, data.shape[0]))

            if direction == "t2d":
                # Build time array (ms)
                t_arr = np.arange(n_t) * dt_ms
                # Compute cumulative depth via numerical integration
                depths = np.zeros(n_t)
                for i in range(1, n_t):
                    v_avg = (v_func(t_arr[i - 1]) + v_func(t_arr[i])) / 2.0
                    depths[i] = depths[i - 1] + v_avg * (dt_ms / 1000.0) / 2.0  # one-way

                max_depth = depths[-1] + datum
                n_z = max(1, int(max_depth / dz))
                depth_axis = np.arange(n_z) * dz + datum
                converted = np.zeros((*data.shape[:-1], n_z), dtype=np.float32) if data.ndim == 3 \
                    else np.zeros((data.shape[0], n_z), dtype=np.float32)

                # Resample each trace via linear interpolation
                flat_data = data.reshape(-1, n_t)
                flat_out  = np.zeros((flat_data.shape[0], n_z), dtype=np.float32)
                for tr in range(flat_data.shape[0]):
                    flat_out[tr] = np.interp(depth_axis, depths + datum, flat_data[tr])
                converted = flat_out.reshape((*data.shape[:-1], n_z)) if data.ndim == 3 \
                    else flat_out
            else:
                # depth → time: invert the depth axis
                n_z   = n_t
                t_max = 2000.0  # ms
                t_out = np.linspace(0, t_max, n_z)
                vel   = float(params.get("const_vel", 2000.0))
                z_arr = np.arange(n_z) * dz + datum
                t_arr = (z_arr / vel) * 2000.0  # one-way to two-way ms

                flat_data = data.reshape(-1, n_t)
                flat_out  = np.zeros((flat_data.shape[0], n_z), dtype=np.float32)
                t_orig    = np.arange(n_t) * dt_ms
                for tr in range(flat_data.shape[0]):
                    flat_out[tr] = np.interp(t_out, t_arr, flat_data[tr])
                converted = flat_out.reshape((*data.shape[:-1], n_z)) if data.ndim == 3 \
                    else flat_out

            # Display depth section
            il_idx = min(self.current_inline, converted.shape[0] - 1) if converted.ndim > 2 else 0
            depth_slice = converted[il_idx] if converted.ndim == 3 else converted

            self.depth_ax.clear()
            vm = self.colormap.currentText()
            flat = depth_slice.reshape(-1)
            vmax = np.percentile(np.abs(flat), self.clip_spin.value()) * self.gain_spin.value()
            self.depth_ax.imshow(depth_slice.T, aspect="auto", cmap=vm,
                                 vmin=-vmax, vmax=vmax, origin="upper")
            ylabel = "Depth (m)" if direction == "t2d" else "Time (ms)"
            self.depth_ax.set_xlabel("Trace", color=TEXT_SECONDARY, fontsize=9)
            self.depth_ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=9)
            self._style_ax(self.depth_ax,
                           f"Depth Section  [IL {self.current_inline}]" if direction == "t2d"
                           else f"Time Section  [IL {self.current_inline}]")
            self.depth_canvas.draw_idle()

            # Switch tab
            self.tabs.setCurrentWidget(self.depth_viewer_widget)

            # Update domain label
            self.depth_mode = (direction == "t2d")
            self._update_domain_ui()

            # Add to workspace tree
            vol_name = f"Depth Vol. (IL {self.current_inline})" if direction == "t2d" \
                else f"Time Vol. (IL {self.current_inline})"
            self.tree_depth_vols.addChild(QTreeWidgetItem([vol_name, "Volume"]))
            self.workspace_tree.expandAll()

            self.lbl_vel_model.setText(f"Velocity Model: {params.get('model','—')}")
            self.status_label.setText(f"Conversion complete  [{direction.upper()}]  "
                                       f"Vel={params.get('const_vel','—')} m/s")
            QMessageBox.information(self, "Conversion Complete",
                                    f"{'Time → Depth' if direction=='t2d' else 'Depth → Time'} "
                                    f"conversion finished successfully.\n"
                                    f"Output shape: {converted.shape}")
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", f"Conversion failed:\n{e}")
            self.status_label.setText("Conversion failed")
        finally:
            self.progress_bar.setVisible(False)

    def _update_domain_ui(self):
        if self.depth_mode:
            txt = "⬇  DEPTH DOMAIN"
            col = ACCENT_GREEN
        else:
            txt = "⏱  TIME DOMAIN"
            col = ACCENT_ORANGE
        self.domain_label.setText(txt)
        self.domain_label.setStyleSheet(
            f"color: {col}; font-weight: 800; font-size: 12px; letter-spacing: 0.8px;")
        self.toolbar_domain_lbl.setText(f"  {'⬇ DEPTH' if self.depth_mode else '⏱ TIME'}  ")
        self.toolbar_domain_lbl.setStyleSheet(
            f"color: {col}; font-weight: 800; font-size: 12px; padding: 0 8px; "
            f"border: 1px solid {col}; border-radius: 3px;")
        self.lbl_current_domain.setText(
            f"Domain: {'Depth (m)' if self.depth_mode else 'Time (ms)'}")

    # ──────────────────────────────────────────
    #  NAVIGATION SLOTS
    # ──────────────────────────────────────────
    def update_inline(self, v):
        self.current_inline = int(v)
        self._sync(self.u_spin, self.u_slider, self.current_inline)
        self.render_timer.start(35)

    def update_crossline(self, v):
        self.current_crossline = int(v)
        self._sync(self.v_spin, self.v_slider, self.current_crossline)
        self.render_timer.start(35)

    def change_view_mode(self, *_):
        self.render_timer.start(15)

    def update_colormap(self, *_):
        self.render_timer.start(25)

    def update_gain(self, *_):
        self.render_timer.start(25)

    def update_clip(self, *_):
        self.render_timer.start(25)

    def reset_view(self):
        self.seismic_viewer.reset_view()

    def toggle_fullscreen(self, checked):
        self.showFullScreen() if checked else self.showNormal()

    # ──────────────────────────────────────────
    #  ATTRIBUTE / ML / EXPORT
    # ──────────────────────────────────────────
    def show_attributes_tab(self):
        if self.current_data is not None:
            sr = self.segy_loader.sample_rate if self.segy_loader else None
            self.attribute_panel.set_data(self.current_data, sample_rate_ms=sr, sample_axis=1)
        self.tabs.setCurrentWidget(self.attribute_panel)

    def show_processing_tab(self):
        self.tabs.setCurrentWidget(self.processing_panel)

    def show_ml_dialog(self):
        QMessageBox.information(self, "ML Classification",
                                "Machine Learning classification is available in this section.\n"
                                "Supported: K-Means, DBSCAN, CNN Facies Predictor.")

    def compute_attribute(self, attr_type):
        if not self.segy_loader or self.current_data is None:
            QMessageBox.warning(self, "Warning", "Load seismic data first.")
            return
        self.attribute_panel.compute_attribute(
            attr_type,
            self.current_data,
            sample_rate_ms=self.segy_loader.sample_rate,
            sample_axis=1,
        )
        self.tabs.setCurrentWidget(self.attribute_panel)

    def export_data(self):
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "",
            "NumPy Files (*.npy);;CSV Files (*.csv);;All Files (*)")
        if filepath:
            try:
                if filepath.endswith(".npy"):
                    np.save(filepath, self.current_data)
                else:
                    np.savetxt(filepath, self.current_data, delimiter=",")
                self.statusbar.showMessage(f"Exported: {os.path.basename(filepath)}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Export failed:\n{e}")

    def show_about(self):
        QMessageBox.about(self, "About SeisLab Pro",
                          "<h3>SeisLab Pro Workstation</h3>"
                          "<p><b>Version 2.0</b>  ·  Professional Seismic Analysis Environment</p>"
                          "<p>Features: orthogonal slicing, time ↔ depth conversion, "
                          "attribute extraction, processing workflows, ML classification.</p>"
                          "<p style='color:#888'>© 2025 SeisLab Team</p>")

    # ──────────────────────────────────────────
    #  THEME
    # ──────────────────────────────────────────
    def apply_light_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor(236, 236, 236))
        palette.setColor(QPalette.WindowText,      QColor(30, 30, 30))
        palette.setColor(QPalette.Base,            QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase,   QColor(245, 245, 245))
        palette.setColor(QPalette.Text,            QColor(20, 20, 20))
        palette.setColor(QPalette.Button,          QColor(238, 238, 238))
        palette.setColor(QPalette.ButtonText,      QColor(25, 25, 25))
        palette.setColor(QPalette.Highlight,       QColor(0, 120, 170))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipBase,     QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText,     QColor(20, 20, 20))
        self.setPalette(palette)
        self.setStyleSheet("")

    def apply_dark_theme(self):
        # Compatibility wrapper: keep app in light mode.
        self.apply_light_theme()
        return

        # Legacy dark theme (disabled)
        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor(26, 29, 33))
        palette.setColor(QPalette.WindowText,      QColor(212, 216, 222))
        palette.setColor(QPalette.Base,            QColor(44, 49, 58))
        palette.setColor(QPalette.AlternateBase,   QColor(40, 44, 52))
        palette.setColor(QPalette.Text,            QColor(212, 216, 222))
        palette.setColor(QPalette.Button,          QColor(33, 37, 43))
        palette.setColor(QPalette.ButtonText,      QColor(212, 216, 222))
        palette.setColor(QPalette.Highlight,       QColor(0, 120, 212))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipBase,     QColor(33, 37, 43))
        palette.setColor(QPalette.ToolTipText,     QColor(212, 216, 222))
        self.setPalette(palette)
        self.setStyleSheet(DARK_STYLESHEET)
