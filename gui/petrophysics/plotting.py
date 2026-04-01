from typing import Optional

import numpy as np
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(8, 6), tight_layout=True)
        self.figure = fig
        super().__init__(fig)
        if parent is not None:
            self.setParent(parent)


def _col_as_series(df, col_name: str) -> pd.Series:
    """Return a single Series even if DataFrame has duplicate column names."""
    data = df[col_name]
    if isinstance(data, pd.DataFrame):
        return data.iloc[:, 0]
    return data


def plot_log_view(
    canvas: MatplotlibCanvas,
    df,
    depth_col: str,
    curve_a: Optional[str],
    curve_b: Optional[str],
    depth_from: Optional[float] = None,
    depth_to: Optional[float] = None,
):
    canvas.figure.clear()
    ax = canvas.figure.add_subplot(111)

    if depth_col not in df:
        ax.text(0.5, 0.5, "Depth column missing", ha="center", va="center")
        canvas.draw_idle()
        return

    view = df.copy()
    if depth_from is not None and depth_to is not None and depth_to > depth_from:
        view = view[(view[depth_col] >= depth_from) & (view[depth_col] <= depth_to)]

    if view.empty:
        ax.text(0.5, 0.5, "No samples in selected depth window", ha="center", va="center")
        canvas.draw_idle()
        return

    depth = view[depth_col]
    if curve_a and curve_a in view:
        ax.plot(view[curve_a], depth, label=curve_a, color="#f0a834", linewidth=1.2)
    if curve_b and curve_b in view:
        ax.plot(view[curve_b], depth, label=curve_b, color="#2ab7ca", linewidth=1.2)

    ax.set_ylabel(depth_col)
    ax.set_xlabel("Curve value")
    ax.invert_yaxis()
    ax.grid(alpha=0.3)
    ax.legend(loc="best")
    canvas.draw_idle()


def plot_crossplot(
    canvas: MatplotlibCanvas,
    df,
    x_curve: str,
    y_curve: str,
    color_curve: Optional[str] = None,
    x_log: bool = False,
    y_log: bool = False,
):
    canvas.figure.clear()
    ax = canvas.figure.add_subplot(111)

    if x_curve not in df or y_curve not in df:
        ax.text(0.5, 0.5, "Select valid X/Y curves", ha="center", va="center")
        canvas.draw_idle()
        return 0, np.nan, np.nan

    x_series = _col_as_series(df, x_curve)
    y_series = _col_as_series(df, y_curve)

    subset = pd.DataFrame({"x": x_series, "y": y_series})
    has_color = bool(color_curve and color_curve in df.columns)
    if has_color:
        subset["c"] = _col_as_series(df, color_curve)
    subset = subset.dropna()

    if subset.empty:
        ax.text(0.5, 0.5, "No valid points for crossplot", ha="center", va="center")
        canvas.draw_idle()
        return 0, np.nan, np.nan

    if has_color:
        c_numeric = pd.to_numeric(subset["c"], errors="coerce")
        if c_numeric.notna().any():
            valid = subset[c_numeric.notna()]
            sc = ax.scatter(valid["x"], valid["y"], c=c_numeric[c_numeric.notna()], cmap="viridis", s=10, alpha=0.8)
            canvas.figure.colorbar(sc, ax=ax, label=color_curve)
        else:
            ax.scatter(subset["x"], subset["y"], s=10, alpha=0.8, color="#2ab7ca")
    else:
        ax.scatter(subset["x"], subset["y"], s=10, alpha=0.8, color="#2ab7ca")

    x = subset["x"].values
    y = subset["y"].values
    if len(x) > 2:
        slope, intercept = np.polyfit(x, y, 1)
        y_fit = slope * x + intercept
        ss_res = np.sum((y - y_fit) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else np.nan
        ax.plot(np.sort(x), np.sort(y_fit), color="#f0a834", linewidth=1.0)
    else:
        slope, intercept, r2 = np.nan, np.nan, np.nan

    ax.set_xlabel(x_curve)
    ax.set_ylabel(y_curve)
    if x_log:
        ax.set_xscale("log")
    if y_log:
        ax.set_yscale("log")
    ax.grid(alpha=0.3)
    canvas.draw_idle()

    return len(subset), float(r2) if np.isfinite(r2) else np.nan, float(slope) if np.isfinite(slope) else np.nan


def plot_histogram(canvas: MatplotlibCanvas, df, curve: str, bins: int = 40):
    canvas.figure.clear()
    ax = canvas.figure.add_subplot(111)

    if curve not in df:
        ax.text(0.5, 0.5, "Select a valid curve", ha="center", va="center")
        canvas.draw_idle()
        return

    data = pd.to_numeric(_col_as_series(df, curve), errors="coerce").dropna()
    if data.empty:
        ax.text(0.5, 0.5, "No numeric values for histogram", ha="center", va="center")
        canvas.draw_idle()
        return

    ax.hist(data.values, bins=bins, color="#2ab7ca", alpha=0.85, edgecolor="#0e1117")
    ax.set_title(f"Histogram: {curve}")
    ax.set_xlabel(curve)
    ax.set_ylabel("Count")
    ax.grid(alpha=0.3)
    canvas.draw_idle()


def plot_triple_combo(
    canvas: MatplotlibCanvas,
    df,
    depth_col: str,
    track1_curves,
    track2_curve: str,
    track3_curves,
):
    canvas.figure.clear()

    if depth_col not in df:
        ax = canvas.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Depth column missing", ha="center", va="center")
        canvas.draw_idle()
        return

    depth = pd.to_numeric(_col_as_series(df, depth_col), errors="coerce")
    axes = canvas.figure.subplots(1, 3, sharey=True)
    track_colors = ["#f0a834", "#43b6c9", "#7ac943", "#ef6c6c"]

    for i, curve in enumerate(track1_curves):
        if curve in df:
            x = pd.to_numeric(_col_as_series(df, curve), errors="coerce")
            axes[0].plot(x, depth, color=track_colors[i % len(track_colors)], linewidth=1.0, label=curve)
    axes[0].set_title("Track 1: GR/CAL")
    axes[0].legend(loc="best", fontsize=7)
    axes[0].grid(alpha=0.25)

    if track2_curve in df:
        x2 = pd.to_numeric(_col_as_series(df, track2_curve), errors="coerce")
        axes[1].plot(x2, depth, color="#f05a5a", linewidth=1.0, label=track2_curve)
        axes[1].set_xscale("log")
    axes[1].set_title("Track 2: Resistivity")
    axes[1].legend(loc="best", fontsize=7)
    axes[1].grid(alpha=0.25)

    for i, curve in enumerate(track3_curves):
        if curve in df:
            x3 = pd.to_numeric(_col_as_series(df, curve), errors="coerce")
            axes[2].plot(x3, depth, color=track_colors[(i + 1) % len(track_colors)], linewidth=1.0, label=curve)
    axes[2].set_title("Track 3: Density/Porosity")
    axes[2].legend(loc="best", fontsize=7)
    axes[2].grid(alpha=0.25)

    axes[0].set_ylabel(depth_col)
    axes[0].invert_yaxis()
    canvas.figure.tight_layout()
    canvas.draw_idle()


def plot_multi_track(canvas: MatplotlibCanvas, df, depth_col: str, curves):
    canvas.figure.clear()

    if depth_col not in df:
        ax = canvas.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Depth column missing", ha="center", va="center")
        canvas.draw_idle()
        return

    valid = [curve for curve in curves if curve in df]
    if not valid:
        ax = canvas.figure.add_subplot(111)
        ax.text(0.5, 0.5, "No valid curves selected", ha="center", va="center")
        canvas.draw_idle()
        return

    depth = pd.to_numeric(_col_as_series(df, depth_col), errors="coerce")
    axes = canvas.figure.subplots(1, len(valid), sharey=True)
    if len(valid) == 1:
        axes = [axes]

    palette = ["#f0a834", "#2ab7ca", "#7ac943", "#ef6c6c", "#9966ff", "#00a8a8"]
    for i, curve in enumerate(valid):
        x = pd.to_numeric(_col_as_series(df, curve), errors="coerce")
        axes[i].plot(x, depth, color=palette[i % len(palette)], linewidth=1.0)
        axes[i].set_title(curve, fontsize=8)
        axes[i].grid(alpha=0.25)

    axes[0].set_ylabel(depth_col)
    axes[0].invert_yaxis()
    canvas.figure.tight_layout()
    canvas.draw_idle()
