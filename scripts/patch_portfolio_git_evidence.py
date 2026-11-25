#!/usr/bin/env python
"""Append Git repository evidence to EngD portfolio DOCX (when Word COM is unavailable)."""
from __future__ import annotations

import subprocess
from pathlib import Path

from docx import Document
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
GITHUB = "https://github.com/nhase13-spec/cnc-tool-remaining-useful-life-prediction"
TARGETS = [
    Path(r"C:\Users\hasen\Downloads\EngD_Tool_Life_RUL_Research_Portfolio_Final.docx"),
]


def git_meta() -> dict[str, str]:
    def g(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

    return {
        "url": GITHUB,
        "branch": g("branch", "--show-current"),
        "short": g("rev-parse", "--short", "HEAD"),
        "subject": g("log", "-1", "--format=%s"),
        "date": g("log", "-1", "--format=%ci"),
        "files": str(len(g("ls-files").splitlines())),
    }


def patch(path: Path) -> None:
    if not path.is_file():
        print(f"Skip missing {path}")
        return
    meta = git_meta()
    doc = Document(str(path))
    body = "\n".join(p.text for p in doc.paragraphs)
    if "nhase13-spec/cnc-tool-remaining-useful-life-prediction" in body:
        print(f"Already contains git evidence: {path}")
        return
    doc.add_page_break()
    h = doc.add_heading("7.2  Public Git repository evidence (update)", level=2)
    h.runs[0].font.size = Pt(12)
    p = doc.add_paragraph()
    p.add_run(
        "The RUL proof-of-concept source, tests and reproduction instructions are version-controlled at "
    )
    p.add_run(GITHUB).bold = True
    p.add_run(
        ". Generated results/figures and report PDFs are produced locally and are not stored in git "
        "(see reports/REPRODUCTION.md)."
    )
    table = doc.add_table(rows=6, cols=2)
    rows = [
        ("Repository URL", meta["url"]),
        ("Branch", meta["branch"]),
        ("Latest commit", meta["short"]),
        ("Commit subject", meta["subject"]),
        ("Commit date", meta["date"]),
        ("Tracked files (git ls-files)", meta["files"]),
    ]
    for i, (a, b) in enumerate(rows):
        table.rows[i].cells[0].text = a
        table.rows[i].cells[1].text = b
    doc.add_paragraph(
        "Tracked areas include src/cnc_rul/, tests/, configs/, scripts/, dashboard/, "
        "data/raw/phm2010_wear/*.csv. Large UniWear bundle CSV: scripts/fetch_phm_bundle.py."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    print(f"Patched {path}")


def main() -> None:
    for t in TARGETS:
        patch(t)


if __name__ == "__main__":
    main()