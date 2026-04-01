from typing import Dict, Tuple

import numpy as np
import pandas as pd


def compute_vshale(
    df: pd.DataFrame,
    gr_curve: str,
    gr_clean: float,
    gr_shale: float,
    method: str = "linear",
    clip: bool = True,
) -> pd.Series:
    if gr_curve not in df:
        raise ValueError(f"Curve not found: {gr_curve}")

    denom = (gr_shale - gr_clean) if (gr_shale - gr_clean) != 0 else np.nan
    igr = (df[gr_curve] - gr_clean) / denom

    m = method.lower()
    if "larionov" in m and "tertiary" in m:
        vsh = 0.083 * (2 ** (3.7 * igr) - 1)
    elif "larionov" in m:
        vsh = 0.33 * (2 ** (2 * igr) - 1)
    elif "clavier" in m:
        vsh = 1.7 - np.sqrt(3.38 - (igr + 0.7) ** 2)
    elif "steiber" in m:
        vsh = igr / (3 - 2 * igr)
    else:
        vsh = igr

    if clip:
        vsh = vsh.clip(lower=0, upper=1)
    return vsh


def compute_density_porosity(rhob: pd.Series, rho_matrix: float, rho_fluid: float) -> pd.Series:
    denom = (rho_matrix - rho_fluid) if (rho_matrix - rho_fluid) != 0 else np.nan
    return ((rho_matrix - rhob) / denom).clip(lower=0, upper=1)


def compute_nd_porosity(nphi: pd.Series, phid: pd.Series, quadratic: bool = False) -> pd.Series:
    if quadratic:
        return np.sqrt((nphi**2 + phid**2) / 2.0).clip(lower=0, upper=1)
    return ((nphi + phid) / 2.0).clip(lower=0, upper=1)


def compute_sonic_porosity(dt: pd.Series, dt_ma: float, dt_fl: float) -> pd.Series:
    denom = (dt_fl - dt_ma) if (dt_fl - dt_ma) != 0 else np.nan
    return ((dt - dt_ma) / denom).clip(lower=0, upper=1)


def compute_effective_porosity(phit: pd.Series, vsh: pd.Series, phi_sh: float) -> pd.Series:
    return (phit - (vsh * phi_sh)).clip(lower=0, upper=1)


def compute_archie_sw(
    rt: pd.Series,
    phie: pd.Series,
    rw: float,
    a: float = 1.0,
    m: float = 2.0,
    n: float = 2.0,
) -> pd.Series:
    rt_safe = rt.replace(0, np.nan)
    phie_safe = phie.replace(0, np.nan)
    sw = ((a * rw) / (rt_safe * (phie_safe**m))) ** (1.0 / n)
    return sw.clip(lower=0, upper=1)


def compute_timur_perm(phie: pd.Series, swirr: pd.Series, c: float = 100.0, a: float = 4.4, b: float = 2.0) -> pd.Series:
    sw_safe = swirr.replace(0, np.nan)
    k = c * ((phie**a) / (sw_safe**b))
    return k.clip(lower=0)


def compute_net_pay_summary(
    df: pd.DataFrame,
    depth_col: str,
    top: float,
    base: float,
    vsh_curve: str,
    phie_curve: str,
    sw_curve: str,
    perm_curve: str,
    vsh_cut: float,
    phie_cut: float,
    sw_cut: float,
    k_cut: float,
) -> Tuple[Dict[str, float], pd.Series]:
    if depth_col not in df:
        raise ValueError("Depth column is missing")

    zone = df[(df[depth_col] >= top) & (df[depth_col] <= base)].copy()
    if zone.empty:
        return {
            "gross_m": 0.0,
            "net_res_m": 0.0,
            "net_pay_m": 0.0,
            "ntg": 0.0,
        }, pd.Series(index=df.index, dtype=float)

    depth = zone[depth_col].dropna()
    step = float(depth.diff().median()) if len(depth) > 1 else 0.0
    gross = max(base - top, 0.0)

    net_res_flag = (zone[vsh_curve] <= vsh_cut) & (zone[phie_curve] >= phie_cut)
    net_pay_flag = net_res_flag & (zone[sw_curve] <= sw_cut) & (zone[perm_curve] >= k_cut)

    net_res = float(net_res_flag.sum() * step)
    net_pay = float(net_pay_flag.sum() * step)
    ntg = (net_res / gross) if gross > 0 else 0.0

    full_flag = pd.Series(False, index=df.index)
    full_flag.loc[zone.index] = net_pay_flag

    return {
        "gross_m": gross,
        "net_res_m": net_res,
        "net_pay_m": net_pay,
        "ntg": ntg,
    }, full_flag
