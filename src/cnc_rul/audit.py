from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd

from cnc_rul.config import ProjectConfig
from cnc_rul.phm_data import load_bundle, segment_bundle_by_wear_step
from cnc_rul.wear import audit_wear_table, build_c1_wear_from_bundle, load_tool_wear


def _nasa_status(path: Path) -> dict:
    if not path.exists():
        return {"available": False, "reason": "file missing"}
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()[:20]
        return {"available": True, "n_files": len(names), "sample": names}
    except zipfile.BadZipFile:
        return {"available": False, "reason": "invalid zip (placeholder or corrupt)"}


def run_audit(cfg: ProjectConfig) -> Path:
    out = cfg.resolve(cfg.tables_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle(cfg.resolve(cfg.bundle_csv))
    build_c1_wear_from_bundle(bundle, cfg.resolve(cfg.wear_dir))

    rows = []
    for tool in cfg.tools:
        wear = load_tool_wear(tool, cfg.resolve(cfg.wear_dir), bundle)
        seg = segment_bundle_by_wear_step(bundle, tool)
        rows.append({
            "tool": tool,
            "wear_cuts_official": len(wear),
            "bundle_wear_steps": len(seg),
            "bundle_rows": int((bundle["experiment_tag"] == tool).sum()),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out / "schema_audit.csv", index=False)

    wear_audits = []
    for th in cfg.sensitivity_thresholds_um:
        for tool in cfg.tools:
            w = load_tool_wear(tool, cfg.resolve(cfg.wear_dir), bundle)
            wear_audits.append(audit_wear_table(w, tool, th, "audit").__dict__)

    nasa = _nasa_status(cfg.resolve(Path("data/external/nasa_mill.zip")))
    report = {
        "phm_tools": list(cfg.tools),
        "wear_threshold_default_um": cfg.default_threshold_um,
        "nasa_milling": nasa,
        "identical_official_cut_counts": df["wear_cuts_official"].nunique() == 1,
        "wear_audits": wear_audits,
        "notes": [
            "No tool crosses 300 µm in available wear files — physical RUL is right-censored at that threshold.",
            "UniWear bundle uses fewer wear steps than 315 official cuts for some tools.",
            "c1 lacks local official per-flute CSV; bundle-derived wear used with disclosure.",
        ],
    }
    def _csv_block(frame: pd.DataFrame) -> str:
        return "```csv\n" + frame.to_csv(index=False) + "```"

    audit_path = cfg.root / "research_evidence_audit.md"
    lines = [
        "# Research evidence audit",
        "",
        "## PHM 2010 (primary)",
        "",
        _csv_block(df),
        "",
        "## Threshold sensitivity (µm)",
        "",
        _csv_block(pd.DataFrame(wear_audits)),
        "",
        "## NASA Milling (secondary)",
        "",
        f"```json\n{json.dumps(nasa, indent=2)}\n```",
        "",
        "## Integrity notes",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    audit_path.write_text("\n".join(lines), encoding="utf-8")

    with (cfg.resolve(cfg.metrics_dir) / "audit_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return audit_path