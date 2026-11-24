from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from cnc_rul.features import feature_columns


@dataclass
class FoldMetrics:
    tool: str
    model: str
    mae: float
    rmse: float
    median_ae: float
    bias: float
    n_predictions: int
    target_name: str


def life_stage_label(cut_index: int, max_cut: int) -> str:
    frac = cut_index / max(max_cut, 1)
    if frac < 1.0 / 3.0:
        return "early"
    if frac < 2.0 / 3.0:
        return "middle"
    return "late"


def loro_evaluate(
    data: pd.DataFrame,
    predict_fn,
    *,
    model_name: str,
    target_col: str = "y_rul",
    tool_col: str = "tool",
) -> tuple[pd.DataFrame, list[FoldMetrics]]:
    """Leave-one-tool-out; predict_fn(train_df, test_df) -> predictions aligned to test_df index."""
    preds_rows: list[pd.DataFrame] = []
    metrics: list[FoldMetrics] = []
    tools = sorted(data[tool_col].unique())
    for held in tools:
        test = data[data[tool_col] == held].copy()
        train = data[data[tool_col] != held].copy()
        if train.empty or test.empty:
            continue
        y_hat = predict_fn(train, test)
        y = test[target_col].to_numpy(dtype=float)
        err = y_hat - y
        fold = FoldMetrics(
            tool=held,
            model=model_name,
            mae=float(np.mean(np.abs(err))),
            rmse=float(np.sqrt(np.mean(err**2))),
            median_ae=float(np.median(np.abs(err))),
            bias=float(np.mean(err)),
            n_predictions=len(test),
            target_name=target_col,
        )
        metrics.append(fold)
        stage_max = int(test["cut_index"].max())
        part = test.copy()
        part["y_true"] = y
        part["y_pred"] = y_hat
        part["error"] = err
        part["life_stage"] = part["cut_index"].apply(lambda c: life_stage_label(int(c), stage_max))
        part["model"] = model_name
        preds_rows.append(part)
    pred_df = pd.concat(preds_rows, ignore_index=True) if preds_rows else pd.DataFrame()
    return pred_df, metrics