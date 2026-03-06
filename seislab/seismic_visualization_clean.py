# #!/usr/bin/env python3
# """
# Clean Interactive 3D Seismic Visualization

# Usage:
#   python3 seismic_visualization_clean.py --segy ST8511r92.segy --html out.html
# """

# import argparse
# import numpy as np
# import segyio
# import plotly.graph_objects as go
# import matplotlib.pyplot as plt
# from matplotlib import cm


# class InteractiveSeismicViewer:
#     def __init__(self, segy_file, n_inline=None, n_crossline=None):
#         self.segy_file = segy_file
#         self.n_inline = n_inline
#         self.n_crossline = n_crossline
#         self.data = None
#         self.sample_rate_ms = 4.0
#         self.t0 = 0.0
#         self.load_data()

#     def _cube_from_headers(self, f, traces):
#         """Build (inline, crossline, sample) cube from trace headers if possible."""
#         try:
#             il = np.asarray(f.attributes(segyio.TraceField.INLINE_3D)[:], dtype=np.int64)
#             xl = np.asarray(f.attributes(segyio.TraceField.CROSSLINE_3D)[:], dtype=np.int64)
#         except Exception:
#             return None

#         if il.size == 0 or xl.size == 0 or il.size != xl.size:
#             return None

#         inlines = np.unique(il)
#         crosslines = np.unique(xl)
#         if inlines.size < 2 or crosslines.size < 2:
#             return None

#         i_idx = np.searchsorted(inlines, il)
#         x_idx = np.searchsorted(crosslines, xl)

#         n_traces, n_samples = traces.shape
#         cube = np.zeros((inlines.size, crosslines.size, n_samples), dtype=np.float32)
#         counts = np.zeros((inlines.size, crosslines.size), dtype=np.int32)

#         for t in range(n_traces):
#             i = i_idx[t]
#             x = x_idx[t]
#             cube[i, x, :] += traces[t, :]
#             counts[i, x] += 1

#         coverage = np.count_nonzero(counts) / counts.size
#         if coverage < 0.90:
#             return None

#         nz = counts > 0
#         cube[nz, :] /= counts[nz, np.newaxis]
#         return cube

#     def load_data(self):
#         print("Loading SEG-Y file...")
#         with segyio.open(self.segy_file, strict=False) as f:
#             traces = np.asarray(f.trace.raw[:], dtype=np.float32)
#             if traces.ndim != 2 or traces.shape[0] == 0 or traces.shape[1] == 0:
#                 raise ValueError("Invalid SEG-Y trace data.")

#             try:
#                 dt_us = segyio.tools.dt(f)
#                 if dt_us:
#                     self.sample_rate_ms = dt_us / 1000.0
#             except Exception:
#                 self.sample_rate_ms = 4.0

#             samples = getattr(f, "samples", None)
#             if samples is not None and len(samples) > 0:
#                 self.t0 = float(samples[0])
#             else:
#                 self.t0 = 0.0

#             cube = None
#             try:
#                 cube = segyio.tools.cube(f)
#             except Exception:
#                 cube = None

#             if cube is None or cube.ndim != 3:
#                 cube = self._cube_from_headers(f, traces)

#             if cube is None:
#                 n_traces, n_samples = traces.shape
#                 if self.n_inline and self.n_crossline:
#                     ni = int(self.n_inline)
#                     nx = int(self.n_crossline)
#                     n_use = min(n_traces, ni * nx)
#                     if n_use < ni * nx:
#                         raise ValueError(
#                             f"Requested n_inline*n_crossline={ni*nx}, but file has {n_traces} traces."
#                         )
#                     cube = traces[:n_use, :].reshape(ni, nx, n_samples)
#                 else:
#                     # Safe fallback to avoid chaotic fake geometry.
#                     cube = traces.reshape(n_traces, 1, n_samples)
#                     print("Warning: geometry not found. Using (trace, 1, sample) fallback.")

#             self.data = np.asarray(cube, dtype=np.float32)
#             ni, nx, nt = self.data.shape
#             print(f"Loaded cube: {ni} inlines x {nx} crosslines x {nt} samples")
#             print(f"Sample rate: {self.sample_rate_ms:.3f} ms")
#             print(f"Amplitude range: [{self.data.min():.2f}, {self.data.max():.2f}]")

#     def _clip_limits(self, clip_percentile=98.0):
#         p = float(np.percentile(np.abs(self.data), clip_percentile))
#         p = max(p, 1e-12)
#         return -p, p

#     def plot_interactive_3d(
#         self,
#         inline_idx=None,
#         xline_idx=None,
#         timeslice_idx=None,
#         clip_percentile=98.0,
#         decimate_xy=1,
#         decimate_t=1,
#         show_timeslice=True,
#         save_html=None,
#     ):
#         ni, nx, nt = self.data.shape
#         inline_idx = ni // 2 if inline_idx is None else int(np.clip(inline_idx, 0, ni - 1))
#         xline_idx = nx // 2 if xline_idx is None else int(np.clip(xline_idx, 0, nx - 1))
#         timeslice_idx = nt // 2 if timeslice_idx is None else int(np.clip(timeslice_idx, 0, nt - 1))

#         decimate_xy = max(1, int(decimate_xy))
#         decimate_t = max(1, int(decimate_t))

#         vmin, vmax = self._clip_limits(clip_percentile)
#         z_all = self.t0 + np.arange(nt) * self.sample_rate_ms

#         fig = go.Figure()

#         # Inline surface
#         x_inline = np.arange(0, nx, decimate_xy)
#         z_inline = z_all[::decimate_t]
#         inline_data = self.data[inline_idx, x_inline, :][:, ::decimate_t].T
#         fig.add_trace(
#             go.Surface(
#                 x=np.tile(x_inline, (z_inline.size, 1)),
#                 y=np.full((z_inline.size, x_inline.size), inline_idx, dtype=float),
#                 z=np.tile(z_inline[:, np.newaxis], (1, x_inline.size)),
#                 surfacecolor=inline_data,
#                 colorscale="RdBu_r",
#                 cmin=vmin,
#                 cmax=vmax,
#                 name=f"Inline {inline_idx}",
#                 showscale=True,
#                 colorbar=dict(title="Amplitude", x=1.02, len=0.72),
#             )
#         )

#         # Crossline surface
#         y_xline = np.arange(0, ni, decimate_xy)
#         z_xline = z_all[::decimate_t]
#         xline_data = self.data[y_xline, xline_idx, :][:, ::decimate_t].T
#         fig.add_trace(
#             go.Surface(
#                 x=np.full((z_xline.size, y_xline.size), xline_idx, dtype=float),
#                 y=np.tile(y_xline, (z_xline.size, 1)),
#                 z=np.tile(z_xline[:, np.newaxis], (1, y_xline.size)),
#                 surfacecolor=xline_data,
#                 colorscale="RdBu_r",
#                 cmin=vmin,
#                 cmax=vmax,
#                 name=f"Crossline {xline_idx}",
#                 showscale=False,
#                 opacity=0.98,
#             )
#         )

#         # Timeslice surface (optional)
#         if show_timeslice:
#             x_ts = np.arange(0, nx, decimate_xy)
#             y_ts = np.arange(0, ni, decimate_xy)
#             ts_data = self.data[np.ix_(y_ts, x_ts, [timeslice_idx])][:, :, 0]
#             X_ts, Y_ts = np.meshgrid(x_ts, y_ts)
#             fig.add_trace(
#                 go.Surface(
#                     x=X_ts,
#                     y=Y_ts,
#                     z=np.full_like(X_ts, z_all[timeslice_idx], dtype=float),
#                     surfacecolor=ts_data,
#                     colorscale="RdBu_r",
#                     cmin=vmin,
#                     cmax=vmax,
#                     name=f"Timeslice {timeslice_idx}",
#                     showscale=False,
#                     opacity=0.86,
#                 )
#             )

#         fig.update_layout(
#             title=dict(
#                 text=f"3D Seismic Cube<br>Inline {inline_idx} | Crossline {xline_idx}",
#                 x=0.5,
#                 xanchor="center",
#                 font=dict(size=20, color="white"),
#             ),
#             scene=dict(
#                 xaxis=dict(
#                     title="Crossline",
#                     backgroundcolor="rgb(20,20,20)",
#                     gridcolor="rgb(60,60,60)",
#                     showbackground=True,
#                     color="white",
#                 ),
#                 yaxis=dict(
#                     title="Inline",
#                     backgroundcolor="rgb(20,20,20)",
#                     gridcolor="rgb(60,60,60)",
#                     showbackground=True,
#                     color="white",
#                 ),
#                 zaxis=dict(
#                     title="Time (ms)",
#                     backgroundcolor="rgb(20,20,20)",
#                     gridcolor="rgb(60,60,60)",
#                     showbackground=True,
#                     autorange="reversed",
#                     color="white",
#                 ),
#                 camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
#                 aspectmode="manual",
#                 aspectratio=dict(x=1, y=1, z=1.25),
#             ),
#             paper_bgcolor="rgb(10,10,10)",
#             plot_bgcolor="rgb(10,10,10)",
#             font=dict(color="white", size=12),
#             width=1400,
#             height=900,
#             margin=dict(l=0, r=0, t=80, b=0),
#         )

#         if save_html:
#             fig.write_html(save_html)
#             print(f"Saved interactive HTML: {save_html}")

#         fig.show()
#         return fig

#     def plot_clean_matplotlib(
#         self,
#         inline_idx=None,
#         xline_idx=None,
#         clip_percentile=98.0,
#         decimate_xy=1,
#         decimate_t=1,
#         figsize=(14, 10),
#         save_path=None,
#     ):
#         ni, nx, nt = self.data.shape
#         inline_idx = ni // 2 if inline_idx is None else int(np.clip(inline_idx, 0, ni - 1))
#         xline_idx = nx // 2 if xline_idx is None else int(np.clip(xline_idx, 0, nx - 1))

#         decimate_xy = max(1, int(decimate_xy))
#         decimate_t = max(1, int(decimate_t))

#         vmin, vmax = self._clip_limits(clip_percentile)
#         norm = plt.Normalize(vmin=vmin, vmax=vmax)
#         cmap = plt.cm.seismic

#         x_coords = np.arange(0, nx, decimate_xy)
#         y_coords = np.arange(0, ni, decimate_xy)
#         z_coords = self.t0 + np.arange(0, nt, decimate_t) * self.sample_rate_ms

#         fig = plt.figure(figsize=figsize, facecolor="#0a0a0a")
#         ax = fig.add_subplot(111, projection="3d")
#         ax.set_facecolor("#0a0a0a")

#         inline_data = self.data[inline_idx, x_coords, :][:, ::decimate_t].T
#         X_inline, Z_inline = np.meshgrid(x_coords, z_coords)
#         Y_inline = np.full_like(X_inline, inline_idx, dtype=float)
#         ax.plot_surface(
#             X_inline,
#             Y_inline,
#             Z_inline,
#             facecolors=cmap(norm(inline_data)),
#             shade=False,
#             antialiased=False,
#             linewidth=0,
#             alpha=1.0,
#         )

#         xline_data = self.data[y_coords, xline_idx, :][:, ::decimate_t].T
#         Y_xline, Z_xline = np.meshgrid(y_coords, z_coords)
#         X_xline = np.full_like(Y_xline, xline_idx, dtype=float)
#         ax.plot_surface(
#             X_xline,
#             Y_xline,
#             Z_xline,
#             facecolors=cmap(norm(xline_data)),
#             shade=False,
#             antialiased=False,
#             linewidth=0,
#             alpha=1.0,
#         )

#         ax.set_xlabel("Crossline", color="white", fontweight="bold")
#         ax.set_ylabel("Inline", color="white", fontweight="bold")
#         ax.set_zlabel("Time (ms)", color="white", fontweight="bold")
#         ax.set_xlim(0, nx - 1 if nx > 1 else 1)
#         ax.set_ylim(0, ni - 1 if ni > 1 else 1)
#         ax.invert_zaxis()
#         ax.tick_params(colors="white", labelsize=9)
#         ax.grid(True, alpha=0.15, color="#666666", linewidth=0.5)
#         ax.view_init(elev=25, azim=-65)

#         title = f"Seismic Volume 3D View\nInline {inline_idx} | Crossline {xline_idx}"
#         plt.title(title, fontsize=15, fontweight="bold", color="white", pad=16)

#         mappable = cm.ScalarMappable(cmap="seismic", norm=norm)
#         cbar = plt.colorbar(mappable, ax=ax, pad=0.12, shrink=0.6, aspect=15)
#         cbar.set_label("Amplitude", color="white", fontweight="bold")
#         cbar.ax.tick_params(colors="white", labelsize=9)

#         if save_path:
#             plt.savefig(save_path, dpi=160, bbox_inches="tight", facecolor="#0a0a0a")
#             print(f"Saved figure: {save_path}")

#         plt.show()


# def main():
#     parser = argparse.ArgumentParser(description="Clean 3D seismic visualization.")
#     parser.add_argument("--segy", required=True, help="Path to SEG-Y file")
#     parser.add_argument("--n-inline", type=int, default=None, help="Manual inline count (fallback only)")
#     parser.add_argument("--n-crossline", type=int, default=None, help="Manual crossline count (fallback only)")
#     parser.add_argument("--inline", type=int, default=None, help="Inline index")
#     parser.add_argument("--xline", type=int, default=None, help="Crossline index")
#     parser.add_argument("--timeslice", type=int, default=None, help="Timeslice index")
#     parser.add_argument("--clip", type=float, default=98.0, help="Clip percentile")
#     parser.add_argument("--decimate-xy", type=int, default=1, help="Spatial decimation step")
#     parser.add_argument("--decimate-t", type=int, default=1, help="Time decimation step")
#     parser.add_argument("--no-timeslice", action="store_true", help="Hide horizontal timeslice plane")
#     parser.add_argument("--html", default=None, help="Output interactive HTML path")
#     parser.add_argument("--matplotlib", action="store_true", help="Also show Matplotlib 3D")
#     args = parser.parse_args()

#     viz = InteractiveSeismicViewer(
#         args.segy,
#         n_inline=args.n_inline,
#         n_crossline=args.n_crossline,
#     )

#     viz.plot_interactive_3d(
#         inline_idx=args.inline,
#         xline_idx=args.xline,
#         timeslice_idx=args.timeslice,
#         clip_percentile=args.clip,
#         decimate_xy=args.decimate_xy,
#         decimate_t=args.decimate_t,
#         show_timeslice=not args.no_timeslice,
#         save_html=args.html,
#     )

#     if args.matplotlib:
#         viz.plot_clean_matplotlib(
#             inline_idx=args.inline,
#             xline_idx=args.xline,
#             clip_percentile=args.clip,
#             decimate_xy=args.decimate_xy,
#             decimate_t=args.decimate_t,
#         )


# if __name__ == "__main__":
#     main()
