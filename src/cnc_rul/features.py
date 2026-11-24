from __future__ import annotations

import numpy as np
import pandas as pd


def causal_history_features(frame: pd.DataFrame, wear_col: str = "wear_um") -> pd.DataFrame:
    """Rolling features using only past and current cuts (no future leakage)."""
    out = frame.sort_values("cut_index").copy()
    out["cycles_completed"] = out["cut_index"].astype(int)
    for w in (3, 5, 10):
        out[f"wear_roll{w}_mean"] = out[wear_col].shift(1).rolling(w, min_periods=1).mean()
        out[f"wear_delta_{w}"] = out[wear_col] - out[wear_col].shift(w)
    out["cumulative_exposure"] = out["cycles_completed"]
    out["wear_rate_1"] = out[wear_col].diff().fillna(0.0)
    return out


def feature_columns(frame: pd.DataFrame) -> list[str]:
    skip = {
        "tool",
        "cut_index",
        "n_samples",
        "wear_mm_observed",
        "wear_um_observed",
        "wear_um_official",
        "wear_um",
        "wear_label_source",
        "threshold_um",
        "crossed_threshold",
        "rul_physical_cycles",
        "rul_recorded_cycles",
        "target_type",
        "life_stage",
        "y_rul",
        "y_wear_next",
    }
    cols = [c for c in frame.columns if c not in skip and frame[c].dtype.kind in "fiu"]
    return cols


def add_prospective_rows(dataset: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Each row is a prediction opportunity at cut_index with target known only for evaluation."""
    dataset = dataset.copy()
    dataset["y_rul"] = dataset[target_col].astype(float)
    return dataset