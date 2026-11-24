#!/usr/bin/env python
"""Reproduce audit + experiments + reports."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cnc_rul.audit import run_audit  # noqa: E402
from cnc_rul.config import load_config  # noqa: E402
from cnc_rul.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    cfg = load_config(ROOT)
    run_audit(cfg)
    run_pipeline(cfg)
    build = ROOT / "scripts" / "build_reports.py"
    if build.exists():
        import subprocess

        candidates = [
            sys.executable,
            Path(r"D:\AI\WindowDesktopUI\.venv\Scripts\python.exe"),
        ]
        for py in candidates:
            if not Path(py).exists():
                continue
            rc = subprocess.run([str(py), str(build)], cwd=ROOT, check=False).returncode
            if rc == 0:
                break
        else:
            print("WARN: could not build DOCX/PDF — install python-docx or run scripts/build_reports.py manually.")


if __name__ == "__main__":
    main()