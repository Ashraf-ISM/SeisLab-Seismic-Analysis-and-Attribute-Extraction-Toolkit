import os
import re
from pathlib import Path

import numpy as np
import segyio

try:
    from netCDF4 import Dataset
except ImportError:  # pragma: no cover - optional dependency at runtime
    Dataset = None


class SegyLoader:

    def __init__(self, filepath):
        self.filepath = filepath
        self.path = Path(filepath)
        self.data = None

        self.inlines = None
        self.crosslines = None

        self.n_samples = 0
        self.sample_rate = 1.0

        self.is_2d = False
        self.mode = "unknown"
        self.source_format = "SEGY"

        self.geometry_info = {}
        self.header_info = {}
        self.text_header = ""
        self.binary_header = {}
        self.synthetic_reason = ""
        self.load_report = "No data loaded."

    # ---------------------------------------------------
    # MAIN LOAD
    # ---------------------------------------------------

    def load_data(self):
        if not self.path.exists():
            self._load_synthetic(f"File not found: {self.filepath}")
            return

        ext = os.path.splitext(self.filepath)[1].lower()
        if ext in {".nc", ".nc4", ".cdf", ".netcdf"}:
            self._load_netcdf()
        else:
            self._load_segy()

    def _load_segy(self):
        self.synthetic_reason = ""
        with segyio.open(self.filepath, ignore_geometry=True) as segy_file:
            self.n_samples = len(segy_file.samples)

            try:
                self.sample_rate = segyio.tools.dt(segy_file) / 1000.0
            except Exception:
                self.sample_rate = 1.0

            traces = np.asarray(segy_file.trace.raw[:], dtype=np.float32)
            self.geometry_info = self.detect_geometry(segy_file)

            il = self.geometry_info.get("inline_values")
            xl = self.geometry_info.get("crossline_values")

            self._build_cube(traces, il, xl)
            self.header_info = self.load_segy_headers(segy_file)
            self.text_header = self.header_info.get("text_header", "")
            self.binary_header = self.header_info.get("binary_header", {})

        self.source_format = "SEGY"
        if __package__:
            from .seismic_info import build_load_report
        else:
            from seismic_info import build_load_report
        self.load_report = build_load_report(self)

    def _load_netcdf(self):
        if Dataset is None:
            raise ImportError("netCDF4 is required to load .nc/.nc4/.cdf files.")

        self.synthetic_reason = ""
        with Dataset(self.filepath, "r") as ds:
            data_var_name = self._pick_netcdf_data_variable(ds)
            if not data_var_name:
                raise ValueError("No suitable seismic data variable found in NetCDF file.")

            data_var = ds.variables[data_var_name]
            raw_data = np.asarray(data_var[:], dtype=np.float32)

            if raw_data.ndim < 2:
                raise ValueError(f"Variable '{data_var_name}' has unsupported shape: {raw_data.shape}")

            self.data = None
            self.geometry_info = {}

            if raw_data.ndim == 2:
                self.data = raw_data[:, np.newaxis, :]
            elif raw_data.ndim == 3:
                netcdf_geometry = self._detect_netcdf_trace_geometry(ds, raw_data)
                if netcdf_geometry is not None:
                    self.n_samples = int(raw_data.shape[-1])
                    traces = raw_data.reshape((-1, self.n_samples))
                    self._build_cube(
                        traces,
                        netcdf_geometry["inline_values"],
                        netcdf_geometry["crossline_values"],
                    )
                    self.geometry_info = netcdf_geometry
                else:
                    self.data = raw_data
            else:
                # Flatten extra leading dimensions to keep viewer contract (IL, XL, T)
                a, b = raw_data.shape[-2], raw_data.shape[-1]
                self.data = raw_data.reshape((-1, a, b))

            if self.data is None:
                raise ValueError("Failed to build seismic cube from NetCDF data.")

            self.n_samples = int(self.data.shape[2])
            self.sample_rate = self._extract_netcdf_sample_rate(ds)

            dim_names = list(getattr(data_var, "dimensions", ()))
            il_dim = dim_names[0] if len(dim_names) > 0 else "Inline"
            xl_dim = dim_names[1] if len(dim_names) > 1 else "Crossline"

            if self.inlines is None:
                self.inlines = self._read_coord_or_index(ds, il_dim, self.data.shape[0])
            if self.crosslines is None:
                self.crosslines = self._read_coord_or_index(ds, xl_dim, self.data.shape[1])

            self.mode = "2d" if self.data.shape[0] <= 1 or self.data.shape[1] <= 1 else "3d"
            self.is_2d = self.mode == "2d"

            if not self.geometry_info:
                self.geometry_info = {
                    "selected_pair": (il_dim, xl_dim),
                    "n_inlines": int(self.data.shape[0]),
                    "n_crosslines": int(self.data.shape[1]),
                    "trace_count": int(np.prod(self.data.shape[:2])),
                    "fill_ratio": 1.0,
                    "source": "netcdf",
                }
            self.header_info = self._load_netcdf_headers(ds, data_var_name)
            self.text_header = self.header_info.get("text_header", "")
            self.binary_header = self.header_info.get("binary_header", {})

        self.source_format = "NETCDF"
        if __package__:
            from .seismic_info import build_load_report
        else:
            from seismic_info import build_load_report
        self.load_report = build_load_report(self)

    # ---------------------------------------------------
    # GEOMETRY / HEADERS
    # ---------------------------------------------------

    def detect_geometry(self, segy_file):
        trace_count = int(segy_file.tracecount)
        cache = {}

        def get_values(field_name):
            if field_name in cache:
                return cache[field_name]

            key = getattr(segyio.TraceField, field_name, None)
            if key is None:
                cache[field_name] = None
                return None

            try:
                cache[field_name] = np.asarray(segy_file.attributes(key)[:], dtype=np.int64)
            except Exception:
                cache[field_name] = None
            return cache[field_name]

        def unique_count(values):
            if values is None or values.size == 0:
                return 0
            return int(np.unique(values).size)

        candidate_pairs = [
            ("INLINE_3D", "CROSSLINE_3D"),
            ("TRACE_SEQUENCE_FILE", "TRACE_SEQUENCE_LINE"),
            ("TRACE_SEQUENCE_FILE", "TraceNumber"),
            ("FieldRecord", "TraceNumber"),
            ("CDP", "TraceNumber"),
            ("ShotPoint", "TraceNumber"),
            ("EnergySourcePoint", "TraceNumber"),
        ]

        tested = []
        best = None
        best_score = -1.0

        for inline_field, crossline_field in candidate_pairs:
            il_values = get_values(inline_field)
            xl_values = get_values(crossline_field)
            n_il = unique_count(il_values)
            n_xl = unique_count(xl_values)

            if n_il <= 1 or n_xl <= 1:
                tested.append((inline_field, crossline_field, n_il, n_xl, 0.0))
                continue

            grid = n_il * n_xl
            if grid < trace_count:
                tested.append((inline_field, crossline_field, n_il, n_xl, 0.0))
                continue

            fill_ratio = trace_count / float(grid)
            tested.append((inline_field, crossline_field, n_il, n_xl, fill_ratio))

            if fill_ratio > best_score:
                best_score = fill_ratio
                best = (inline_field, crossline_field, il_values, xl_values, n_il, n_xl)

        if best is None:
            il_values = np.zeros(trace_count, dtype=np.int64)
            xl_values = np.arange(trace_count, dtype=np.int64)
            return {
                "selected_pair": ("SyntheticInline", "TraceIndex"),
                "inline_values": il_values,
                "crossline_values": xl_values,
                "n_inlines": 1,
                "n_crosslines": trace_count,
                "trace_count": trace_count,
                "fill_ratio": 1.0,
                "tested_pairs": tested,
                "source": "fallback_2d",
            }

        inline_field, crossline_field, il_values, xl_values, n_il, n_xl = best
        grid = max(1, n_il * n_xl)
        return {
            "selected_pair": (inline_field, crossline_field),
            "inline_values": il_values,
            "crossline_values": xl_values,
            "n_inlines": n_il,
            "n_crosslines": n_xl,
            "trace_count": trace_count,
            "fill_ratio": trace_count / float(grid),
            "tested_pairs": tested,
            "source": "segy_headers",
        }

    def load_segy_headers(self, segy_file):
        text_header = ""
        try:
            text_header = segyio.tools.wrap(segy_file.text[0]).rstrip()
        except Exception:
            text_header = ""

        binary_header = {}
        for name, key in segyio.binfield.keys.items():
            try:
                value = int(segy_file.bin[key])
                if value != 0:
                    binary_header[name] = value
            except Exception:
                continue

        if not binary_header:
            for name, key in list(segyio.binfield.keys.items())[:10]:
                try:
                    binary_header[name] = int(segy_file.bin[key])
                except Exception:
                    continue

        trace_fields = list(segyio.tracefield.keys.keys())
        return {
            "text_header": text_header,
            "binary_header": binary_header,
            "trace_header_fields": trace_fields,
        }

    def _load_netcdf_headers(self, dataset, data_var_name):
        text_header = ""
        if "text" in dataset.ncattrs():
            text_header = str(dataset.getncattr("text"))

        bin_header = None
        if "bin" in dataset.ncattrs():
            bin_header = str(dataset.getncattr("bin"))

        dimensions = [(name, len(dim)) for name, dim in dataset.dimensions.items()]
        variables = []
        for name, var in dataset.variables.items():
            dtype_name = np.dtype(var.dtype).name
            dims = ", ".join(var.dimensions)
            variables.append(f"{dtype_name} {name}({dims})")

        return {
            "text_header": text_header.strip(),
            "binary_header": bin_header,
            "dimensions": dimensions,
            "variables": variables,
            "groups": list(dataset.groups.keys()),
            "data_variable": data_var_name,
        }

    def _detect_netcdf_trace_geometry(self, dataset, raw_data):
        if raw_data.ndim != 3:
            return None

        # Only attempt reconstruction for trace-like layout (1, ntraces, nsamples)
        if raw_data.shape[0] > 1 and raw_data.shape[1] > 1:
            return None

        trace_count = int(np.prod(raw_data.shape[:-1]))
        if trace_count <= 1:
            return None

        def read_trace_header(name):
            if name not in dataset.variables:
                return None
            try:
                values = np.asarray(dataset.variables[name][:], dtype=np.int64).reshape(-1)
            except Exception:
                return None
            if values.size != trace_count:
                return None
            return values

        candidate_pairs = [
            ("INLINE_3D", "CROSSLINE_3D"),
            ("TRACE_SEQUENCE_FILE", "TRACE_SEQUENCE_LINE"),
            ("TRACE_SEQUENCE_FILE", "TraceNumber"),
            ("FieldRecord", "TraceNumber"),
            ("CDP", "TraceNumber"),
            ("ShotPoint", "TraceNumber"),
            ("EnergySourcePoint", "TraceNumber"),
        ]

        tested = []
        best = None
        best_score = -1.0

        for inline_field, crossline_field in candidate_pairs:
            il_values = read_trace_header(inline_field)
            xl_values = read_trace_header(crossline_field)

            if il_values is None or xl_values is None:
                continue

            n_il = int(np.unique(il_values).size)
            n_xl = int(np.unique(xl_values).size)

            if n_il <= 1 or n_xl <= 1:
                tested.append((inline_field, crossline_field, n_il, n_xl, 0.0))
                continue

            grid = n_il * n_xl
            if grid < trace_count:
                tested.append((inline_field, crossline_field, n_il, n_xl, 0.0))
                continue

            fill_ratio = trace_count / float(grid)
            tested.append((inline_field, crossline_field, n_il, n_xl, fill_ratio))

            if fill_ratio > best_score:
                best_score = fill_ratio
                best = (inline_field, crossline_field, il_values, xl_values, n_il, n_xl)

        if best is None:
            return None

        inline_field, crossline_field, il_values, xl_values, n_il, n_xl = best
        grid = max(1, n_il * n_xl)
        return {
            "selected_pair": (inline_field, crossline_field),
            "inline_values": il_values,
            "crossline_values": xl_values,
            "n_inlines": n_il,
            "n_crosslines": n_xl,
            "trace_count": trace_count,
            "fill_ratio": trace_count / float(grid),
            "tested_pairs": tested,
            "source": "netcdf_headers",
        }

    # ---------------------------------------------------
    # BUILD SEISMIC CUBE
    # ---------------------------------------------------

    def _build_cube(self, traces, il, xl):
        il = np.asarray(il, dtype=np.int64)
        xl = np.asarray(xl, dtype=np.int64)

        unique_il = np.unique(il)
        unique_xl = np.unique(xl)
        n_traces = traces.shape[0]

        if len(unique_il) <= 1 or len(unique_xl) <= 1:
            self.is_2d = True
            self.mode = "2d"
            self.data = traces[:, np.newaxis, :]
            self.inlines = np.arange(traces.shape[0], dtype=np.int64)
            self.crosslines = np.array([0], dtype=np.int64)
            return

        self.mode = "3d"
        self.is_2d = False

        n_il = len(unique_il)
        n_xl = len(unique_xl)
        cube = np.zeros((n_il, n_xl, self.n_samples), dtype=np.float32)

        il_map = {value: idx for idx, value in enumerate(unique_il)}
        xl_map = {value: idx for idx, value in enumerate(unique_xl)}

        for t in range(n_traces):
            i = il_map.get(il[t])
            x = xl_map.get(xl[t])
            if i is None or x is None:
                continue
            cube[i, x, :] = traces[t]

        self.data = cube
        self.inlines = unique_il
        self.crosslines = unique_xl

    # ---------------------------------------------------
    # NETCDF HELPERS
    # ---------------------------------------------------

    def _pick_netcdf_data_variable(self, dataset):
        priorities = ["Samples", "samples", "Data", "data", "seismic", "amplitude"]
        for name in priorities:
            if name in dataset.variables:
                if dataset.variables[name].ndim >= 2:
                    return name

        candidates = []
        for name, variable in dataset.variables.items():
            if variable.ndim < 2:
                continue
            size = int(np.prod(variable.shape))
            candidates.append((size, name))

        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]

    def _extract_netcdf_sample_rate(self, dataset):
        for var_name in ("Time", "time", "TWT", "twt"):
            if var_name not in dataset.variables:
                continue
            try:
                axis = np.asarray(dataset.variables[var_name][:], dtype=np.float64)
                if axis.size >= 2:
                    delta = float(np.mean(np.diff(axis[: min(axis.size, 64)])))
                    if np.isfinite(delta) and delta != 0:
                        delta = abs(delta)
                        # Common SEG-Y export convention: microseconds on time axis.
                        if delta > 50:
                            delta = delta / 1000.0
                        return delta
            except Exception:
                continue

        if "bin" in dataset.ncattrs():
            bin_text = str(dataset.getncattr("bin"))
            match = re.search(r"Interval:\s*([0-9]+(?:\.[0-9]+)?)", bin_text)
            if match:
                return float(match.group(1)) / 1000.0

        return 1.0

    def _read_coord_or_index(self, dataset, dim_name, expected_size):
        if dim_name in dataset.variables:
            var = dataset.variables[dim_name]
            if getattr(var, "ndim", 0) == 1 and len(var) == expected_size:
                try:
                    return np.asarray(var[:], dtype=np.int64)
                except Exception:
                    pass
        return np.arange(expected_size, dtype=np.int64)

    def _load_synthetic(self, reason):
        if __package__:
            from .seismic_info import build_load_report
        else:
            from seismic_info import build_load_report

        rng = np.random.default_rng(42)

        n_inlines = 50
        n_crosslines = 50
        n_samples = 500
        sample_rate_ms = 2.0

        cube = np.zeros((n_inlines, n_crosslines, n_samples), dtype=np.float32)
        time_axis = np.arange(n_samples, dtype=np.float32)

        event_times = (80, 150, 250, 350, 420)
        event_amplitudes = (1.2, 0.8, 1.5, 0.6, 1.0)
        event_frequencies = (20.0, 25.0, 30.0, 22.0, 28.0)

        for il_idx in range(n_inlines):
            for xl_idx in range(n_crosslines):
                dip_x = int(il_idx * 0.3)
                dip_y = int(xl_idx * 0.2)
                amplitude_var = 0.8 + 0.4 * np.sin(il_idx / 10.0) * np.cos(xl_idx / 8.0)

                trace = np.zeros(n_samples, dtype=np.float32)
                for event_time, amplitude, frequency in zip(
                    event_times,
                    event_amplitudes,
                    event_frequencies,
                ):
                    shifted = time_axis - (event_time + dip_x + dip_y)
                    trace += amplitude_var * amplitude * self._ricker_wavelet(shifted, frequency, sample_rate_ms)

                trace += rng.normal(0.0, 0.08, n_samples).astype(np.float32)
                cube[il_idx, xl_idx, :] = trace

        self.data = cube
        self.inlines = np.arange(n_inlines, dtype=np.int64)
        self.crosslines = np.arange(n_crosslines, dtype=np.int64)
        self.n_samples = n_samples
        self.sample_rate = sample_rate_ms
        self.mode = "3d"
        self.is_2d = False
        self.source_format = "SYNTHETIC"
        self.synthetic_reason = reason
        self.geometry_info = {
            "selected_pair": ("Inline", "Crossline"),
            "n_inlines": n_inlines,
            "n_crosslines": n_crosslines,
            "trace_count": n_inlines * n_crosslines,
            "fill_ratio": 1.0,
            "source": "synthetic",
        }
        self.header_info = {
            "text_header": "",
            "binary_header": {},
            "trace_header_fields": [],
        }
        self.text_header = ""
        self.binary_header = {}
        self.load_report = build_load_report(self)

    def _ricker_wavelet(self, t_samples, frequency_hz, sample_rate_ms):
        t_seconds = np.asarray(t_samples, dtype=np.float32) * (sample_rate_ms / 1000.0)
        arg = np.pi * frequency_hz * t_seconds
        return (1.0 - 2.0 * arg * arg) * np.exp(-(arg * arg))
