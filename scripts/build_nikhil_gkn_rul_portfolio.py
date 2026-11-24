#!/usr/bin/env python
"""
Build a Sandvik-style EngD research evidence portfolio for GKN / MADE4Manufacturing
tool-life RUL theme. Metrics are read from results/; bio text matches the verified
Sandvik portfolio (Nikhil Hase, November 2026).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from word_layout import (  # noqa: E402
    Doc,
    S_BULLET,
    S_CAPTION,
    S_SUBTITLE,
    S_TITLE,
    n3,
)

OUT_DOCX = ROOT / "reports" / "Nikhil_Hase_Sheffield_EngD_GKN_Tool_Life_RUL_Research_Portfolio.docx"
OUT_PDF = ROOT / "reports" / "Nikhil_Hase_Sheffield_EngD_GKN_Tool_Life_RUL_Research_Portfolio.pdf"
FIG_DIR = ROOT / "results" / "figures" / "portfolio_embedded"
METRICS = ROOT / "results" / "tables" / "model_metrics.csv"
ROBUST = ROOT / "results" / "tables" / "robustness_missing_sensors.csv"
AUDIT = ROOT / "results" / "metrics" / "audit_summary.json"
PIPE = ROOT / "results" / "metrics" / "pipeline_summary.json"


def _fig_industry_months() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / "industry_domains.png"
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    labels = ["Manufacturing-facing\n(design, CAD/CAM)", "Software QA &\nAI evaluation"]
    months = [36, 53]
    ax.barh(labels, months, color=["#1f4e79", "#2ca8a8"])
    ax.set_xlabel("Months (to October 2026)")
    ax.set_xlim(0, 60)
    for i, m in enumerate(months):
        ax.text(m + 1, i, f"{m} mo", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _load_verified_metrics() -> dict:
    m = pd.read_csv(METRICS).drop_duplicates(subset=["tool", "model", "scenario"], keep="first")
    rf = m[m["model"] == "ml_random_forest"]
    xgb = m[m["model"] == "xgboost"]
    cyc = m[m["model"] == "baseline_cycle_only"]
    fixed = m[m["model"] == "baseline_fixed_lifetime"]
    assert len(rf) == 3 and len(cyc) == 3, "unexpected metrics shape"
    pipe = json.loads(PIPE.read_text(encoding="utf-8")) if PIPE.exists() else {}
    audit = json.loads(AUDIT.read_text(encoding="utf-8")) if AUDIT.exists() else {}
    rob = pd.read_csv(ROBUST) if ROBUST.exists() else pd.DataFrame()
    return {
        "rf_mae_by_tool": {r.tool: r.mae for r in rf.itertuples()},
        "rf_mae_mean": float(rf.mae.mean()),
        "xgb_mae_mean": float(xgb.mae.mean()) if len(xgb) else None,
        "cycle_mae_mean": float(cyc.mae.mean()),
        "fixed_mae_mean": float(fixed.mae.mean()),
        "threshold_300_cross": bool(pipe.get("any_threshold_crossing_300um", False)),
        "n_tools": int(pipe.get("n_tools", 3)),
        "audit_notes": audit.get("notes", []),
        "rob_c6_no_ae": float(rob[(rob.tool == "c6") & (rob.sensor_group == "no_ae")].mae.iloc[0])
        if len(rob) else None,
        "rob_c6_all": float(rob[(rob.tool == "c6") & (rob.sensor_group == "all")].mae.iloc[0])
        if len(rob) else None,
    }


def build() -> None:
    v = _load_verified_metrics()
    F = ROOT / "results" / "figures"
    industry_fig = _fig_industry_months()

    d = Doc()

    # ---- title block (Sandvik-style) ---------------------------------
    d.add("NIKHIL HASE | Research evidence portfolio", S_TITLE)
    d.add(
        "Supporting material for the University of Sheffield / GKN Aerospace EngD theme: "
        "Data-driven tool-life prediction for safer and more productive aerospace machining",
        S_SUBTITLE,
        space_after=6,
    )
    d.para(
        "Engineering foundations • Quantitative modelling • AI evaluation • Prognostic experimentation",
        align=1,
        size=10,
        color=(89, 89, 89),
    )
    d.h2("How to read this portfolio")
    d.para(
        "Completed work (sections 01 to 03 and 03A) is kept separate from the proposed doctoral "
        "approach (sections 04 and 07). Self-assessments are labelled as such. This document does "
        "not claim in-plant aerospace titanium trials, shop-floor tool replacement authority, or "
        "GKN sponsorship of the independent PHM2010 preparation work.",
        size=10,
    )
    d.h2("Research readiness at a glance")
    d.figure(industry_fig, "Industry experience by domain (months to October 2026).", width_cm=14)
    d.para("What this shows", lead="")
    d.bullet(
        "About 3 of my 7.5 years in industry were manufacturing-facing (design and CAD application "
        "engineering); about 4.4 years were software quality and AI evaluation."
    )
    d.bullet(
        "The profile is a manufacturing engineer who moved into data validation, not a machining-science "
        "or tool-wear specialist."
    )
    d.bullet(
        "Academic record: B.E. Mechanical Engineering 64% (Pune University, 2017); PG Diploma, Tool "
        "Design and CAD/CAM 81% (IGTR, 2019); Executive MBA, Data Analytics (SIBM Pune, expected 2027)."
    )

    # ---- 01 FDM (verified — same as Sandvik portfolio) -----------------
    d.h1("01 Manufacturing experimentation | FDM polymer study", page_break=True)
    d.para(
        "Examined how FDM process settings, including layer height and infill, relate to mechanical "
        "response for ULTEM 9085, ULTEM 1000 and POM-C specimens, using ASTM D638 Type V tensile "
        "testing and comparison with injection-moulded material response.",
    )
    d.table(
        "FDM study structure",
        ["Inputs", "Method", "Output and interpretation"],
        [
            [
                "Material; layer height; infill percentage",
                "Prepare specimens; tensile test to ASTM D638 Type V; compare with injection-moulded response",
                "Process-property relationships and manufacturing variability",
            ]
        ],
        [4.0, 6.5, 6.5],
        [0, 0, 0],
    )
    d.para(
        "Transfer to the EngD: reasoning from process parameters to physical measurements, relevant "
        "to linking cutting conditions and tool state with sensor histories. FDM is not equivalent "
        "to metal cutting, and the work involved no in-process sensing.",
        italic=True,
        color=(89, 89, 89),
    )

    # ---- 02 MBA -------------------------------------------------------
    d.h1("02 Quantitative modelling | SIBM Executive MBA")
    d.para(
        "Excel models built and solved during coursework using formulas, statistical analysis tools and "
        "Solver. These are applied classroom exercises on supplied datasets, not published research.",
    )
    d.table(
        "MBA modelling exercises",
        ["Method", "Documented exercises", "Research transfer"],
        [
            ["Regression", "Regression_Analysis workbook", "Interpretable baselines for degradation trends"],
            ["Forecasting", "Moving average, exponential smoothing, trend", "Wear progression and RUL horizons"],
            ["Simulation", "Probability distributions and sampling", "Uncertainty propagation for replacement risk"],
            ["Optimisation", "Linear and nonlinear programming cases", "Tool-replacement decisions under constraints"],
        ],
        [3.5, 5.0, 8.5],
        [0, 0, 0],
        note="Evidence available on request: original SIBM classroom spreadsheets.",
    )

    # ---- 03 Autodesk --------------------------------------------------
    d.h1("03 Industrial AI evaluation | Autodesk")
    d.para(
        "Evaluation of AI-enabled CAD-related image editing and engineering workflows, using structured "
        "benchmark cases and automated quality checks. Specific internal results are not reproduced here "
        "and would be shared only with employer approval.",
    )
    d.table(
        "Evaluation practice",
        ["Research-like activity", "Evidence of method", "Lesson for machining research"],
        [
            ["Define evaluation criteria", "Reference cases and scoring rubrics", "Wear/RUL ground truth must be explicit"],
            [
                "Compare independent measures",
                "LLM judgement alongside image-similarity metrics",
                "Single metrics can mislead; report disagreement",
            ],
            ["Automate repeatable tests", "Python/PyTest and CI validation", "Reproducible LOTO prognostic experiments"],
        ],
        [4.5, 5.5, 7.0],
        [0, 0, 0],
    )

    # ---- 03A RUL preparation (completed) --------------------------------
    d.h1("03A Independent preparation | PHM2010 tool-life RUL proof-of-concept")
    d.para(
        "Repository: cnc-tool-remaining-useful-life-prediction. Public PHM Society 2010 milling data "
        "(cutters c1, c4, c6) with leave-one-tool-out validation, baseline models, and a research-only "
        "Streamlit demonstrator. This is preparation work, not GKN production software.",
        links=[
            (
                "cnc-tool-remaining-useful-life-prediction",
                "file:///D:/AI/cnc-tool-remaining-useful-life-prediction",
            )
        ],
    )
    cross_txt = (
        "none of the three tools crossed a 300 µm flank-wear limit in available files"
        if not v["threshold_300_cross"]
        else "at least one tool crossed 300 µm"
    )
    d.para(
        f"Target audit finding: {cross_txt}; physical RUL at that threshold is therefore "
        "right-censored and must not be treated as observed failure. Sensor data use the Katulu "
        "UniWear PHM2010 bundle (CC BY 4.0) with official per-flute wear for c4 and c6.",
        lead="Key finding (verified from research_evidence_audit.md).",
    )
    rf_rows = [[t, n3(v["rf_mae_by_tool"][t])] for t in sorted(v["rf_mae_by_tool"])]
    d.table(
        "Random forest RUL MAE (cycles) by held-out tool, sensor features only",
        ["Held-out tool", "LOTO MAE"],
        rf_rows + [["Mean across tools", n3(v["rf_mae_mean"])]],
        [5.0, 12.0],
        [0, 1],
    )
    d.table(
        "Mean LOTO MAE (cycles) — selected models vs baselines (physical/censored RUL target)",
        ["Model", "Mean MAE", "Interpretation"],
        [
            ["baseline_cycle_only", n3(v["cycle_mae_mean"]), "Uses cut index only; strong when target ≈ remaining recorded cuts"],
            ["baseline_fixed_lifetime", n3(v["fixed_mae_mean"]), "Training-tool lifetime prior"],
            ["ml_random_forest", n3(v["rf_mae_mean"]), "Best ML mean MAE in this run; does not beat cycle-only on average"],
        ],
        [5.5, 3.5, 8.0],
        [0, 1, 0],
    )
    if v["rob_c6_all"] is not None:
        d.para(
            f"Missing-sensor check (c6, random forest): all sensors MAE {n3(v['rob_c6_all'])} cycles; "
            f"without acoustic emission MAE {n3(v['rob_c6_no_ae'])} cycles — illustrative only.",
            size=10,
        )
    d.figure(F / "01_wear_trajectories.png", "Measured / aligned wear histories and 300 µm reference.", 14)
    d.figure(F / "08_model_comparison.png", "Baseline vs machine-learning mean LOTO MAE.", 14)

    # ---- 04 proposed approach -----------------------------------------
    d.h1("04 Research translation | proposed EngD approach", page_break=True)
    d.para(
        "Proposed work, not work already performed. Figures below include experimental outputs "
        "(03A) and schematics of the doctoral validation design.",
        italic=True,
        color=(89, 89, 89),
    )
    d.para(
        "A central methodological point is how prognostic models are validated. Cuts from the same "
        "tool share insert, set-up and workpiece context, so random row splits leak information. "
        "I would use leave-one-tool-out and prospective cut-by-cut prediction, with simple "
        "remaining-cut and fixed-life baselines reported separately from sensor-rich models.",
        lead="Validation principle.",
    )
    d.figure(F / "03_rul_target_construction.png", "RUL target construction with right censoring (example tool c6).", 14)
    d.figure(F / "11_decision_workflow.png", "Conceptual risk-based decision-support workflow (research demonstrator only).", 14)

    # ---- 05 evidence matrix -------------------------------------------
    d.h1("05 Evidence against the EngD theme aims")
    d.para(
        "The advertised GKN / MADE4Manufacturing theme emphasises data-driven tool-life prediction "
        "and safer productivity. Ratings are self-assessment: Strong = direct relevant experience; "
        "Partial = transferable; To develop = specialist gap.",
        size=10,
    )
    d.table(
        "Readiness matrix (self-assessed)",
        ["Theme aim", "Manufacturing", "Modelling", "Validation practice", "Prognostics / wear science"],
        [
            ["Sensor-based tool-life / RUL estimation", "Partial", "Partial", "Strong", "To develop"],
            ["Risk-based replacement decisions", "Partial", "Strong", "Strong", "To develop"],
            ["Grouped validation on unseen tools", "Partial", "Partial", "Strong", "Partial"],
            ["Aerospace material / process trials", "Partial", "Partial", "Partial", "To develop"],
            ["Uncertainty-aware recommendations", "Partial", "Partial", "Strong", "Partial"],
        ],
        [5.5, 2.5, 2.5, 3.5, 3.0],
        [0, 1, 1, 1, 1],
    )
    d.figure(F / "02_threshold_audit.png", "Wear threshold audit: no 300 µm crossing in available PHM files.", 12)

    # ---- 06 literature ------------------------------------------------
    d.h1("06 Existing research | selected literature (milling prognostics)")
    d.table(
        "Literature mapping",
        ["Study", "What it establishes", "Boundary and opportunity"],
        [
            [
                "PHM Society (2010) milling challenge",
                "Benchmark force, vibration and AE histories with measured flank wear for six cutters",
                "Stainless steel, few tools; challenge scored RUL prediction — threshold definition matters",
            ],
            [
                "Colantonio et al. (2021) AI tool-wear review",
                "Force is the dominant turning input; few studies predict future wear state",
                "Milling benchmarks rare; need held-out tools and future-state targets",
            ],
            [
                "Li et al. (2022) physics-informed meta-learning",
                "Hybrid wear models can help under changing wear rates",
                "Milling-focused; test transfer to aerospace processes with explicit uncertainty",
            ],
            [
                "Xu et al. (2018) MS-CGRU tool wear",
                "Deep models on PHM2010 sensor series for wear / RUL",
                "Only three training tools; compare honestly to cycle-only baselines",
            ],
        ],
        [3.2, 5.0, 8.8],
        [0, 0, 0],
    )

    # ---- 07 proposed contribution -------------------------------------
    d.h1("07 Proposed research contribution | testable approach")
    d.para(
        "H1: sensor histories improve held-out-tool RUL or wear-horizon estimates over cycle-only "
        "baselines when physical wear limits are documented. H2: uncertainty intervals flag when "
        "predictions are unsafe for operations. Both require sponsor data; null results are informative.",
    )
    d.table(
        "Work packages",
        ["Work package", "Method", "Success criterion"],
        [
            [
                "WP1 Data integrity",
                "Audit wear labels, timestamps, stopping rules; MSA on flank wear",
                "Traceable RUL definition with censoring documented",
            ],
            [
                "WP2 Baselines and prognostics",
                "Fixed life, degradation extrapolation, ridge/ensemble models; LOTO; missing-sensor tests",
                "Reported gain over baselines without leakage",
            ],
            [
                "WP3 Risk-based decision support",
                "Interval calibration, asymmetric cost discussion with operations",
                "Demonstrator aligned to engineering approval, not autonomous control",
            ],
            [
                "WP4 Aerospace validation",
                "Targeted trials on sponsor material, tools, conditions",
                "External validation beyond public benchmark",
            ],
        ],
        [3.5, 8.0, 5.5],
        [0, 0, 0],
    )
    d.table(
        "Risks and mitigations",
        ["Risk", "Likelihood", "Impact", "Mitigation"],
        [
            ["Ambiguous wear endpoint / censoring", "High", "High", "Threshold sensitivity analysis; separate recorded-horizon target"],
            ["Too few independent tools", "High", "High", "Sponsor trials; report learning curves and uncertainty"],
            ["Missing or biased sensors", "Medium", "Medium", "Robustness experiments; fallback sensor groups"],
            ["Benchmark ≠ aerospace process", "High", "High", "Do not claim transfer without measured trials"],
        ],
        [5.0, 2.5, 2.0, 7.5],
        [0, 1, 1, 0],
    )
    d.h2("Research ethics and engineering assurance")
    d.para(
        "Prognostic outputs should inform inspection and replacement planning, not autonomously override "
        "approved limits. Any change to tool-replacement practice would require measured wear evidence, "
        "validation on representative batches, and sign-off by GKN engineering and quality functions.",
    )

    # ---- 08 references ------------------------------------------------
    d.h1("08 References (APA 7th edition)")
    refs = [
        "Colantonio, L., Equeter, L., Dehombreux, P., & Ducobu, F. (2021). A systematic literature review "
        "of cutting tool wear monitoring in turning by using artificial intelligence techniques. Machines, 9(12), Article 351. "
        "https://doi.org/10.3390/machines9120351",
        "Li, Y., Wang, J., Huang, Z., & Gao, R. X. (2022). Physics-informed meta learning for machining tool wear prediction. "
        "Journal of Manufacturing Systems, 62, 17–27. https://doi.org/10.1016/j.jmsy.2021.10.013",
        "PHM Society. (2010). 2010 PHM Society Conference Data Challenge. "
        "https://phmsociety.org/phm_competition/2010-phm-society-conference-data-challenge/",
        "Xu, W., Miao, H., Zhao, Z., Liu, J., Sun, C., & Yan, R. (2018). Multi-scale convolutional gated recurrent "
        "unit networks for tool wear prediction in smart manufacturing. Advanced Engineering Informatics, 38, 652–664. "
        "https://doi.org/10.1016/j.advei.2018.11.006",
    ]
    for r in refs:
        d.para(r, size=10, space_after=3)

    d.para(
        "Supporting material: engineering portfolio https://nhase13.wixsite.com/portfolio. "
        "Supporting evidence on request: SIBM workbooks, FDM materials, academic transcripts, "
        "RUL repository results and audit files.",
        size=10,
        links=[("https://nhase13.wixsite.com/portfolio", "https://nhase13.wixsite.com/portfolio")],
    )
    d.para(
        "Note: These are my own ideas for discussion and do not represent agreed GKN project methods. Nikhil Hase.",
        italic=True,
        size=10,
    )

    pages = d.finish(
        "Nikhil Hase — GKN Tool Life RUL Research Portfolio",
        OUT_DOCX,
        OUT_PDF,
    )
    print(f"Wrote {OUT_DOCX} ({pages} pages)")
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()