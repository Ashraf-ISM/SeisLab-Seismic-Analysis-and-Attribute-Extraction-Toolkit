"""
Seismic trace and header summary helpers for loaded SEG-Y or NetCDF data.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import segyio

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency at runtime
    pd = None

if TYPE_CHECKING:
    if __package__:
        from .segy_loader import SegyLoader
    else:
        from segy_loader import SegyLoader


def _friendly_dim_name(header_field, axis):
    if axis == 0:
        mapping = {
            "TRACE_SEQUENCE_FILE": "FieldRecord",
            "FieldRecord": "FieldRecord",
            "INLINE_3D": "Inline",
            "CDP": "CDP",
        }
    else:
        mapping = {
            "TRACE_SEQUENCE_LINE": "ReceiverID",
            "TraceNumber": "ReceiverID",
            "CROSSLINE_3D": "Crossline",
            "CDP_TRACE": "CDP_TRACE",
        }
    return mapping.get(header_field, header_field)


def build_load_report(loader):
    data = getattr(loader, "data", None)
    if data is None:
        return "No data loaded."

    geometry_info = dict(getattr(loader, "geometry_info", {}) or {})
    header_info = dict(getattr(loader, "header_info", {}) or {})
    source_format = str(getattr(loader, "source_format", "SEGY"))

    if source_format == "SYNTHETIC":
        lines = ["Synthetic fallback activated."]
        reason = str(getattr(loader, "synthetic_reason", "") or "")
        if reason:
            lines.append(reason)
        lines.append(f"Data shape: {tuple(int(v) for v in data.shape)}")
        lines.append(f"Sample rate: {float(getattr(loader, 'sample_rate', 0.0)):.3f} ms")
        return "\n".join(lines)

    lines = ["detect_geometry()"]

    pair = geometry_info.get("selected_pair", ("Inline", "Crossline"))
    pair_a, pair_b = pair[0], pair[1]

    lines.append(f"|- source: {geometry_info.get('source', 'unknown')}")
    lines.append(f"|- selected headers: {pair_a} x {pair_b}")
    lines.append(
        f"|- dimensions: {geometry_info.get('n_inlines', data.shape[0])} x "
        f"{geometry_info.get('n_crosslines', data.shape[1])}"
    )
    lines.append(
        f"|- traces: {geometry_info.get('trace_count', int(np.prod(data.shape[:2])))} "
        f"(fill ratio {geometry_info.get('fill_ratio', 1.0):.3f})"
    )

    lines.append("")
    lines.append("load_segy_headers()")

    text_header = header_info.get("text_header") or ""
    if text_header:
        lines.append(text_header)

    if source_format == "NETCDF":
        dims = header_info.get("dimensions", [])
        vars_list = header_info.get("variables", [])
        groups = header_info.get("groups", [])
        if geometry_info.get("source") == "netcdf_headers":
            dim_a = _friendly_dim_name(pair_a, axis=0)
            dim_b = _friendly_dim_name(pair_b, axis=1)
            dims_text = (
                f"{dim_a}({data.shape[0]}), "
                f"{dim_b}({data.shape[1]}), "
                f"Time({data.shape[2]})"
            )
        else:
            dims_text = ", ".join(f"{name}({size})" for name, size in dims) if dims else "-"
        vars_text = ", ".join(vars_list) if vars_list else "-"
        groups_text = ", ".join(groups) if groups else "-"
    else:
        dim_a = _friendly_dim_name(pair_a, axis=0)
        dim_b = _friendly_dim_name(pair_b, axis=1)
        dims_text = f"{dim_a}({data.shape[0]}), {dim_b}({data.shape[1]}), Time({data.shape[2]})"

        trace_fields = header_info.get("trace_header_fields", [])
        variables = [f"float32 Samples({dim_a}, {dim_b}, Time)", "float32 Time(Time)"]
        variables.extend(f"int32 {field}({dim_a}, {dim_b})" for field in trace_fields)
        vars_text = ", ".join(variables)
        groups_text = "-"

    lines.append(f"dimensions(sizes): {dims_text}")
    lines.append(f"variables(dimensions): {vars_text}")
    lines.append(f"groups: {groups_text}")

    binary_header = header_info.get("binary_header")
    if isinstance(binary_header, dict) and binary_header:
        bin_text = ", ".join(f"{k}: {v}" for k, v in binary_header.items())
        lines.append(f"bin: {{{bin_text}}}")
    elif binary_header:
        lines.append(f"bin: {binary_header}")

    lines.append(f"Data shape: {tuple(int(v) for v in data.shape)}")
    return "\n".join(lines)


def build_loader_info(loader):
    data = getattr(loader, "data", None)
    geometry_info = dict(getattr(loader, "geometry_info", {}) or {})
    return {
        "filepath": str(getattr(loader, "filepath", "")),
        "mode": str(getattr(loader, "mode", "unknown")),
        "is_2d": bool(getattr(loader, "is_2d", False)),
        "format": str(getattr(loader, "source_format", "unknown")),
        "n_inlines": int(data.shape[0]) if data is not None else 0,
        "n_crosslines": int(data.shape[1]) if data is not None else 0,
        "n_samples": int(data.shape[2]) if data is not None else 0,
        "sample_rate": float(getattr(loader, "sample_rate", 0.0)),
        "data_min": float(np.min(data)) if data is not None else 0.0,
        "data_max": float(np.max(data)) if data is not None else 0.0,
        "load_report": build_load_report(loader),
        "geometry_info": geometry_info,
    }


def get_trace_header_dataframe(loader):
    if pd is None:
        raise ImportError("pandas is required to export trace headers as a table.")

    if str(getattr(loader, "source_format", "")).upper() != "SEGY":
        return pd.DataFrame()

    header_info = dict(getattr(loader, "header_info", {}) or {})
    trace_fields = header_info.get("trace_header_fields", [])
    records = {}

    with segyio.open(loader.filepath, ignore_geometry=True) as segy_file:
        for field_name in trace_fields:
            key = getattr(segyio.TraceField, field_name, None)
            if key is None:
                continue
            try:
                records[field_name] = np.asarray(segy_file.attributes(key)[:])
            except Exception:
                continue

    return pd.DataFrame(records)


def export_trace_headers(loader, filepath):
    trace_headers = get_trace_header_dataframe(loader)
    out_path = Path(filepath)
    if out_path.suffix.lower() in {".parquet", ".pq"}:
        trace_headers.to_parquet(out_path, index=False)
        return
    trace_headers.to_csv(out_path, index=False)


@dataclass
class SeismicTraceHeaderInfo:
    filepath: str
    source_format: str
    mode: str
    is_2d: bool
    n_inlines: int
    n_crosslines: int
    n_samples: int
    sample_rate: float
    selected_headers: tuple
    geometry_info: dict
    header_info: dict
    load_report: str

    @classmethod
    def from_loader(cls, loader: "SegyLoader"):
        info = build_loader_info(loader)
        geometry_info = dict(info.get("geometry_info", {}) or {})
        header_info = dict(getattr(loader, "header_info", {}) or {})

        return cls(
            filepath=str(info.get("filepath", "")),
            source_format=str(info.get("format", getattr(loader, "source_format", "unknown"))),
            mode=str(info.get("mode", getattr(loader, "mode", "unknown"))),
            is_2d=bool(info.get("is_2d", getattr(loader, "is_2d", False))),
            n_inlines=int(info.get("n_inlines", 0)),
            n_crosslines=int(info.get("n_crosslines", 0)),
            n_samples=int(info.get("n_samples", 0)),
            sample_rate=float(info.get("sample_rate", 0.0)),
            selected_headers=tuple(geometry_info.get("selected_pair", ())),
            geometry_info=geometry_info,
            header_info=header_info,
            load_report=str(info.get("load_report", "")),
        )

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_text(self):
        lines = [
            f"File: {self.filepath}",
            f"Format: {self.source_format}",
            f"Mode: {self.mode}",
            f"2D: {self.is_2d}",
            f"Cube: {self.n_inlines} x {self.n_crosslines} x {self.n_samples}",
            f"Sample rate: {self.sample_rate}",
        ]

        if self.selected_headers:
            lines.append(f"Selected trace headers: {self.selected_headers}")

        text_header = (self.header_info.get("text_header") or "").strip()
        if text_header:
            lines.append("")
            lines.append("Text header:")
            lines.append(text_header)

        binary_header = self.header_info.get("binary_header")
        if binary_header:
            lines.append("")
            lines.append(f"Binary header: {binary_header}")

        trace_fields = self.header_info.get("trace_header_fields")
        if trace_fields:
            lines.append("")
            lines.append("Trace header fields:")
            lines.append(", ".join(str(field) for field in trace_fields))

        if self.load_report:
            lines.append("")
            lines.append("Load report:")
            lines.append(self.load_report)

        return "\n".join(lines)


def build_seismic_info(loader):
    return SeismicTraceHeaderInfo.from_loader(loader)


def format_seismic_info(loader):
    return build_seismic_info(loader).to_text()


def build_argument_parser():
    parser = argparse.ArgumentParser(description="Print trace and header information for a seismic file.")
    parser.add_argument("filepath", help="Path to the SEG-Y or NetCDF file")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of plain text")
    return parser


def main(argv=None):
    args = build_argument_parser().parse_args(argv)
    if __package__:
        from .segy_loader import SegyLoader
    else:
        from segy_loader import SegyLoader

    loader = SegyLoader(args.filepath)
    loader.load_data()

    info = SeismicTraceHeaderInfo.from_loader(loader)
    output = info.to_json() if args.json else info.to_text()
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
