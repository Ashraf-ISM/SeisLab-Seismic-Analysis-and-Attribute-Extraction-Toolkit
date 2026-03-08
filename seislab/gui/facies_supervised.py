"""
Supervised facies classification dialog and runner for well-log data.
"""

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


@dataclass
class SupervisedFaciesConfig:
    feature_columns: List[str]
    target_column: str
    output_column: str = "FACIES_SUP"
    model_name: str = "Random Forest"
    test_size: float = 0.25
    random_state: int = 42
    standardize: bool = True
    model_params: Dict[str, object] = field(default_factory=dict)


@dataclass
class SupervisedFaciesResult:
    output_column: str
    prediction_codes: pd.Series
    model_name: str
    used_rows: int
    train_rows: int
    validation_rows: int
    train_accuracy: float
    validation_accuracy: float
    label_mapping: Dict[int, object] = field(default_factory=dict)


class SupervisedFaciesClassifier:
    """Run supervised facies classification on well-log data."""

    MODEL_NAMES = (
        "Random Forest",
        "Logistic Regression",
        "Support Vector Machine",
        "K-Nearest Neighbors",
    )

    def __init__(self, config: SupervisedFaciesConfig):
        self.config = config

    def run(self, df: pd.DataFrame) -> SupervisedFaciesResult:
        required = list(dict.fromkeys(self.config.feature_columns + [self.config.target_column]))
        missing = [column for column in required if column not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {', '.join(missing)}")

        work_df = df[required].dropna().copy()
        if work_df.empty:
            raise ValueError("No valid samples remain after removing rows with missing values.")
        if len(work_df) < 8:
            raise ValueError("At least 8 complete rows are required for supervised classification.")

        target_codes, target_labels = pd.factorize(work_df[self.config.target_column], sort=True)
        if len(target_labels) < 2:
            raise ValueError("Target column must contain at least two facies classes.")

        x_data = work_df[self.config.feature_columns]
        y_data = target_codes
        stratify = self._build_stratify_target(y_data, len(target_labels), len(work_df))

        try:
            split = train_test_split(
                x_data,
                y_data,
                test_size=self.config.test_size,
                random_state=self.config.random_state,
                stratify=stratify,
            )
        except ValueError:
            split = train_test_split(
                x_data,
                y_data,
                test_size=self.config.test_size,
                random_state=self.config.random_state,
                stratify=None,
            )

        x_train, x_test, y_train, y_test = split
        model = self._build_pipeline(len(x_train))
        model.fit(x_train, y_train)

        predicted_codes = model.predict(x_data)
        prediction_series = pd.Series(np.nan, index=df.index, dtype=float)
        prediction_series.loc[work_df.index] = predicted_codes.astype(float)

        return SupervisedFaciesResult(
            output_column=self.config.output_column,
            prediction_codes=prediction_series,
            model_name=self.config.model_name,
            used_rows=len(work_df),
            train_rows=len(x_train),
            validation_rows=len(x_test),
            train_accuracy=float(model.score(x_train, y_train)),
            validation_accuracy=float(model.score(x_test, y_test)),
            label_mapping={int(code): label for code, label in enumerate(target_labels.tolist())},
        )

    def _build_stratify_target(self, y_data, class_count: int, row_count: int):
        counts = pd.Series(y_data).value_counts()
        test_rows = max(1, int(round(row_count * self.config.test_size)))
        if counts.min() < 2 or test_rows < class_count:
            return None
        return y_data

    def _build_pipeline(self, train_size: int) -> Pipeline:
        steps = []
        if self.config.standardize:
            steps.append(("scaler", StandardScaler()))
        steps.append(("model", self._build_model(train_size)))
        return Pipeline(steps)

    def _build_model(self, train_size: int):
        params = dict(self.config.model_params)
        name = self.config.model_name

        if name == "Random Forest":
            max_depth = params.get("max_depth") or None
            return RandomForestClassifier(
                n_estimators=int(params.get("n_estimators", 200)),
                max_depth=max_depth,
                min_samples_leaf=int(params.get("min_samples_leaf", 1)),
                random_state=self.config.random_state,
            )

        if name == "Logistic Regression":
            return LogisticRegression(
                C=float(params.get("c", 1.0)),
                max_iter=int(params.get("max_iter", 1000)),
                random_state=self.config.random_state,
                multi_class="auto",
            )

        if name == "Support Vector Machine":
            return SVC(
                C=float(params.get("c", 1.0)),
                kernel=str(params.get("kernel", "rbf")),
                random_state=self.config.random_state,
            )

        if name == "K-Nearest Neighbors":
            return KNeighborsClassifier(
                n_neighbors=max(1, min(int(params.get("n_neighbors", 5)), train_size)),
                weights=str(params.get("weights", "uniform")),
            )

        raise ValueError(f"Unsupported supervised method: {name}")


class SupervisedFaciesDialog(QDialog):
    """Dialog for configuring supervised facies classification."""

    def __init__(self, well, parent=None):
        super().__init__(parent)
        self.well = well
        self.result_data = None
        self.config_data = None

        self.setWindowTitle("Supervised Facies Classification")
        self.resize(540, 720)
        self._build_ui()
        self._populate_columns()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Train a classifier from an existing facies target column and write "
            "predicted facies codes back to the active well."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        feature_group = QGroupBox("Feature Logs")
        feature_layout = QVBoxLayout(feature_group)
        feature_layout.addWidget(QLabel("Select the well logs used as predictor features."))

        self.feature_list = QListWidget()
        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.feature_list.setMinimumHeight(180)
        feature_layout.addWidget(self.feature_list)

        feature_actions = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.clear_btn = QPushButton("Clear")
        feature_actions.addWidget(self.select_all_btn)
        feature_actions.addWidget(self.clear_btn)
        feature_layout.addLayout(feature_actions)
        layout.addWidget(feature_group)

        setup_group = QGroupBox("Training Setup")
        setup_form = QFormLayout(setup_group)
        self.target_combo = QComboBox()
        self.output_edit = QLineEdit("FACIES_SUP")
        self.model_combo = QComboBox()
        self.model_combo.addItems(SupervisedFaciesClassifier.MODEL_NAMES)
        self.standardize_cb = QCheckBox("Standardize feature logs before fitting")
        self.standardize_cb.setChecked(True)
        self.test_size_spin = QDoubleSpinBox()
        self.test_size_spin.setRange(0.10, 0.50)
        self.test_size_spin.setSingleStep(0.05)
        self.test_size_spin.setValue(0.25)
        self.test_size_spin.setDecimals(2)
        self.random_state_spin = QSpinBox()
        self.random_state_spin.setRange(0, 99999)
        self.random_state_spin.setValue(42)
        setup_form.addRow("Target facies column:", self.target_combo)
        setup_form.addRow("Output facies column:", self.output_edit)
        setup_form.addRow("Model:", self.model_combo)
        setup_form.addRow("Validation split:", self.test_size_spin)
        setup_form.addRow("Random state:", self.random_state_spin)
        setup_form.addRow("", self.standardize_cb)
        layout.addWidget(setup_group)

        params_group = QGroupBox("Method Options")
        params_layout = QVBoxLayout(params_group)
        self.params_stack = QStackedWidget()
        params_layout.addWidget(self.params_stack)
        layout.addWidget(params_group)

        self.params_stack.addWidget(self._build_random_forest_page())
        self.params_stack.addWidget(self._build_logistic_page())
        self.params_stack.addWidget(self._build_svm_page())
        self.params_stack.addWidget(self._build_knn_page())

        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.run_button = self.buttons.addButton(
            "Run Classification",
            QDialogButtonBox.AcceptRole,
        )
        layout.addWidget(self.buttons)

        self.select_all_btn.clicked.connect(self._select_all_features)
        self.clear_btn.clicked.connect(self.feature_list.clearSelection)
        self.target_combo.currentTextChanged.connect(self._sync_target_selection)
        self.model_combo.currentIndexChanged.connect(self.params_stack.setCurrentIndex)
        self.buttons.accepted.connect(self._run_classification)
        self.buttons.rejected.connect(self.reject)

    def _build_random_forest_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.rf_estimators = QSpinBox()
        self.rf_estimators.setRange(20, 1000)
        self.rf_estimators.setValue(200)
        self.rf_max_depth = QSpinBox()
        self.rf_max_depth.setRange(0, 100)
        self.rf_max_depth.setValue(0)
        self.rf_max_depth.setSpecialValueText("Auto")
        self.rf_min_leaf = QSpinBox()
        self.rf_min_leaf.setRange(1, 25)
        self.rf_min_leaf.setValue(1)
        form.addRow("Trees:", self.rf_estimators)
        form.addRow("Max depth:", self.rf_max_depth)
        form.addRow("Min leaf samples:", self.rf_min_leaf)
        return page

    def _build_logistic_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.logreg_c = QDoubleSpinBox()
        self.logreg_c.setRange(0.01, 1000.0)
        self.logreg_c.setDecimals(2)
        self.logreg_c.setSingleStep(0.25)
        self.logreg_c.setValue(1.0)
        self.logreg_iter = QSpinBox()
        self.logreg_iter.setRange(100, 5000)
        self.logreg_iter.setSingleStep(100)
        self.logreg_iter.setValue(1000)
        form.addRow("Regularization C:", self.logreg_c)
        form.addRow("Max iterations:", self.logreg_iter)
        return page

    def _build_svm_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.svm_c = QDoubleSpinBox()
        self.svm_c.setRange(0.01, 1000.0)
        self.svm_c.setDecimals(2)
        self.svm_c.setSingleStep(0.25)
        self.svm_c.setValue(1.0)
        self.svm_kernel = QComboBox()
        self.svm_kernel.addItems(["rbf", "linear", "poly"])
        form.addRow("Penalty C:", self.svm_c)
        form.addRow("Kernel:", self.svm_kernel)
        return page

    def _build_knn_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.knn_neighbors = QSpinBox()
        self.knn_neighbors.setRange(1, 50)
        self.knn_neighbors.setValue(5)
        self.knn_weights = QComboBox()
        self.knn_weights.addItems(["uniform", "distance"])
        form.addRow("Neighbors:", self.knn_neighbors)
        form.addRow("Weights:", self.knn_weights)
        return page

    def _populate_columns(self):
        columns = [column for column in self.well.curve_names if column != self.well.depth_col]
        self.feature_list.clear()
        self.target_combo.clear()

        for column in columns:
            item = QListWidgetItem(column)
            self.feature_list.addItem(item)
            self.target_combo.addItem(column)

        if columns:
            self.target_combo.setCurrentIndex(0)
        self._apply_default_feature_selection()

    def _apply_default_feature_selection(self):
        target = self.target_combo.currentText()
        selected = 0
        for index in range(self.feature_list.count()):
            item = self.feature_list.item(index)
            should_select = item.text() != target and selected < 4
            item.setSelected(should_select)
            if should_select:
                selected += 1

    def _select_all_features(self):
        target = self.target_combo.currentText()
        for index in range(self.feature_list.count()):
            item = self.feature_list.item(index)
            item.setSelected(item.text() != target)

    def _sync_target_selection(self):
        target = self.target_combo.currentText()
        selected_features = [
            self.feature_list.item(index).text()
            for index in range(self.feature_list.count())
            if self.feature_list.item(index).isSelected()
        ]

        for index in range(self.feature_list.count()):
            item = self.feature_list.item(index)
            if item.text() == target:
                item.setSelected(False)

        if not [name for name in selected_features if name != target]:
            self._apply_default_feature_selection()

    def _selected_features(self) -> List[str]:
        return [item.text() for item in self.feature_list.selectedItems()]

    def _build_config(self) -> SupervisedFaciesConfig:
        features = [name for name in self._selected_features() if name != self.target_combo.currentText()]
        if not features:
            raise ValueError("Select at least one feature log that is different from the target column.")

        output_column = self.output_edit.text().strip() or "FACIES_SUP"
        model_name = self.model_combo.currentText()
        model_params = self._current_model_params()

        return SupervisedFaciesConfig(
            feature_columns=features,
            target_column=self.target_combo.currentText(),
            output_column=output_column,
            model_name=model_name,
            test_size=self.test_size_spin.value(),
            random_state=self.random_state_spin.value(),
            standardize=self.standardize_cb.isChecked(),
            model_params=model_params,
        )

    def _current_model_params(self) -> Dict[str, object]:
        model_name = self.model_combo.currentText()

        if model_name == "Random Forest":
            return {
                "n_estimators": self.rf_estimators.value(),
                "max_depth": self.rf_max_depth.value(),
                "min_samples_leaf": self.rf_min_leaf.value(),
            }

        if model_name == "Logistic Regression":
            return {
                "c": self.logreg_c.value(),
                "max_iter": self.logreg_iter.value(),
            }

        if model_name == "Support Vector Machine":
            return {
                "c": self.svm_c.value(),
                "kernel": self.svm_kernel.currentText(),
            }

        return {
            "n_neighbors": self.knn_neighbors.value(),
            "weights": self.knn_weights.currentText(),
        }

    def _run_classification(self):
        try:
            config = self._build_config()
            self.config_data = config
            self.result_data = SupervisedFaciesClassifier(config).run(self.well.df)
        except Exception as exc:
            QMessageBox.critical(self, "Supervised Classification", str(exc))
            return

        self.accept()

    def get_result(self):
        return self.result_data

    def get_config(self):
        return self.config_data or self._build_config()
