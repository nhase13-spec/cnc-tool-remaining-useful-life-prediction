#!/usr/bin/env python
"""Generate DOCX research report and EngD portfolio (PDF via Word if available)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from docx import Document
from docx.shared import Pt

REPORTS = ROOT / "reports"
METRICS = ROOT / "results" / "metrics" / "pipeline_summary.json"
TABLES = ROOT / "results" / "tables"


def _load_summary() -> dict:
    if METRICS.exists():
        return json.loads(METRICS.read_text(encoding="utf-8"))
    return {}


def _add_heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def _metrics_snapshot() -> str:
    import csv
    from collections import defaultdict

    path = TABLES / "model_metrics.csv"
    if not path.exists():
        return "No metrics file."
    sums: dict[str, list[float]] = defaultdict(list)
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sums[row["model"]].append(float(row["mae"]))
    ranked = sorted(((k, sum(v) / len(v)) for k, v in sums.items()), key=lambda x: x[1])
    return "\n".join(f"{k}: mean MAE={mae:.2f} cycles" for k, mae in ranked[:12])


def build_main_report() -> Path:
    summary = _load_summary()
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    _add_heading(doc, "Data-Driven Cutting Tool Remaining Useful Life Prediction and Risk-Based Manufacturing Decision Support")
    doc.add_paragraph("Independent research proof-of-concept aligned with University of Sheffield MADE4Manufacturing EngD themes. "
                      "Not GKN-sponsored production software.")

    sections = [
        ("Plain-language summary", (
            "This study tests whether PHM2010 milling sensor histories support remaining useful life (RUL) "
            "estimation for cutters c1, c4, and c6 using leave-one-tool-out validation. "
            "Official wear files show no 300 µm threshold crossing; conclusions emphasise right-censored "
            "physical RUL and recorded-horizon baselines."
        )),
        ("Dataset and target construction", (
            f"Primary sensors: UniWear PHM bundle (CC BY 4.0) with per-flute wear for c4/c6. "
            f"Threshold audit: any crossing at 300 µm = {summary.get('any_threshold_crossing_300um', 'see audit')}."
        )),
        ("Model evaluation", _metrics_snapshot()),
        ("Limitations", (
            "Three independent tool histories; bundle cut segmentation < 315 official cuts; "
            "aerospace titanium transfer not evaluated; demonstrator is not machine control."
        )),
        ("Relevance to GKN EngD", (
            "Motivates data-driven tool-life and risk-aware replacement research for aerospace machining productivity "
            "without claiming sponsor validation on this public stainless-steel benchmark."
        )),
        ("Reproduction and public repository", (
            "Version-controlled source: https://github.com/nhase13-spec/cnc-tool-remaining-useful-life-prediction "
            "(branch main; pipeline code, tests, wear labels committed; generated results and large data gitignored). "
            "Clone, install requirements.txt, run scripts/fetch_phm_bundle.py then scripts/run_all.py per "
            "reports/REPRODUCTION.md."
        )),
    ]
    for title, body in sections:
        _add_heading(doc, title, 2)
        doc.add_paragraph(body)

    if (TABLES / "model_metrics.csv").exists():
        _add_heading(doc, "Metric snapshot", 2)
        doc.add_paragraph((TABLES / "model_metrics.csv").read_text(encoding="utf-8")[:2000])

    out = REPORTS / "GKN_Tool_Life_Research_Report.docx"
    REPORTS.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    return out


def build_portfolio() -> Path:
    doc = Document()
    _add_heading(doc, "GKN EngD Research Portfolio (Draft)")
    doc.add_paragraph(
        "Replace bracketed sections with your verified education and employment history before submission."
    )
    for heading, text in [
        ("Background", "[Mechanical Engineering qualification — verified details]"),
        (
            "Machining ML preparation",
            "PHM2010 RUL experiments: https://github.com/nhase13-spec/cnc-tool-remaining-useful-life-prediction",
        ),
        ("Research readiness", "Evidence audit complete; external PHM CSV download recommended for doctoral scale-up."),
    ]:
        _add_heading(doc, heading, 2)
        doc.add_paragraph(text)
    out = REPORTS / "GKN_EngD_Research_Portfolio.docx"
    doc.save(out)
    return out


def export_pdf(docx_path: Path) -> Path | None:
    pdf_path = docx_path.with_suffix(".pdf")
    try:
        import win32com.client

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(docx_path))
        doc.SaveAs(str(pdf_path), FileFormat=17)
        doc.Close()
        word.Quit()
        return pdf_path
    except Exception:
        return None


def main() -> None:
    r1 = build_main_report()
    r2 = build_portfolio()
    for p in (r1, r2):
        pdf = export_pdf(p)
        print("Wrote", p, "PDF:", pdf)


if __name__ == "__main__":
    main()