from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from cnc_rul.baselines import (
    baseline_cycle_only,
    baseline_fixed_lifetime,
    baseline_linear_wear_extrapolation,
)
from cnc_rul.config import ProjectConfig
from cnc_rul.features import add_prospective_rows, causal_history_features, feature_columns
from cnc_rul.models import build_model_bank, fit_predict
from cnc_rul.phm_data import align_wear_labels, load_bundle, segment_bundle_by_wear_step
from cnc_rul.validation import loro_evaluate
from cnc_rul.wear import audit_wear_table, compute_rul_targets, load_tool_wear
from cnc_rul import visualize


def build_master_table(cfg: ProjectConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    bundle_path = cfg.resolve(cfg.bundle_csv)
    bundle = load_bundle(bundle_path)
    parts: list[pd.DataFrame] = []
    audits: list[dict] = []

    wear_sources = {}
    for tool in cfg.tools:
        wear_df = load_tool_wear(tool, cfg.resolve(cfg.wear_dir), bundle)
        src = "official_flute" if (cfg.resolve(cfg.wear_dir) / f"{tool}_wear.csv").exists() else "bundle_derived"
        wear_sources[tool] = src
        ar = audit_wear_table(wear_df, tool, cfg.default_threshold_um, src)
        audits.append(ar.__dict__)
        ruled = compute_rul_targets(wear_df, cfg.default_threshold_um)
        feats = segment_bundle_by_wear_step(bundle, tool)
        merged = align_wear_labels(feats, wear_df)
        merged = merged.merge(
            ruled[["cut", "rul_physical_cycles", "rul_recorded_cycles", "target_type", "crossed_threshold"]],
            left_on="cut_index",
            right_on="cut",
            how="left",
        )
        merged.drop(columns=["cut"], inplace=True, errors="ignore")
        merged["tool"] = tool
        merged["threshold_um"] = cfg.default_threshold_um
        merged = causal_history_features(merged, wear_col="wear_um")
        merged = add_prospective_rows(merged, "rul_physical_cycles")
        parts.append(merged)

    master = pd.concat(parts, ignore_index=True)
    audit_df = pd.DataFrame(audits)
    return master, audit_df


def run_pipeline(cfg: ProjectConfig) -> dict:
    cfg.resolve(cfg.metrics_dir).mkdir(parents=True, exist_ok=True)
    cfg.resolve(cfg.tables_dir).mkdir(parents=True, exist_ok=True)
    cfg.resolve(cfg.figures_dir).mkdir(parents=True, exist_ok=True)

    master, audit_df = build_master_table(cfg)
    master.to_csv(cfg.resolve(cfg.tables_dir) / "master_cut_features.csv", index=False)
    audit_df.to_csv(cfg.resolve(cfg.tables_dir) / "wear_audit.csv", index=False)

    identical_lengths = master.groupby("tool")["cut_index"].max().nunique() == 1
    summary = {
        "n_tools": master["tool"].nunique(),
        "identical_max_cuts_across_tools": bool(identical_lengths),
        "default_threshold_um": cfg.default_threshold_um,
        "any_threshold_crossing_300um": bool(audit_df["crossed"].any()),
    }

    cols = feature_columns(master)
    # Exclude wear-derived history if sensor-only scenario
    sensor_cols = [c for c in cols if not c.startswith("wear_") and c not in ("wear_um",)]

    all_metrics: list[dict] = []
    all_preds: list[pd.DataFrame] = []

    def ml_predict(train: pd.DataFrame, test: pd.DataFrame, use_cols: list[str], model):
        X_tr = train[use_cols].fillna(0.0).to_numpy(dtype=float)
        y_tr = train["y_rul"].to_numpy(dtype=float)
        X_te = test[use_cols].fillna(0.0).to_numpy(dtype=float)
        pred, _ = fit_predict(model, X_tr, y_tr, X_te)
        return pred

    train_max_cut = float(master.groupby("tool")["cut_index"].max().median())

    for target_name, target_col in (
        ("physical_rul", "y_rul"),
        ("recorded_horizon", "rul_recorded_cycles"),
    ):
        subset = master.copy()
        subset["y_rul"] = subset[target_col if target_col != "y_rul" else "rul_physical_cycles"]

        def fixed_bl(tr, te):
            return baseline_fixed_lifetime(tr, te, "y_rul")

        def cycle_bl(tr, te):
            return baseline_cycle_only(te, train_max_cut)

        def lin_bl(tr, te):
            return baseline_linear_wear_extrapolation(te)

        for name, fn in (
            ("baseline_fixed_lifetime", fixed_bl),
            ("baseline_cycle_only", cycle_bl),
            ("baseline_linear_wear", lin_bl),
        ):
            pred_df, metrics = loro_evaluate(subset, fn, model_name=name)
            all_preds.append(pred_df)
            all_metrics.extend([m.__dict__ | {"scenario": "sensor_features" if name != "baseline_cycle_only" else "cycle_only"}
                                for m in metrics])

        for spec in build_model_bank(cfg.random_seed):
            model = spec.estimator

            def make_predictor(m, cols):
                def _fn(tr, te):
                    return ml_predict(tr, te, cols, m)
                return _fn

            pred_df, metrics = loro_evaluate(
                subset,
                make_predictor(model, sensor_cols),
                model_name=f"ml_{spec.name}",
            )
            all_preds.append(pred_df)
            all_metrics.extend([m.__dict__ | {"scenario": "sensor_only"} for m in metrics])

    metrics_df = pd.DataFrame(all_metrics)
    pred_df = pd.concat(all_preds, ignore_index=True)
    metrics_df.to_csv(cfg.resolve(cfg.tables_dir) / "model_metrics.csv", index=False)
    pred_df.to_csv(cfg.resolve(cfg.tables_dir) / "predictions_loro.csv", index=False)

    visualize.make_all_figures(cfg, master, audit_df, metrics_df, pred_df)

    # Threshold sensitivity
    sens_rows = []
    for th in cfg.sensitivity_thresholds_um:
        for tool in cfg.tools:
            w = load_tool_wear(tool, cfg.resolve(cfg.wear_dir), load_bundle(cfg.resolve(cfg.bundle_csv)))
            ar = audit_wear_table(w, tool, th, "mixed")
            sens_rows.append({"threshold_um": th, **ar.__dict__})
    pd.DataFrame(sens_rows).to_csv(cfg.resolve(cfg.tables_dir) / "threshold_sensitivity.csv", index=False)

    # Missing sensor robustness (drop groups)
    robust_rows = []
    groups = {
        "all": sensor_cols,
        "no_force": [c for c in sensor_cols if not c.startswith("force_")],
        "no_vibration": [c for c in sensor_cols if not c.startswith("vibration_")],
        "no_ae": [c for c in sensor_cols if "acoustic" not in c],
        "process_only": ["cycles_completed", "cumulative_exposure"],
    }
    subset = master.copy()
    subset["y_rul"] = subset["rul_physical_cycles"]
    spec = build_model_bank(cfg.random_seed)[1]  # RF

    for gname, gcols in groups.items():
        use = [c for c in gcols if c in subset.columns]
        if not use:
            continue

        def fn(tr, te, u=use, m=spec.estimator):
            return ml_predict(tr, te, u, m)

        _, mets = loro_evaluate(subset, fn, model_name=f"rf_{gname}")
        for m in mets:
            robust_rows.append({**m.__dict__, "sensor_group": gname})
    pd.DataFrame(robust_rows).to_csv(cfg.resolve(cfg.tables_dir) / "robustness_missing_sensors.csv", index=False)

    summary["metrics_path"] = str(cfg.resolve(cfg.tables_dir) / "model_metrics.csv")
    with (cfg.resolve(cfg.metrics_dir) / "pipeline_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    return summary