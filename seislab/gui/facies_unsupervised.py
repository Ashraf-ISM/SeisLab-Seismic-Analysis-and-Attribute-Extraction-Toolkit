"""
Unsupervised facies classification dialog and runner for well-log data.
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
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


@dataclass
class UnsupervisedFaciesConfig:
    feature_columns: List[str]
    output_column: str = "FACIES_UNSUP"
    model_name: str = "K-Means"
    standardize: bool = True
    random_state: int = 42
    model_params: Dict[str, object] = field(default_factory=dict)


@dataclass
class UnsupervisedFaciesResult:
    output_column: str
    prediction_codes: pd.Series
    model_name: str
    used_rows: int
    cluster_count: int
    noise_points: int


class UnsupervisedFaciesClassifier:
    """Run unsupervised facies classification on well-log data."""

    MODEL_NAMES = (
        "K-Means",
        "Gaussian Mixture",
        "DBSCAN",
        "Agglomerative Clustering",
    )

    def __init__(self, config: UnsupervisedFaciesConfig):
        self.config = config

    def run(self, df: pd.DataFrame) -> UnsupervisedFaciesResult:
        missing = [column for column in self.config.feature_columns if column not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {', '.join(missing)}")

        work_df = df[self.config.feature_columns].dropna().copy()
        if work_df.empty:
            raise ValueError("No valid samples remain after removing rows with missing values.")
        if len(work_df) < 4:
            raise ValueError("At least 4 complete rows are required for unsupervised classification.")

        feature_matrix = work_df.to_numpy(dtype=float)
        if self.config.standardize:
            feature_matrix = StandardScaler().fit_transform(feature_matrix)

        labels = self._fit_predict(feature_matrix, len(work_df))

        prediction_series = pd.Series(np.nan, index=df.index, dtype=float)
        prediction_series.loc[work_df.index] = labels.astype(float)

        unique_labels = set(int(label) for label in np.unique(labels))
        noise_points = int(np.sum(labels == -1))
        cluster_count = len(unique_labels - {-1})

        return UnsupervisedFaciesResult(
            output_column=self.config.output_column,
            prediction_codes=prediction_series,
            model_name=self.config.model_name,
            used_rows=len(work_df),
            cluster_count=cluster_count,
            noise_points=noise_points,
        )

    def _fit_predict(self, feature_matrix: np.ndarray, row_count: int) -> np.ndarray:
        params = dict(self.config.model_params)
        name = self.config.model_name

        if name == "K-Means":
            cluster_count = int(params.get("n_clusters", 5))
            self._validate_cluster_count(cluster_count, row_count, name)
            model = KMeans(
                n_clusters=cluster_count,
                init=str(params.get("init", "k-means++")),
                n_init=int(params.get("n_init", 10)),
                random_state=self.config.random_state,
            )
            return model.fit_predict(feature_matrix)

        if name == "Gaussian Mixture":
            component_count = int(params.get("n_components", 5))
            self._validate_cluster_count(component_count, row_count, name)
            model = GaussianMixture(
                n_components=component_count,
                covariance_type=str(params.get("covariance_type", "full")),
                random_state=self.config.random_state,
            )
            model.fit(feature_matrix)
            return model.predict(feature_matrix)

        if name == "DBSCAN":
            model = DBSCAN(
                eps=float(params.get("eps", 0.5)),
                min_samples=int(params.get("min_samples", 5)),
            )
            return model.fit_predict(feature_matrix)

        if name == "Agglomerative Clustering":
            cluster_count = int(params.get("n_clusters", 5))
            self._validate_cluster_count(cluster_count, row_count, name)
            model = AgglomerativeClustering(
                n_clusters=cluster_count,
                linkage=str(params.get("linkage", "ward")),
            )
            return model.fit_predict(feature_matrix)

        raise ValueError(f"Unsupported unsupervised method: {name}")

    def _validate_cluster_count(self, cluster_count: int, row_count: int, method_name: str):
        if cluster_count < 2:
            raise ValueError(f"{method_name} requires at least 2 clusters.")
        if cluster_count >= row_count:
            raise ValueError(f"{method_name} requires cluster count smaller than the number of valid rows.")


class UnsupervisedFaciesDialog(QDialog):
    """Dialog for configuring unsupervised facies classification."""

    def __init__(self, well, parent=None):
        super().__init__(parent)
        self.well = well
        self.result_data = None

        self.setWindowTitle("Unsupervised Facies Classification")
        self.resize(540, 680)
        self._build_ui()
        self._populate_columns()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Cluster well-log responses into facies groups without a training "
            "target and write the facies codes back to the active well."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        feature_group = QGroupBox("Feature Logs")
        feature_layout = QVBoxLayout(feature_group)
        feature_layout.addWidget(QLabel("Select the logs used to build clustering features."))

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

        setup_group = QGroupBox("Clustering Setup")
        setup_form = QFormLayout(setup_group)
        self.output_edit = QLineEdit("FACIES_UNSUP")
        self.method_combo = QComboBox()
        self.method_combo.addItems(UnsupervisedFaciesClassifier.MODEL_NAMES)
        self.standardize_cb = QCheckBox("Standardize feature logs before clustering")
        self.standardize_cb.setChecked(True)
        self.random_state_spin = QSpinBox()
        self.random_state_spin.setRange(0, 99999)
        self.random_state_spin.setValue(42)
        setup_form.addRow("Output facies column:", self.output_edit)
        setup_form.addRow("Method:", self.method_combo)
        setup_form.addRow("Random state:", self.random_state_spin)
        setup_form.addRow("", self.standardize_cb)
        layout.addWidget(setup_group)

        params_group = QGroupBox("Method Options")
        params_layout = QVBoxLayout(params_group)
        self.params_stack = QStackedWidget()
        params_layout.addWidget(self.params_stack)
        layout.addWidget(params_group)

        self.params_stack.addWidget(self._build_kmeans_page())
        self.params_stack.addWidget(self._build_gmm_page())
        self.params_stack.addWidget(self._build_dbscan_page())
        self.params_stack.addWidget(self._build_agglomerative_page())

        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.run_button = self.buttons.addButton(
            "Run Classification",
            QDialogButtonBox.AcceptRole,
        )
        layout.addWidget(self.buttons)

        self.select_all_btn.clicked.connect(self._select_all_features)
        self.clear_btn.clicked.connect(self.feature_list.clearSelection)
        self.method_combo.currentIndexChanged.connect(self.params_stack.setCurrentIndex)
        self.buttons.accepted.connect(self._run_classification)
        self.buttons.rejected.connect(self.reject)

    def _build_kmeans_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.kmeans_clusters = QSpinBox()
        self.kmeans_clusters.setRange(2, 50)
        self.kmeans_clusters.setValue(5)
        self.kmeans_init = QComboBox()
        self.kmeans_init.addItems(["k-means++", "random"])
        self.kmeans_n_init = QSpinBox()
        self.kmeans_n_init.setRange(1, 100)
        self.kmeans_n_init.setValue(10)
        form.addRow("Clusters:", self.kmeans_clusters)
        form.addRow("Initialization:", self.kmeans_init)
        form.addRow("Restarts:", self.kmeans_n_init)
        return page

    def _build_gmm_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.gmm_components = QSpinBox()
        self.gmm_components.setRange(2, 50)
        self.gmm_components.setValue(5)
        self.gmm_covariance = QComboBox()
        self.gmm_covariance.addItems(["full", "diag", "tied", "spherical"])
        form.addRow("Components:", self.gmm_components)
        form.addRow("Covariance:", self.gmm_covariance)
        return page

    def _build_dbscan_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.dbscan_eps = QDoubleSpinBox()
        self.dbscan_eps.setRange(0.05, 20.0)
        self.dbscan_eps.setDecimals(2)
        self.dbscan_eps.setSingleStep(0.05)
        self.dbscan_eps.setValue(0.50)
        self.dbscan_min_samples = QSpinBox()
        self.dbscan_min_samples.setRange(2, 100)
        self.dbscan_min_samples.setValue(5)
        form.addRow("Neighborhood radius:", self.dbscan_eps)
        form.addRow("Min samples:", self.dbscan_min_samples)
        return page

    def _build_agglomerative_page(self):
        page = QWidget()
        form = QFormLayout(page)
        self.agg_clusters = QSpinBox()
        self.agg_clusters.setRange(2, 50)
        self.agg_clusters.setValue(5)
        self.agg_linkage = QComboBox()
        self.agg_linkage.addItems(["ward", "complete", "average", "single"])
        form.addRow("Clusters:", self.agg_clusters)
        form.addRow("Linkage:", self.agg_linkage)
        return page

    def _populate_columns(self):
        columns = [column for column in self.well.curve_names if column != self.well.depth_col]
        self.feature_list.clear()
        for column in columns:
            self.feature_list.addItem(QListWidgetItem(column))

        for index in range(min(4, self.feature_list.count())):
            self.feature_list.item(index).setSelected(True)

    def _select_all_features(self):
        for index in range(self.feature_list.count()):
            self.feature_list.item(index).setSelected(True)

    def _selected_features(self) -> List[str]:
        return [item.text() for item in self.feature_list.selectedItems()]

    def _build_config(self) -> UnsupervisedFaciesConfig:
        features = self._selected_features()
        if not features:
            raise ValueError("Select at least one feature log for clustering.")

        return UnsupervisedFaciesConfig(
            feature_columns=features,
            output_column=self.output_edit.text().strip() or "FACIES_UNSUP",
            model_name=self.method_combo.currentText(),
            standardize=self.standardize_cb.isChecked(),
            random_state=self.random_state_spin.value(),
            model_params=self._current_model_params(),
        )

    def _current_model_params(self) -> Dict[str, object]:
        method_name = self.method_combo.currentText()

        if method_name == "K-Means":
            return {
                "n_clusters": self.kmeans_clusters.value(),
                "init": self.kmeans_init.currentText(),
                "n_init": self.kmeans_n_init.value(),
            }

        if method_name == "Gaussian Mixture":
            return {
                "n_components": self.gmm_components.value(),
                "covariance_type": self.gmm_covariance.currentText(),
            }

        if method_name == "DBSCAN":
            return {
                "eps": self.dbscan_eps.value(),
                "min_samples": self.dbscan_min_samples.value(),
            }

        return {
            "n_clusters": self.agg_clusters.value(),
            "linkage": self.agg_linkage.currentText(),
        }

    def _run_classification(self):
        try:
            config = self._build_config()
            self.result_data = UnsupervisedFaciesClassifier(config).run(self.well.df)
        except Exception as exc:
            QMessageBox.critical(self, "Unsupervised Classification", str(exc))
            return

        self.accept()

    def get_result(self):
        return self.result_data
