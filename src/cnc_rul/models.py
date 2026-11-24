from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class ModelSpec:
    name: str
    estimator: Any


def build_model_bank(random_state: int = 42) -> list[ModelSpec]:
    bank: list[ModelSpec] = [
        ModelSpec(
            "ridge",
            Pipeline([
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=1.0, random_state=random_state)),
            ]),
        ),
        ModelSpec(
            "random_forest",
            RandomForestRegressor(
                n_estimators=300,
                min_samples_leaf=2,
                random_state=random_state,
                n_jobs=-1,
            ),
        ),
    ]
    try:
        from xgboost import XGBRegressor

        bank.append(
            ModelSpec(
                "xgboost",
                XGBRegressor(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.9,
                    colsample_bytree=0.8,
                    random_state=random_state,
                    n_jobs=-1,
                ),
            )
        )
    except ImportError:
        pass

    kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
    bank.append(
        ModelSpec(
            "gaussian_process",
            Pipeline([
                ("scaler", StandardScaler()),
                (
                    "model",
                    GaussianProcessRegressor(
                        kernel=kernel,
                        random_state=random_state,
                        normalize_y=True,
                    ),
                ),
            ]),
        )
    )
    return bank


def fit_predict(
    model: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray | None]:
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return np.asarray(pred, dtype=float), None