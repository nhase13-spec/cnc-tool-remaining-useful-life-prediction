#!/usr/bin/env python
"""Copy PHM2010 bundle CSV from a local uniwear-dataset clone (not stored in git)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "external" / "phm2010_bundle_high_resolution.csv"
DEFAULT_SRC = ROOT.parent / "cnc-tool-remaining-useful-life-prediction" / "_tmp_uniwear"


def main() -> int:
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    else:
        candidates = [
            ROOT / "_tmp_uniwear" / "data" / "phm2010_bundle_high_resolution.csv",
            Path(r"D:\AI\cnc-tool-remaining-useful-life-prediction\_tmp_uniwear\data\phm2010_bundle_high_resolution.csv"),
        ]
        src = next((p for p in candidates if p.is_file()), None)
        if src is None:
            print(
                "Usage: python scripts/fetch_phm_bundle.py <path-to-phm2010_bundle_high_resolution.csv>\n"
                "Or clone https://github.com/katulu-io/uniwear-dataset and pass data/phm2010_bundle_high_resolution.csv"
            )
            return 1
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, TARGET)
    print(f"Copied to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())