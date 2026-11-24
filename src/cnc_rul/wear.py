from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class WearAuditResult:
    tool: str
    n_cuts: int
    max_wear_um: float
    threshold_um: float
    crossed: bool
    crossing_cut: int | None
    right_censored: bool
    wear_source: str


def load_flute_wear_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "cut" not in df.columns:
        raise ValueError(f"{path}: expected 'cut' column")
    flute_cols = [c for c in df.columns if c.startswith("flute")]
    if len(flute_cols) < 1:
        raise ValueError(f"{path}: no flute columns")
    out = df[["cut", *flute_cols]].copy()
    out["max_flute_um"] = out[flute_cols].max(axis=1)
    return out


def build_c1_wear_from_bundle(bundle: pd.DataFrame, wear_dir: Path) -> Path:
    """Derive c1 max wear per bundle segment; official per-flute file not available locally."""
    d = bundle[bundle["experiment_tag"] == "c1"].copy()
    seg = (d["tool_wear"] != d["tool_wear"].shift()).cumsum()
    rows = []
    for i, (_, g) in enumerate(d.groupby(seg, sort=True), start=1):
        rows.append({"cut": i, "flute_1": np.nan, "flute_2": np.nan, "flute_3": np.nan,
                       "max_flute_um": float(g["tool_wear"].iloc[0]) * 1000.0})
    out = pd.DataFrame(rows)
    path = wear_dir / "c1_wear_bundle.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    return path


def load_tool_wear(tool: str, wear_dir: Path, bundle: pd.DataFrame) -> pd.DataFrame:
    official = wear_dir / f"{tool}_wear.csv"
    if official.exists() and official.stat().st_size > 100:
        return load_flute_wear_csv(official)
    if tool == "c1":
        bundle_path = wear_dir / "c1_wear_bundle.csv"
        if not bundle_path.exists():
            build_c1_wear_from_bundle(bundle, wear_dir)
        df = pd.read_csv(bundle_path)
        return df
    raise FileNotFoundError(f"No wear file for {tool} in {wear_dir}")


def threshold_crossing(max_wear_um: np.ndarray, threshold_um: float) -> tuple[bool, int | None]:
    mask = max_wear_um >= threshold_um
    if not mask.any():
        return False, None
    idx = int(np.argmax(mask)) + 1
    return True, idx


def audit_wear_table(df: pd.DataFrame, tool: str, threshold_um: float, wear_source: str) -> WearAuditResult:
    max_w = df["max_flute_um"].to_numpy(dtype=float)
    crossed, cut = threshold_crossing(max_w, threshold_um)
    return WearAuditResult(
        tool=tool,
        n_cuts=len(df),
        max_wear_um=float(np.nanmax(max_w)),
        threshold_um=threshold_um,
        crossed=crossed,
        crossing_cut=cut,
        right_censored=not crossed,
        wear_source=wear_source,
    )


def compute_rul_targets(
    df: pd.DataFrame,
    threshold_um: float,
    *,
    allow_recorded_horizon: bool = True,
) -> pd.DataFrame:
    """
    RUL at cut t = first crossing cut minus t (if crossed), else right-censored remaining recorded cuts.
    """
    max_w = df["max_flute_um"].to_numpy(dtype=float)
    crossed, cross_cut = threshold_crossing(max_w, threshold_um)
    n = len(df)
    cuts = df["cut"].to_numpy(dtype=int)
    out = df.copy()
    out["threshold_um"] = threshold_um
    out["crossed_threshold"] = crossed
    if crossed and cross_cut is not None:
        out["rul_physical_cycles"] = np.maximum(cross_cut - cuts, 0)
        out["target_type"] = "physical_threshold"
    else:
        out["rul_physical_cycles"] = np.maximum(n - cuts + 1, 0)
        out["target_type"] = "right_censored"
    if allow_recorded_horizon:
        out["rul_recorded_cycles"] = np.maximum(n - cuts + 1, 0)
    return out