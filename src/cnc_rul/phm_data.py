from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from cnc_rul.wear import load_tool_wear


SENSOR_COLUMNS = (
    "force_x",
    "force_y",
    "force_z",
    "vibration_x",
    "vibration_y",
    "vibration_z",
    "acoustic_emission_rms",
)


def load_bundle(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"experiment_tag", "tool_wear", *SENSOR_COLUMNS}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Bundle missing columns: {sorted(missing)}")
    return df


def segment_bundle_by_wear_step(bundle: pd.DataFrame, tool: str) -> pd.DataFrame:
    """One row per wear step (proxy cut) with aggregated sensor statistics."""
    d = bundle[bundle["experiment_tag"] == tool].copy()
    if d.empty:
        raise ValueError(f"No rows for tool {tool}")
    d["wear_step"] = (d["tool_wear"] != d["tool_wear"].shift()).cumsum()
    rows: list[dict] = []
    for step, g in d.groupby("wear_step", sort=True):
        row: dict = {
            "tool": tool,
            "cut_index": int(step),
            "n_samples": len(g),
            "wear_mm_observed": float(g["tool_wear"].iloc[0]),
            "wear_um_observed": float(g["tool_wear"].iloc[0]) * 1000.0,
        }
        for col in SENSOR_COLUMNS:
            vals = g[col].to_numpy(dtype=float)
            row[f"{col}_mean"] = float(np.mean(vals))
            row[f"{col}_std"] = float(np.std(vals))
            row[f"{col}_rms"] = float(np.sqrt(np.mean(vals**2)))
            row[f"{col}_max"] = float(np.max(vals))
        rows.append(row)
    return pd.DataFrame(rows)


def align_wear_labels(
    per_cut_features: pd.DataFrame,
    wear_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Map official wear table (315 cuts) onto bundle-derived feature rows by cut index.
    When lengths differ, join on cut index and mark alignment quality.
    """
    merged = per_cut_features.merge(
        wear_df[["cut", "max_flute_um"]].rename(columns={"cut": "cut_index", "max_flute_um": "wear_um_official"}),
        on="cut_index",
        how="left",
    )
    merged["wear_um"] = merged["wear_um_official"].fillna(merged["wear_um_observed"])
    merged["wear_label_source"] = np.where(
        merged["wear_um_official"].notna(),
        "official_flute",
        "bundle_segment",
    )
    return merged