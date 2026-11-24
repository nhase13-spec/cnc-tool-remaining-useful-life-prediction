from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from cnc_rul.config import ProjectConfig


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_all_figures(
    cfg: ProjectConfig,
    master: pd.DataFrame,
    audit_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    pred_df: pd.DataFrame,
) -> None:
    fig_dir = cfg.resolve(cfg.figures_dir)
    sns.set_theme(style="whitegrid", context="talk")

    # 1 Wear trajectories
    fig, ax = plt.subplots(figsize=(10, 5))
    for tool, g in master.groupby("tool"):
        ax.plot(g["cut_index"], g["wear_um"], label=tool)
    ax.axhline(cfg.default_threshold_um, color="crimson", ls="--", label=f"threshold {cfg.default_threshold_um} µm")
    ax.set_xlabel("Cut index (bundle wear step)")
    ax.set_ylabel("Max flank wear (µm)")
    ax.set_title("Measured / aligned wear histories")
    ax.legend()
    _save(fig, fig_dir / "01_wear_trajectories.png")

    # 2 Threshold audit
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = audit_df["crossed"].map({True: "tab:green", False: "tab:orange"})
    ax.bar(audit_df["tool"], audit_df["max_wear_um"], color=colors)
    ax.axhline(cfg.default_threshold_um, color="crimson", ls="--")
    ax.set_ylabel("Max observed wear (µm)")
    ax.set_title("Threshold crossing audit (green=crossed)")
    _save(fig, fig_dir / "02_threshold_audit.png")

    # 3 RUL construction illustration
    fig, ax = plt.subplots(figsize=(10, 5))
    sample = master[master["tool"] == "c6"]
    ax.plot(sample["cut_index"], sample["rul_physical_cycles"], label="RUL target")
    ax.set_xlabel("Cut index")
    ax.set_ylabel("RUL (cycles)")
    ax.set_title("RUL target construction (c6 example)")
    ax.legend()
    _save(fig, fig_dir / "03_rul_target_construction.png")

    if not pred_df.empty:
        ml_preds = pred_df[pred_df["model"].str.startswith("ml_")]
        if not ml_preds.empty:
            best_model = ml_preds["model"].value_counts().index[0]
            sub = pred_df[pred_df["model"] == best_model]
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.scatter(sub["y_true"], sub["y_pred"], alpha=0.35, s=20)
            lim = max(sub["y_true"].max(), sub["y_pred"].max())
            ax.plot([0, lim], [0, lim], "k--")
            ax.set_xlabel("Observed RUL")
            ax.set_ylabel("Predicted RUL")
            ax.set_title(f"Predicted vs observed ({best_model})")
            _save(fig, fig_dir / "04_pred_vs_observed.png")

        fig, ax = plt.subplots(figsize=(10, 5))
        stage = pred_df.groupby(["life_stage", "model"])["error"].apply(lambda s: np.mean(np.abs(s))).reset_index()
        stage = stage[stage["model"].str.contains("baseline|ml_random")]
        if not stage.empty:
            sns.barplot(data=stage, x="life_stage", y="error", hue="model", ax=ax)
            ax.set_ylabel("MAE (cycles)")
            ax.set_title("Error by life stage (retrospective labels)")
            ax.tick_params(axis="x", rotation=15)
            _save(fig, fig_dir / "07_life_stage_errors.png")

    if not metrics_df.empty:
        comp = metrics_df.groupby("model")["mae"].mean().sort_values()
        fig, ax = plt.subplots(figsize=(10, 5))
        comp.plot(kind="barh", ax=ax)
        ax.set_xlabel("Mean MAE (cycles, LOTO)")
        ax.set_title("Baseline vs ML comparison")
        _save(fig, fig_dir / "08_model_comparison.png")

    # Decision workflow schematic
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis("off")
    ax.text(0.05, 0.5, "Sensors → Features → RUL / uncertainty → Risk review\n(research demonstrator — not machine control)", fontsize=14)
    _save(fig, fig_dir / "11_decision_workflow.png")