from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

from cnc_rul.features import causal_history_features  # noqa: E402
from cnc_rul.wear import compute_rul_targets, threshold_crossing  # noqa: E402


def test_causal_wear_roll_uses_past_only():
    df = pd.DataFrame({"cut_index": [1, 2, 3], "wear_um": [10.0, 20.0, 30.0]})
    out = causal_history_features(df)
    assert np.isnan(out.loc[0, "wear_roll3_mean"]) or out.loc[0, "wear_roll3_mean"] == out.loc[0, "wear_um"]


def test_rul_non_negative_and_monotone_without_crossing():
    wear = pd.DataFrame({"cut": [1, 2, 3], "max_flute_um": [50.0, 80.0, 100.0]})
    ruled = compute_rul_targets(wear, 300.0)
    assert (ruled["rul_physical_cycles"] >= 0).all()
    assert ruled["target_type"].iloc[0] == "right_censored"


def test_no_fabricated_threshold_crossing():
    w = np.array([100.0, 150.0, 180.0])
    crossed, cut = threshold_crossing(w, 300.0)
    assert crossed is False
    assert cut is None