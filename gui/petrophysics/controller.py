import os
from typing import Dict, List, Optional

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QPushButton,
    QTableWidgetItem,
    QTreeWidgetItem,
)

from .calculations import (
    compute_archie_sw,
    compute_density_porosity,
    compute_effective_porosity,
    compute_nd_porosity,
    compute_net_pay_summary,
    compute_sonic_porosity,
    compute_timur_perm,
    compute_vshale,
)
from .data_loading import load_well, unique_well_name
from .models import WellDataset
from .plotting import MatplotlibCanvas, plot_crossplot, plot_log_view
from .plotting import plot_histogram, plot_multi_track, plot_triple_combo


class PetrophysicsWorkstationController(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "petrophysicsWorkstaton.ui")
        uic.loadUi(ui_path, self)

        self.wells: Dict[str, WellDataset] = {}
        self.active_well_name: Optional[str] = None

        self.log_canvas = MatplotlibCanvas(self)
        self.cross_canvas = MatplotlibCanvas(self)
        self.logCanvasLayout.addWidget(self.log_canvas)
        self.crossplotCanvasLayout.insertWidget(0, self.cross_canvas)

        self._wire_actions()
        self._log("Petrophysics workstation ready.")

    def _wire_actions(self):
        self.btnBrowseFile.clicked.connect(self._browse_file)
        self.btnImport.clicked.connect(self._import_from_path)
        self.btnBatchImport.clicked.connect(self._batch_import)
        self.btnAddWell.clicked.connect(self._browse_file)
        self.btnDanger.clicked.connect(self._remove_selected_well)

        self.comboLogDisplayWell.currentTextChanged.connect(self._set_active_well)
        self.comboPetroWell.currentTextChanged.connect(self._set_active_well)

        self.btnFitAll.clicked.connect(self._plot_log_display)
        self.btnZoomIn.clicked.connect(lambda: self._zoom_depth(0.9))
        self.btnZoomOut.clicked.connect(lambda: self._zoom_depth(1.1))

        self.btnUpdateCrossplot.clicked.connect(self._plot_crossplot)

        self.btnRunAll.clicked.connect(self._run_full_pipeline)

        for button in self.findChildren(QPushButton, "btnCalculate"):
            button.clicked.connect(self._dispatch_calculation)

        self._ensure_plot_modes()

    def _ensure_plot_modes(self):
        required = [
            "Histogram",
            "Crossplot",
            "Triple Combo Plot",
            "Multi-Track Plot",
        ]
        existing = [self.comboCrossplotType.itemText(i) for i in range(self.comboCrossplotType.count())]
        self.comboCrossplotType.clear()
        self.comboCrossplotType.addItems(required)
        for item in existing:
            if item not in required:
                self.comboCrossplotType.addItem(item)

    def _log(self, message: str):
        if hasattr(self, "txtOutputLog"):
            self.txtOutputLog.append(message)
        if hasattr(self, "statusbar"):
            self.statusbar.showMessage(message)

    def _active_well(self) -> Optional[WellDataset]:
        return self.wells.get(self.active_well_name or "")

    def _curve_from_combo(self, combo_text: str, well: WellDataset) -> Optional[str]:
        if combo_text in well.df.columns:
            return combo_text
        short = combo_text.split("(")[0].strip()
        if short in well.df.columns:
            return short
        short2 = combo_text.split()[0].strip()
        if short2 in well.df.columns:
            return short2
        return None

    def _update_well_tree(self):
        self.treeWellExplorer.clear()
        for well in self.wells.values():
            root = QTreeWidgetItem(self.treeWellExplorer, [well.name, ""])
            root.setData(0, Qt.UserRole, well.name)
            curves_node = QTreeWidgetItem(root, ["Curves", ""])
            for curve in well.curve_names:
                unit = well.curves.get(curve, {}).get("unit", "")
                QTreeWidgetItem(curves_node, [curve, unit])
            root.setExpanded(True)
            curves_node.setExpanded(True)

    def _set_active_well(self, well_name: str):
        if well_name in self.wells:
            self.active_well_name = well_name
            self._sync_well_combos()
            self._populate_tables_for_active_well()
            self._populate_curve_controls()
            self._plot_log_display()
            self._plot_crossplot()

    def _sync_well_combos(self):
        names = list(self.wells.keys())
        for combo in (self.comboLogDisplayWell, self.comboPetroWell):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(names)
            if current in names:
                combo.setCurrentText(current)
            elif self.active_well_name in names:
                combo.setCurrentText(self.active_well_name)
            combo.blockSignals(False)

    def _populate_tables_for_active_well(self):
        well = self._active_well()
        if not well:
            return

        # Header table
        self.tableHeaderInfo.setRowCount(0)
        rows = list(well.header.items())
        if not rows:
            rows = [
                ("WELL", {"unit": "", "value": well.name, "desc": "Well Name"}),
                ("FILE", {"unit": "", "value": os.path.basename(well.filename), "desc": "Source file"}),
            ]
        self.tableHeaderInfo.setRowCount(len(rows))
        for r, (key, meta) in enumerate(rows):
            values = [key, meta.get("unit", ""), str(meta.get("value", "")), meta.get("desc", "")]
            for c, value in enumerate(values):
                self.tableHeaderInfo.setItem(r, c, QTableWidgetItem(str(value)))

        # Curve list table
        self.tableCurveList.setRowCount(len(well.curve_names))
        for r, curve in enumerate(well.curve_names):
            unit = well.curves.get(curve, {}).get("unit", "")
            desc = well.curves.get(curve, {}).get("desc", "")
            vals = ["Yes", curve, curve, unit, "", "", "0", "", "", desc, "", ""]
            for c, value in enumerate(vals[: self.tableCurveList.columnCount()]):
                self.tableCurveList.setItem(r, c, QTableWidgetItem(str(value)))

    def _populate_curve_controls(self):
        well = self._active_well()
        if not well:
            return

        curve_names = well.curve_names
        curve_labels = [f"{c} ({well.curves.get(c, {}).get('unit', '')})".strip() for c in curve_names]

        combos = [
            self.comboVshaleGR,
            self.comboDenRHOB,
            self.comboNDRHOB,
            self.comboNDNPHI,
            self.comboSonicDT,
            self.comboPHITSource,
            self.comboPHIEVshale,
            self.comboSwRt,
            self.comboSwPHIE,
            self.comboPermPHIE,
            self.comboCrossX,
            self.comboCrossY,
            self.comboCrossColor,
            self.comboCrossSize,
        ]
        for combo in combos:
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(curve_labels)
            if current:
                combo.setCurrentText(current)
            combo.blockSignals(False)

        dmin = well.depth_min or 0
        dmax = well.depth_max or dmin + 1
        self.spinDepthFrom.setValue(dmin)
        self.spinDepthTo.setValue(dmax)
        self.spinCrossDepthFrom.setValue(dmin)
        self.spinCrossDepthTo.setValue(dmax)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select well file",
            "",
            "Well files (*.las *.LAS *.csv *.CSV *.txt *.TXT *.xlsx *.xls);;All files (*)",
        )
        if path:
            self.lineEditFilePath.setText(path)

    def _import_from_path(self):
        path = self.lineEditFilePath.text().strip()
        if not path:
            QMessageBox.information(self, "Import", "Pick a file first.")
            return

        try:
            well = load_well(path, replace_nulls=self.chkNullReplace.isChecked())
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            return

        well.name = unique_well_name(well.name, self.wells)
        self.wells[well.name] = well
        self.active_well_name = well.name

        self.progressImport.setValue(100)
        self.progressImport.setFormat(f"Imported: {well.name}")
        self._update_well_tree()
        self._sync_well_combos()
        self._populate_tables_for_active_well()
        self._populate_curve_controls()
        self._plot_log_display()
        self._plot_crossplot()
        self._log(f"Imported {well.name} with {len(well.curve_names)} curves.")

    def _batch_import(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select well files",
            "",
            "Well files (*.las *.LAS *.csv *.CSV *.txt *.TXT *.xlsx *.xls);;All files (*)",
        )
        if not paths:
            return

        loaded = 0
        for path in paths:
            try:
                well = load_well(path, replace_nulls=self.chkNullReplace.isChecked())
                well.name = unique_well_name(well.name, self.wells)
                self.wells[well.name] = well
                self.active_well_name = well.name
                loaded += 1
            except Exception as exc:
                self._log(f"Failed: {os.path.basename(path)} - {exc}")

        self._update_well_tree()
        self._sync_well_combos()
        self._populate_tables_for_active_well()
        self._populate_curve_controls()
        self._plot_log_display()
        self._plot_crossplot()

        self.progressImport.setValue(100)
        self.progressImport.setFormat(f"Imported {loaded}/{len(paths)}")
        self._log(f"Batch import completed: {loaded}/{len(paths)} files loaded.")

    def _remove_selected_well(self):
        item = self.treeWellExplorer.currentItem()
        if not item:
            return
        well_name = item.data(0, Qt.UserRole)
        if not well_name:
            parent = item
            while parent and not parent.data(0, Qt.UserRole):
                parent = parent.parent()
            well_name = parent.data(0, Qt.UserRole) if parent else None

        if well_name and well_name in self.wells:
            self.wells.pop(well_name)
            self.active_well_name = next(iter(self.wells.keys()), None)
            self._update_well_tree()
            self._sync_well_combos()
            self._populate_tables_for_active_well()
            self._populate_curve_controls()
            self._plot_log_display()
            self._plot_crossplot()
            self._log(f"Removed well: {well_name}")

    def _plot_log_display(self):
        well = self._active_well()
        if not well:
            return

        curve_a = well.curve_names[0] if well.curve_names else None
        curve_b = well.curve_names[1] if len(well.curve_names) > 1 else None
        plot_log_view(
            self.log_canvas,
            well.df,
            well.depth_col,
            curve_a,
            curve_b,
            self.spinDepthFrom.value(),
            self.spinDepthTo.value(),
        )

    def _zoom_depth(self, factor: float):
        mid = 0.5 * (self.spinDepthFrom.value() + self.spinDepthTo.value())
        half = 0.5 * (self.spinDepthTo.value() - self.spinDepthFrom.value()) * factor
        self.spinDepthFrom.setValue(max(0, mid - half))
        self.spinDepthTo.setValue(mid + half)
        self._plot_log_display()

    def _plot_crossplot(self):
        well = self._active_well()
        if not well:
            return

        mode = self.comboCrossplotType.currentText().strip().lower()
        if "histogram" in mode:
            self._plot_histogram_mode(well)
            return
        if "triple" in mode:
            self._plot_triple_combo_mode(well)
            return
        if "multi-track" in mode:
            self._plot_multi_track_mode(well)
            return

        x_curve = self._curve_from_combo(self.comboCrossX.currentText(), well)
        y_curve = self._curve_from_combo(self.comboCrossY.currentText(), well)
        color_curve = self._curve_from_combo(self.comboCrossColor.currentText(), well)
        x_log = self.comboCrossXScale.currentText().lower() == "log"
        y_log = self.comboCrossYScale.currentText().lower() == "log"

        n, r2, slope = plot_crossplot(self.cross_canvas, well.df, x_curve or "", y_curve or "", color_curve, x_log, y_log)
        self.lblCrossplotN.setText(f"N: {n}")
        self.lblCrossplotR2.setText(f"R²: {r2:.4f}" if r2 == r2 else "R²: —")
        self.lblCrossplotSlope.setText(f"Slope: {slope:.4f}" if slope == slope else "Slope: —")

    def _curve_choices(self, well: WellDataset):
        return [col for col in well.df.columns if col != well.depth_col]

    def _ask_single_curve(self, title: str, curves):
        if not curves:
            return None
        curve, ok = QInputDialog.getItem(self, title, "Curve:", curves, 0, False)
        return curve if ok and curve else None

    def _ask_multi_curves(self, title: str, curves, min_required: int = 1):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget(dialog)
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        for curve in curves:
            item = QListWidgetItem(curve)
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return []
        selected = [item.text() for item in list_widget.selectedItems()]
        if len(selected) < min_required:
            QMessageBox.information(self, "Selection", f"Please select at least {min_required} curve(s).")
            return []
        return selected

    def _plot_histogram_mode(self, well: WellDataset):
        curve = self._curve_from_combo(self.comboCrossX.currentText(), well)
        if not curve:
            curve = self._ask_single_curve("Histogram Curve", self._curve_choices(well))
        if not curve:
            return

        bins, ok = QInputDialog.getInt(self, "Histogram Bins", "Bins:", 40, 5, 200, 1)
        if not ok:
            return
        plot_histogram(self.cross_canvas, well.df, curve, bins=bins)
        self.lblCrossplotN.setText("N: histogram")
        self.lblCrossplotR2.setText("R²: —")
        self.lblCrossplotSlope.setText("Slope: —")

    def _plot_triple_combo_mode(self, well: WellDataset):
        curves = self._curve_choices(well)
        if not curves:
            return

        gr_curve = self._ask_single_curve("Track 1 - Gamma Ray", curves)
        if not gr_curve:
            return
        cal_curve = self._ask_single_curve("Track 1 - Caliper", curves)
        if not cal_curve:
            return
        res_curve = self._ask_single_curve("Track 2 - Resistivity", curves)
        if not res_curve:
            return
        den_curve = self._ask_single_curve("Track 3 - Density", curves)
        if not den_curve:
            return
        por_curve = self._ask_single_curve("Track 3 - Porosity", curves)
        if not por_curve:
            return

        plot_triple_combo(
            self.cross_canvas,
            well.df,
            well.depth_col,
            [gr_curve, cal_curve],
            res_curve,
            [den_curve, por_curve],
        )
        self.lblCrossplotN.setText("N: triple combo")
        self.lblCrossplotR2.setText("R²: —")
        self.lblCrossplotSlope.setText("Slope: —")

    def _plot_multi_track_mode(self, well: WellDataset):
        curves = self._curve_choices(well)
        selected = self._ask_multi_curves("Select Curves for Multi-Track", curves, min_required=1)
        if not selected:
            return

        plot_multi_track(self.cross_canvas, well.df, well.depth_col, selected)
        self.lblCrossplotN.setText(f"N: {len(selected)} tracks")
        self.lblCrossplotR2.setText("R²: —")
        self.lblCrossplotSlope.setText("Slope: —")

    def _dispatch_calculation(self):
        sender = self.sender()
        tab_name = self._parent_tab_name(sender)
        if tab_name == "tabVshale":
            self._calculate_vshale()
        elif tab_name == "tabPorosity":
            self._calculate_porosity()
        elif tab_name == "tabWaterSat":
            self._calculate_sw()
        elif tab_name == "tabPermeability":
            self._calculate_perm()
        elif tab_name == "tabNetPay":
            self._calculate_netpay()

    def _parent_tab_name(self, widget) -> str:
        current = widget
        while current is not None:
            name = getattr(current, "objectName", lambda: "")()
            if name.startswith("tab"):
                return name
            current = current.parent()
        return ""

    def _calculate_vshale(self):
        well = self._active_well()
        if not well:
            return
        gr = self._curve_from_combo(self.comboVshaleGR.currentText(), well)
        if not gr:
            return
        output = self.lineVshaleOutput.text().strip() or "VSHALE_GR"
        series = compute_vshale(
            well.df,
            gr,
            self.spinGRClean.value(),
            self.spinGRShale.value(),
            self.comboVshaleMethod.currentText(),
            self.chkConstrainVshale.isChecked(),
        )
        well.df[output] = series

        stats = {
            "Min": series.min(),
            "P10": series.quantile(0.10),
            "P50": series.quantile(0.50),
            "P90": series.quantile(0.90),
            "Max": series.max(),
        }
        self.tableGRStats.setRowCount(len(stats))
        for r, (k, v) in enumerate(stats.items()):
            self.tableGRStats.setItem(r, 0, QTableWidgetItem(k))
            self.tableGRStats.setItem(r, 1, QTableWidgetItem(f"{v:.4f}"))

        self._populate_curve_controls()
        self._log(f"Computed {output} for {well.name}")

    def _calculate_porosity(self):
        well = self._active_well()
        if not well:
            return

        rhob = self._curve_from_combo(self.comboDenRHOB.currentText(), well)
        nphi = self._curve_from_combo(self.comboNDNPHI.currentText(), well)
        dt = self._curve_from_combo(self.comboSonicDT.currentText(), well)
        vsh = self._curve_from_combo(self.comboPHIEVshale.currentText(), well)

        if rhob:
            phid_name = self.linePHIDOutput.text().strip() or "PHID"
            well.df[phid_name] = compute_density_porosity(
                well.df[rhob], self.spinRhoMatrix.value(), self.spinRhoFluid.value()
            )
        else:
            phid_name = "PHID"

        if nphi and phid_name in well.df:
            phind_name = self.lineNDOutput.text().strip() or "PHIND"
            well.df[phind_name] = compute_nd_porosity(
                well.df[nphi],
                well.df[phid_name],
                quadratic=self.radioNDQuadratic.isChecked(),
            )
        else:
            phind_name = "PHIND"

        if dt:
            phis_name = self.lineSonicOutput.text().strip() or "PHIS"
            well.df[phis_name] = compute_sonic_porosity(
                well.df[dt], self.spinDTma.value(), self.spinDTfl.value()
            )

        phit = self._curve_from_combo(self.comboPHITSource.currentText(), well)
        if phit and vsh and phit in well.df and vsh in well.df:
            well.df["PHIE"] = compute_effective_porosity(
                well.df[phit], well.df[vsh], self.spinPhiShale.value()
            )

        self._populate_curve_controls()
        self._log(f"Computed porosity curves for {well.name}")

    def _calculate_sw(self):
        well = self._active_well()
        if not well:
            return

        rt = self._curve_from_combo(self.comboSwRt.currentText(), well)
        phie = self._curve_from_combo(self.comboSwPHIE.currentText(), well)
        if not rt or not phie:
            return

        output = self.lineSwOutput.text().strip() or "SW_ARCHIE"
        well.df[output] = compute_archie_sw(
            well.df[rt],
            well.df[phie],
            rw=self.spinRw.value(),
            a=self.spinArchieA.value(),
            m=self.spinArchieM.value(),
            n=self.spinArchieN.value(),
        )
        well.df["BVW"] = (well.df[phie] * well.df[output]).clip(lower=0)

        self._populate_curve_controls()
        self._log(f"Computed {output} and BVW for {well.name}")

    def _calculate_perm(self):
        well = self._active_well()
        if not well:
            return

        phie = self._curve_from_combo(self.comboPermPHIE.currentText(), well)
        sw = self._curve_from_combo(self.comboSwPHIE.currentText(), well)
        if not phie:
            return
        sw_series = well.df[sw] if sw and sw in well.df else well.df.get("SW_ARCHIE")
        if sw_series is None:
            sw_series = well.df[phie] * 0 + self.spinSwirr.value()

        output = self.linePermOutput.text().strip() or "PERM_TIMUR"
        well.df[output] = compute_timur_perm(
            well.df[phie],
            sw_series,
            c=self.spinPermC.value(),
            a=self.spinPermA.value(),
            b=self.spinPermB.value(),
        )
        if self.chkPermLog.isChecked():
            well.df[f"LOG10_{output}"] = well.df[output].clip(lower=1e-9).apply(lambda v: float(__import__('math').log10(v)))

        self._populate_curve_controls()
        self._log(f"Computed {output} for {well.name}")

    def _calculate_netpay(self):
        well = self._active_well()
        if not well:
            return

        depth = well.depth_col
        vsh = self.lineVshaleOutput.text().strip() or "VSHALE_GR"
        phie = "PHIE"
        sw = self.lineSwOutput.text().strip() or "SW_ARCHIE"
        perm = self.linePermOutput.text().strip() or "PERM_TIMUR"
        if not all(c in well.df.columns for c in [vsh, phie, sw, perm]):
            QMessageBox.warning(self, "Net Pay", "Run Vshale, Porosity, Sw, and Permeability calculations first.")
            return

        summary, flag = compute_net_pay_summary(
            well.df,
            depth,
            self.spinNetPayTop.value(),
            self.spinNetPayBase.value(),
            vsh,
            phie,
            sw,
            perm,
            self.spinVshCutoff.value(),
            self.spinPHIECutoff.value(),
            self.spinSwCutoff.value(),
            self.spinKCutoff.value(),
        )
        well.df["PAY_FLAG"] = flag.astype(int)

        rows = [
            ("Gross", summary["gross_m"], "m"),
            ("Net Reservoir", summary["net_res_m"], "m"),
            ("Net Pay", summary["net_pay_m"], "m"),
            ("NTG", summary["ntg"], "frac"),
        ]
        self.tableNetPaySummary.setRowCount(len(rows))
        for r, (name, value, unit) in enumerate(rows):
            self.tableNetPaySummary.setItem(r, 0, QTableWidgetItem(name))
            self.tableNetPaySummary.setItem(r, 1, QTableWidgetItem(f"{value:.4f}"))
            self.tableNetPaySummary.setItem(r, 2, QTableWidgetItem(unit))

        self._populate_curve_controls()
        self._log(f"Computed net pay summary for {well.name}")

    def _run_full_pipeline(self):
        well_targets: List[WellDataset]
        if self.radioBatchAllWells.isChecked():
            well_targets = list(self.wells.values())
        else:
            well = self._active_well()
            well_targets = [well] if well else []

        if not well_targets:
            return

        self.progressBatchCalc.setValue(0)
        self.txtBatchLog.clear()

        for i, well in enumerate(well_targets, start=1):
            self.active_well_name = well.name
            self._sync_well_combos()
            self._populate_curve_controls()

            if self.chkBatchVshale.isChecked():
                self._calculate_vshale()
            if self.chkBatchPoro.isChecked():
                self._calculate_porosity()
            if self.chkBatchSw.isChecked():
                self._calculate_sw()
            if self.chkBatchPerm.isChecked():
                self._calculate_perm()
            if self.chkBatchNetPay.isChecked():
                self._calculate_netpay()

            self.txtBatchLog.append(f"Completed pipeline for {well.name}")
            pct = int((i / len(well_targets)) * 100)
            self.progressBatchCalc.setValue(pct)
            self.progressBatchCalc.setFormat(f"Processed {i}/{len(well_targets)} wells")

        self._log("Full petro pipeline completed.")
