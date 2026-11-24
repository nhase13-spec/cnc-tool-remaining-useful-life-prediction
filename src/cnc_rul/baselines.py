from __future__ import annotations

import numpy as np
import pandas as pd


def baseline_fixed_lifetime(train: pd.DataFrame, test: pd.DataFrame, target_col: str) -> np.ndarray:
    """Mean terminal horizon from training tools only."""
    terminal = train.groupby("tool")["cut_index"].max().mean()
    return np.maximum(terminal - test["cut_index"].to_numpy(dtype=float) + 1, 0)


def baseline_cycle_only(test: pd.DataFrame, global_max_cut: float) -> np.ndarray:
    """Remaining recorded cuts from training max cut (no sensor info)."""
    return np.maximum(global_max_cut - test["cut_index"].to_numpy(dtype=float) + 1, 0)


def baseline_linear_wear_extrapolation(test: pd.DataFrame, wear_col: str = "wear_um") -> np.ndarray:
    """Extrapolate linear wear rate from history prefix at each row (uses only past wear)."""
    preds = []
    wears = test.sort_values("cut_index")[wear_col].to_numpy(dtype=float)
    cuts = test.sort_values("cut_index")["cut_index"].to_numpy(dtype=float)
    threshold_um = float(test["threshold_um"].iloc[0]) if "threshold_um" in test else 300.0
    for i in range(len(wears)):
        if i < 2:
            preds.append(float(len(wears) - i))
            continue
        x = cuts[: i + 1]
        y = wears[: i + 1]
        coef = np.polyfit(x, y, 1)
        rate = coef[0]
        if rate <= 1e-9:
            preds.append(float(len(wears) - i))
            continue
        remaining_wear = threshold_um - y[-1]
        if remaining_wear <= 0:
            preds.append(0.0)
        else:
            preds.append(max(remaining_wear / rate, 0.0))
    order = test.sort_values("cut_index").index
    out = np.zeros(len(test))
    for j, idx in enumerate(order):
        loc = test.index.get_loc(idx)
        out[loc] = preds[j]
    return out


def baseline_persistence_wear(test: pd.DataFrame, wear_col: str = "wear_um") -> np.ndarray:
    """If wear known at prediction time (oracle scenario), predict no further wear change."""
    if wear_col not in test:
        return np.zeros(len(test))
    threshold = float(test["threshold_um"].iloc[0])
    gap = np.maximum(threshold - test[wear_col].to_numpy(dtype=float), 0.0)
    return gap  # proxy cycles — documented as wear-gap not true RUL