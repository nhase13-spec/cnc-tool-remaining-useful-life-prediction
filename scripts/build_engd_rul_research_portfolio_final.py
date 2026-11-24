#!/usr/bin/env python
"""
Full EngD research portfolio (Machining ML Final style) for GKN tool-life / RUL work.
Reuses the Word COM Doc class from the surface-roughness / sensor monitoring portfolio.
Metrics: results/tables/*.csv only.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DOCX = ROOT / "reports" / "EngD_Tool_Life_RUL_Research_Portfolio_Final.docx"
OUT_PDF = ROOT / "reports" / "EngD_Tool_Life_RUL_Research_Portfolio_Final.pdf"
DL = Path(r"C:\Users\hasen\Downloads")

_PB = Path(
    r"D:\AI\Sensor-Based Tool Wear Prediction and Machining Quality Monitoring"
    r"\Model\scripts\build_engd_portfolio_docx.py"
)
spec = importlib.util.spec_from_file_location("portfolio_builder", _PB)
pb = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(pb)

S_TITLE = pb.S_TITLE
S_SUBTITLE = pb.S_SUBTITLE
S_NORMAL = pb.S_NORMAL
n3 = pb.n3


class Doc(pb.Doc):
    def finish(self, title: str, out_docx: Path, out_pdf: Path) -> int:
        out_docx.parent.mkdir(parents=True, exist_ok=True)
        last = self.doc.Paragraphs.Last.Range
        if last.Text.strip() == "":
            last.Style = self.doc.Styles(pb.S_NORMAL)
            last.ListFormat.RemoveNumbers()
        self.doc.Content.LanguageID = 2057
        pages = self.doc.ComputeStatistics(2)
        self.doc.SaveAs2(str(out_docx), FileFormat=16)
        try:
            self.doc.ExportAsFixedFormat(
                OutputFileName=str(out_pdf),
                ExportFormat=17,
                OpenAfterExport=False,
                OptimizeFor=0,
                CreateBookmarks=1,
            )
        except Exception:
            self.doc.SaveAs2(str(out_pdf), FileFormat=17)
        self.doc.Close(False)
        self.word.Quit()
        return pages


def _metrics():
    m = pd.read_csv(ROOT / "results/tables/model_metrics.csv")
    m = m.drop_duplicates(subset=["tool", "model", "scenario"], keep="first")
    pipe = json.loads((ROOT / "results/metrics/pipeline_summary.json").read_text(encoding="utf-8"))
    rob = pd.read_csv(ROOT / "results/tables/robustness_missing_sensors.csv")
    def mean_mae(model: str) -> float:
        return float(m[m.model == model].mae.mean())
    rf = m[m.model == "ml_random_forest"]
    return {
        "pipe": pipe,
        "rf_by_tool": {r.tool: (n3(r.mae), n3(r.rmse)) for r in rf.itertuples()},
        "rf_mean_mae": mean_mae("ml_random_forest"),
        "xgb_mean_mae": mean_mae("ml_xgboost"),
        "ridge_mean_mae": mean_mae("ml_ridge"),
        "gp_mean_mae": mean_mae("ml_gaussian_process"),
        "cycle_mae": mean_mae("baseline_cycle_only"),
        "fixed_mae": mean_mae("baseline_fixed_lifetime"),
        "linear_mae": mean_mae("baseline_linear_wear"),
        "rob": rob,
        "models_ranked": [
            ("baseline_cycle_only", mean_mae("baseline_cycle_only")),
            ("baseline_fixed_lifetime", mean_mae("baseline_fixed_lifetime")),
            ("ml_random_forest", mean_mae("ml_random_forest")),
            ("ml_xgboost", mean_mae("ml_xgboost")),
            ("ml_ridge", mean_mae("ml_ridge")),
            ("ml_gaussian_process", mean_mae("ml_gaussian_process")),
            ("baseline_linear_wear", mean_mae("baseline_linear_wear")),
        ],
    }


def build() -> None:
    v = _metrics()
    F = ROOT / "results" / "figures"
    d = Doc()

    d.add("Data-Driven Cutting Tool Remaining Useful Life Prediction", S_TITLE)
    d.add(
        "Sensor-Based Prognostics, Leakage-Aware Validation, and Risk-Based Decision Support",
        S_SUBTITLE,
    )
    d.add(
        "An Independent Machine Learning Research Portfolio Supporting the University of Sheffield "
        "/ GKN Aerospace EngD Theme (MADE4Manufacturing)",
        S_NORMAL,
        italic=True,
        space_after=8,
    )
    d.para(
        "B.E. Mechanical Engineering (Pune University, 2017); Postgraduate Diploma in Tool Design "
        "and CAD/CAM (IGTR Aurangabad, 2019); Executive MBA in Data Analytics (SIBM Pune, "
        "expected 2027); experience in manufacturing and CAD/CAM, engineering software validation "
        "and AI-enabled engineering workflow evaluation. Only public datasets and open "
        "repositories are used; no employer-confidential information is included.",
        lead="Author background (self-reported).",
        size=10,
    )
    d.para(
        "Repository cnc-tool-remaining-useful-life-prediction (PHM2010 cutters c1, c4, c6). "
        "Related preparatory work: surface-roughness-machine-learning-model and "
        "cnc_sensor_quality_monitoring (separate portfolios). Results verified from saved metric "
        "files and test runs in November 2026.",
        lead="Source repositories.",
        size=10,
        links=[
            (
                "cnc-tool-remaining-useful-life-prediction",
                "file:///D:/AI/cnc-tool-remaining-useful-life-prediction",
            ),
        ],
    )

    plain = [
        (
            "What did we investigate?",
            "Whether historical force, vibration and acoustic-emission summaries from the PHM "
            "Society 2010 milling challenge support remaining useful life (RUL) estimation for "
            "cutters c1, c4 and c6, using leave-one-tool-out validation and explicit wear-limit "
            "audits. The work is an independent proof-of-concept, not a GKN production system.",
        ),
        (
            "What did we discover?",
            "At a 300 µm flank-wear reference no tool crossed the limit in available wear files, "
            "so physical RUL at that threshold is right-censored and largely tracks remaining "
            "recorded experimental cuts. A cycle-only baseline (mean MAE about "
            f"{v['cycle_mae']} cuts) was competitive with random forest (mean MAE about "
            f"{v['rf_mean_mae']} cuts). Linear wear extrapolation performed poorly. Missing-sensor "
            "tests on cutter c6 showed acoustic-emission dropout did not degrade MAE in this run.",
        ),
        (
            "What does it mean for manufacturing?",
            "The benchmark has only three independent tool histories and stainless-steel conditions; "
            "it does not validate aerospace titanium processes. Honest baselines and censoring "
            "disclosure are necessary before any tool-replacement decision support. The study "
            "documents methodology and negative or mixed prognostic outcomes rather than "
            "deployment readiness or cost savings.",
        ),
    ]
    d.h1("Plain-Language Summary")
    for head, text in plain:
        d.para(text, lead=head)

    glossary = [
        ("RUL (remaining useful life)", "remaining cutting cycles until a defined wear limit is reached, "
         "or until the experimental record ends if the limit is never crossed (right censoring)."),
        ("Flank wear (VB)", "wear land on the tool flank, measured in micrometres in PHM2010 files."),
        ("Cut / wear step", "one indexed machining pass after which wear was measured or assigned."),
        ("LOTO", "leave-one-tool-out: train on two cutters, test prospectively on the held-out cutter."),
        ("Censoring", "the wear limit was not observed before the experiment stopped; RUL is bounded by "
         "remaining recorded cuts, not proven physical failure."),
        ("MAE", "mean absolute error in predicted versus reference RUL, in cutting cycles."),
        ("Baseline_cycle_only", "predicts remaining cuts from training median length without sensor inputs."),
        ("Data leakage", "using future wear, final tool lifetime or test-set statistics during training."),
        ("Proxy target", "remaining recorded experimental cycles mistaken for true physical RUL."),
    ]
    d.h1("Glossary")
    for term, meaning in glossary:
        d.bullet(meaning, lead=term + ":")

    d.h1("1  Technical Research Summary")
    d.h2("1.1  Industrial research problem")
    d.para(
        "Aerospace machining depends on timely tool replacement: too early wastes carbide and machine "
        "time; too late risks surface integrity, vibration and unplanned stoppages. Condition-based "
        "prognostics from in-process sensors could support safer scheduling, but only when wear "
        "labels, stopping rules and validation units (tools, batches, materials) are traceable. "
        "GKN’s EngD theme asks for data-driven tool-life prediction; this portfolio uses the public "
        "PHM2010 benchmark (stainless steel, 6 mm ball-nose carbide) as methodology preparation, "
        "not as evidence on titanium aerospace parts."
    )
    d.h2("1.2  Research objective")
    d.para(
        "Construct defensible RUL targets from documented wear measurements; extract causal per-cut "
        "sensor features; compare baselines and regression models under leave-one-tool-out validation; "
        "test missing-sensor robustness; and provide a research-only decision demonstrator."
    )
    d.h2("1.3  Key findings (verified from saved pipeline outputs)")
    for tool, (mae, rmse) in v["rf_by_tool"].items():
        d.bullet(
            f"Random forest LOTO MAE {mae} cycles, RMSE {rmse} cycles (held-out {tool}).",
            lead=f"Tool {tool}.",
        )
    d.bullet(
        f"Cycle-only baseline mean MAE {n3(v['cycle_mae'])} cycles; fixed-lifetime baseline "
        f"{n3(v['fixed_mae'])}; linear wear extrapolation {n3(v['linear_mae'])}.",
        lead="Baselines.",
    )
    d.bullet(
        "No tool crossed 300 µm in audited wear files; at 200 µm, c4 and c6 crossed late in the "
        "experiment while c1 did not.",
        lead="Wear threshold audit.",
    )
    d.bullet(
        "UniWear bundle segment counts (255/260/290) differ from 315 official wear rows for c4/c6; "
        "c1 wear uses bundle-derived labels where official per-flute CSV was unavailable.",
        lead="Data alignment.",
    )
    d.para(
        "These are mixed results: sensors did not clearly dominate cycle-only prediction under the "
        "censored 300 µm target. They demonstrate audit-first RUL construction and small-sample "
        "limits; they are not evidence of shop-floor deployment.",
        lead="Interpretation.",
    )
    d.h2("1.4  Research relevance")
    d.para(
        "The project extends prior machining ML portfolios (roughness and wax-milling classification) "
        "into prognostic regression with explicit right censoring. Together they form an evidence "
        "chain: schema audit, grouped validation, baseline discipline and limitation statements "
        "needed before sponsor-scale trials."
    )

    d.h1("2  Business Problem and Research Questions")
    d.h2("2.1  Manufacturing challenge")
    d.para("Tool-life uncertainty affects:", keep_next=True)
    d.bullet("unplanned downtime and lost aerospace production capacity;")
    d.bullet("premature carbide disposal and tungsten supply-chain pressure;")
    d.bullet("scrap, rework and downstream inspection load;")
    d.bullet("safety risk if wear limits are exceeded before detection.")
    d.para("No financial or carbon savings are quantified here.")
    d.h2("2.2  Stakeholders")
    d.bullet("schedules replacement and interprets wear evidence.", lead="Manufacturing engineer:")
    d.bullet("defines wear limits and approves process changes.", lead="Manufacturing authority:")
    d.bullet("evaluates model evidence and validation design.", lead="Research engineer:")
    d.para(
        "Outputs are decision-support for inspection and review, not autonomous machine control."
    )
    d.h2("2.3  Research questions")
    for lab, q in [
        ("RQ1", "Can historical sensor measurements estimate remaining useful cutting-tool life?"),
        ("RQ2", "Do sensor models outperform fixed-life and degradation baselines?"),
        ("RQ3", "How does prediction quality change across early, middle and late tool life?"),
        ("RQ4", "How reliable are predictions when sensor channels are absent?"),
        ("RQ5", "Can models generalise to unseen tools under LOTO?"),
        ("RQ6", "Can uncertainty-aware outputs support safer replacement recommendations?"),
        ("RQ7", "What evidence is required for transfer across materials and conditions?"),
    ]:
        d.para(q, lead=lab + ":", space_after=2)

    d.h1("3  PHM2010 Tool-Life RUL Study")
    d.h2("3.1  Dataset and target construction")
    d.para(
        "PHM Society 2010 milling challenge: cutters c1, c4, c6 (training), high-speed dry milling, "
        "seven channels (three forces, three vibrations, AE-RMS). Wear in 10⁻³ mm. Secondary NASA "
        "milling zip was not valid locally. Primary signals use Katulu UniWear PHM2010 bundle "
        "(CC BY 4.0) with official flute wear CSV for c4 and c6."
    )
    d.para("Data limitations:", keep_next=True)
    d.bullet("three independent tools only;")
    d.bullet("stainless benchmark ≠ aerospace titanium;")
    d.bullet("bundle downsampling yields fewer wear steps than 315 official cuts;")
    d.bullet("300 µm ISO-style limit never crossed — physical failure not observed.")
    if (F / "01_wear_trajectories.png").is_file():
        d.figure(F / "01_wear_trajectories.png", "Wear trajectories and 300 µm reference.", 15.5)
    if (F / "02_threshold_audit.png").is_file():
        d.figure(F / "02_threshold_audit.png", "Maximum wear versus threshold audit.", 12)

    d.h2("3.2  Validation design")
    d.para(
        "Leave-one-tool-out; each prediction uses only data available up to the current cut; "
        "preprocessing fit on training tools only. Life-stage stratification for reporting is "
        "retrospective and labelled as such."
    )
    if (F / "03_rul_target_construction.png").is_file():
        d.figure(F / "03_rul_target_construction.png", "RUL target under right censoring (example c6).", 14)

    d.h2("3.3  Models and baselines")
    d.para(
        "Baselines: fixed training lifetime, cycle-only remaining cuts, linear wear extrapolation. "
        "Models: Ridge, random forest, XGBoost, Gaussian process on per-cut sensor statistics and "
        "causal wear-history features."
    )

    d.h2("3.4  Results")
    rows = []
    for name, mae in sorted(v["models_ranked"], key=lambda x: x[1]):
        rows.append([name.replace("ml_", ""), n3(mae), "LOTO", "censored RUL @ 300 µm"])
    d.table(
        "Mean LOTO MAE (cutting cycles) by model",
        ["Model", "Mean MAE", "Validation", "Target"],
        rows,
        [5.0, 2.5, 3.5, 6.0],
        [0, 1, 1, 0],
        note="Lower is better. Cycle-only baseline uses no sensor columns.",
    )
    tool_rows = [[t, v["rf_by_tool"][t][0], v["rf_by_tool"][t][1]] for t in sorted(v["rf_by_tool"])]
    d.table(
        "Random forest — held-out tool MAE / RMSE (cycles)",
        ["Held-out tool", "MAE", "RMSE"],
        tool_rows,
        [4.0, 4.0, 9.0],
        [0, 1, 1],
    )
    if (F / "04_pred_vs_observed.png").is_file():
        d.figure(F / "04_pred_vs_observed.png", "Predicted versus observed RUL (selected model).", 11)
    if (F / "08_model_comparison.png").is_file():
        d.figure(F / "08_model_comparison.png", "Mean LOTO MAE by model.", 14)

    d.h2("3.5  Prediction stage and error structure")
    if (F / "07_life_stage_errors.png").is_file():
        d.figure(
            F / "07_life_stage_errors.png",
            "Absolute error by retrospective life stage (early / middle / late).",
            15,
        )
    d.para(
        "Early-cycle predictions face greater remaining-life uncertainty; late-cycle errors matter "
        "for replacement timing because overestimating RUL increases failure risk. Asymmetric "
        "interpretation: positive bias (overprediction) is often more hazardous than early replacement.",
    )

    d.h2("3.6  Threshold sensitivity")
    sens = pd.read_csv(ROOT / "results/tables/threshold_sensitivity.csv")
    srows = []
    for _, r in sens.iterrows():
        cross = "yes" if r.crossed else "no (censored)"
        srows.append(
            [r.tool, n3(r.threshold_um), cross, "" if pd.isna(r.crossing_cut) else str(int(r.crossing_cut))]
        )
    d.table(
        "Flank-wear threshold crossing audit",
        ["Tool", "Threshold (µm)", "Crossed", "First crossing cut"],
        srows[:12],
        [2.0, 3.0, 4.0, 8.0],
        [0, 1, 1, 1],
        note="No crossing at 300 µm. At 200 µm only c4 and c6 cross, late in the experiment.",
    )

    d.h2("3.7  Missing-sensor robustness (random forest)")
    rob = v["rob"]
    rrows = []
    for grp in ["all", "no_force", "no_vibration", "no_ae", "process_only"]:
        sub = rob[rob.sensor_group == grp]
        if sub.empty:
            continue
        rrows.append([grp, n3(sub.mae.mean()), str(len(sub))])
    d.table(
        "Mean MAE by sensor group",
        ["Sensor group", "Mean MAE", "n folds"],
        rrows,
        [5.0, 3.5, 8.5],
        [0, 1, 1],
    )

    d.h2("3.8  Two-stage prognostic framework (research design)")
    d.para(
        "Approach A maps sensor histories directly to RUL. Approach B forecasts wear then estimates "
        "threshold-crossing time. Indirect approaches require out-of-fold wear predictions when wear "
        "estimates feed a second-stage model. Both were scoped; Approach A was implemented fully in "
        "the proof-of-concept pipeline; Approach B is planned for doctoral work with full per-cut CSV "
        "and calibrated metrology."
    )

    d.h2("3.9  Decision-support demonstrator")
    d.para(
        "Streamlit dashboard (dashboard/app.py) shows wear trajectory, RUL estimate, illustrative "
        "risk thresholds and replacement categories. It does not interface with machine control."
    )
    if (F / "11_decision_workflow.png").is_file():
        d.figure(F / "11_decision_workflow.png", "Conceptual workflow (research only).", 15)

    d.h1("4  Comparative Findings and Relation to Prior Portfolios")
    d.para(
        "The Rolls-Royce-oriented machining quality portfolio (EngD_Machining_ML_Research_Portfolio_Final) "
        "documented that grouped validation and simple baselines often reverse apparent ML gains on "
        "small public datasets. This RUL study applies the same discipline to regression: with only "
        "three tools and censored 300 µm targets, cycle index carries most of the predictable "
        "variance. Sensor models can improve held-out tool c6 (random forest MAE about "
        f"{v['rf_by_tool']['c6'][0]} cycles) but not uniformly across tools."
    )
    d.table(
        "Question-level status (self-assessed from current evidence)",
        ["Research question", "Status", "Comment"],
        [
            ["RQ1 Sensor-based RUL", "Partial", "RUL defined; sensors alone not decisive on average"],
            ["RQ2 vs baselines", "Partial", "Cycle-only competitive under censoring"],
            ["RQ3 Life stage", "Explored", "Stage stratification in figures; small n"],
            ["RQ4 Missing sensors", "Partial", "Group dropout tested; not all failure modes"],
            ["RQ5 Unseen tools", "Explored", "LOTO executed on three tools"],
            ["RQ6 Uncertainty", "To develop", "Intervals not stable at n=3"],
            ["RQ7 Transfer", "To develop", "Aerospace trials not run"],
        ],
        [2.0, 2.5, 12.5],
        [0, 1, 0],
    )

    d.h1("5  MBA and Sustainability Considerations (Illustrative)")
    d.para(
        "Fixed-interval versus condition-based replacement trades inventory and labour against failure "
        "risk. Illustrative KPIs: tool utilisation %, premature changes, missed wear crossings, false "
        "alarms, unplanned downtime. Scenario costs are not estimated from this benchmark."
    )

    d.h2("5.1  Illustrative KPIs (no measured costs)")
    d.table(
        "Operational KPIs for future sponsor pilots",
        ["KPI", "Definition", "Data needed"],
        [
            ["Tool utilisation %", "Cutting time / purchased tool life", "MES + tool log"],
            ["Premature changes", "Replacements before wear limit", "Wear metrology"],
            ["Missed crossings", "Cuts after limit without planned change", "QC records"],
            ["False alarms", "Predicted failure without measured wear", "Labeled events"],
            ["Unplanned downtime", "Stops attributed to tool failure", "Maintenance log"],
        ],
        [4.0, 5.5, 7.5],
        [0, 0, 0],
    )

    d.h1("6  Research Lessons and Implications for the GKN EngD")
    d.bullet("Audit wear endpoints before modelling; do not treat last cut as failure.")
    d.bullet("Report cycle-only and fixed-life baselines alongside sensor models.")
    d.bullet("Use grouped validation by tool; report censoring and threshold sensitivity.")
    d.bullet("Plan sponsor trials for titanium, approved wear metrology and more independent units.")
    d.para(
        "Independent preparation does not imply GKN sponsorship. Doctoral work should integrate "
        "shop-floor data governance and engineering sign-off."
    )

    d.h2("6.1  Limitations and gaps")
    d.bullet("NASA secondary dataset unavailable locally (invalid archive).")
    d.bullet("No SHAP / full quantile-coverage study at three tools.")
    d.bullet("No aerospace material or GKN confidential data.")
    d.bullet("Bundle sensor data differ from raw 50 kHz PHM CSV.")
    d.bullet("Doctoral programme requires sponsor trials and approved wear measurement.")

    d.h2("6.2  Proposed doctoral roadmap (outline)")
    d.table(
        "Illustrative four-year focus",
        ["Year", "Focus", "Deliverable"],
        [
            ["1", "Data governance + trials design", "Wear MSA, timestamp audit"],
            ["2", "Baselines + physics-informed wear", "Grouped validation on sponsor data"],
            ["3", "Uncertainty + decision support", "Calibrated intervals, HIL review"],
            ["4", "Transfer + thesis", "Material/condition sensitivity report"],
        ],
        [2.0, 6.0, 9.0],
        [0, 0, 0],
        note="Timings indicative only; subject to supervision and facility access.",
    )

    d.h1("7  Verification Status and References")
    d.para("Verification:", lead="")
    d.bullet("pytest: leakage, censoring, temporal ordering tests passed in repo tests/.")
    d.bullet("research_evidence_audit.md generated from audit CLI.")
    d.bullet("Figures reproduced from results/figures/ pipeline run.")
    refs = [
        "PHM Society. (2010). 2010 PHM Society Conference Data Challenge. "
        "https://phmsociety.org/phm_competition/2010-phm-society-conference-data-challenge/",
        "Li, Y., Wang, J., Huang, Z., & Gao, R. X. (2022). Physics-informed meta learning for machining "
        "tool wear prediction. Journal of Manufacturing Systems, 62, 17–27.",
        "Colantonio, L., Equeter, L., Dehombreux, P., & Ducobu, F. (2021). A systematic literature review "
        "of cutting tool wear monitoring. Machines, 9(12), Article 351.",
        "Xu, W., Miao, H., Zhao, Z., Liu, J., Sun, C., & Yan, R. (2018). MS-CGRU networks for tool wear "
        "prediction. Advanced Engineering Informatics, 38, 652–664.",
    ]
    for r in refs:
        d.para(r, size=10, space_after=3)

    pages = d.finish(
        "EngD Tool Life RUL Research Portfolio",
        OUT_DOCX,
        OUT_PDF,
    )
    if DL.is_dir():
        import shutil

        shutil.copy2(OUT_DOCX, DL / OUT_DOCX.name)
        shutil.copy2(OUT_PDF, DL / OUT_PDF.name)
    print(f"Wrote {OUT_DOCX} ({pages} pages)")
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    build()