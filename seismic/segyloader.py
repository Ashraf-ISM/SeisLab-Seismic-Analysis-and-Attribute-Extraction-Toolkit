"""
Backward-compatible imports for legacy `segyloader` module paths.
"""

from __future__ import annotations

if __package__:
    from .segy_loader import SegyLoader
    from .seismic_info import (
        SeismicTraceHeaderInfo,
        build_load_report,
        build_loader_info,
        build_seismic_info,
        export_trace_headers,
        format_seismic_info,
        get_trace_header_dataframe,
    )
    try:
        from . import seismic_visualization as _seismic_visualization
    except Exception:
        _seismic_visualization = None
else:
    from segy_loader import SegyLoader
    from seismic_info import (
        SeismicTraceHeaderInfo,
        build_load_report,
        build_loader_info,
        build_seismic_info,
        export_trace_headers,
        format_seismic_info,
        get_trace_header_dataframe,
    )
    try:
        import seismic_visualization as _seismic_visualization
    except Exception:
        _seismic_visualization = None

SeisLab3DViewer = getattr(_seismic_visualization, "SeisLab3DViewer", None)
build_argument_parser = getattr(_seismic_visualization, "build_argument_parser", None)
load_and_show = getattr(_seismic_visualization, "load_and_show", None)
main = getattr(_seismic_visualization, "main", None)

__all__ = [
    "SegyLoader",
    "SeismicTraceHeaderInfo",
    "build_load_report",
    "build_loader_info",
    "build_seismic_info",
    "export_trace_headers",
    "format_seismic_info",
    "get_trace_header_dataframe",
]

if SeisLab3DViewer is not None:
    __all__.append("SeisLab3DViewer")
if build_argument_parser is not None:
    __all__.append("build_argument_parser")
if load_and_show is not None:
    __all__.append("load_and_show")
if main is not None:
    __all__.append("main")
