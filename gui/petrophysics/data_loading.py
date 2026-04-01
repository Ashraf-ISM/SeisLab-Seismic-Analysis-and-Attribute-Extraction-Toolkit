import os
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .models import WellDataset

try:
    import lasio

    HAS_LASIO = True
except ImportError:
    HAS_LASIO = False


NULL_VALUES = (-999.25, -999.0, -9999.0, -99999.0)


def detect_format(path: str) -> Optional[str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".las":
        return "las"
    if ext in (".csv", ".txt"):
        return "csv"
    if ext in (".xlsx", ".xls"):
        return "excel"
    return None


def _guess_depth_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if col.upper() in ("DEPT", "DEPTH", "MD", "TVD", "TVDSS"):
            return col
    return df.columns[0]


def _sanitize_dataframe(df: pd.DataFrame, replace_nulls: bool = True) -> pd.DataFrame:
    out = df.copy()
    if replace_nulls:
        out.replace(list(NULL_VALUES), np.nan, inplace=True)
    return out


def load_las(path: str, replace_nulls: bool = True) -> WellDataset:
    if not HAS_LASIO:
        raise ImportError("lasio is not installed. Install with: pip install lasio")

    las = lasio.read(path)
    name = str(getattr(las.well.WELL, "value", "") or os.path.basename(path))
    df = las.df().reset_index()
    df = _sanitize_dataframe(df, replace_nulls=replace_nulls)
    depth_col = df.columns[0]

    header = {}
    for item in las.well:
        header[item.mnemonic] = {
            "value": str(item.value),
            "unit": str(item.unit),
            "desc": str(item.descr),
        }

    curves = {}
    for curve in las.curves:
        curves[curve.mnemonic] = {
            "unit": str(curve.unit),
            "desc": str(curve.descr),
        }

    return WellDataset(
        name=name,
        filename=path,
        df=df,
        depth_col=depth_col,
        curves=curves,
        header=header,
    )


def load_csv(path: str, replace_nulls: bool = True) -> WellDataset:
    df = pd.read_csv(path)
    df = _sanitize_dataframe(df, replace_nulls=replace_nulls)
    depth_col = _guess_depth_column(df)
    return WellDataset(
        name=os.path.basename(path),
        filename=path,
        df=df,
        depth_col=depth_col,
    )


def load_excel(path: str, replace_nulls: bool = True) -> WellDataset:
    df = pd.read_excel(path)
    df = _sanitize_dataframe(df, replace_nulls=replace_nulls)
    depth_col = _guess_depth_column(df)
    return WellDataset(
        name=os.path.basename(path),
        filename=path,
        df=df,
        depth_col=depth_col,
    )


def load_well(path: str, fmt: Optional[str] = None, replace_nulls: bool = True) -> WellDataset:
    selected = fmt or detect_format(path)
    if selected == "las":
        return load_las(path, replace_nulls=replace_nulls)
    if selected == "csv":
        return load_csv(path, replace_nulls=replace_nulls)
    if selected == "excel":
        return load_excel(path, replace_nulls=replace_nulls)
    raise ValueError(f"Unsupported file format for: {os.path.basename(path)}")


def unique_well_name(name: str, existing_names: Dict[str, WellDataset]) -> str:
    base = (name or "").strip() or "Untitled Well"
    if base not in existing_names:
        return base
    suffix = 2
    while f"{base} ({suffix})" in existing_names:
        suffix += 1
    return f"{base} ({suffix})"
