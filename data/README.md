# Data layout

Raw PHM Society 2010 milling challenge archives (~800 MB per cutter) are **not** committed.
Place official per-cut CSV folders under `data/raw/phm2010/{c1,c4,c6}/` when available
(Kaggle: `rabahba/phm-data-challenge-2010`, or PHM Society challenge page).

## Bundled research inputs (download locally — not in git)

| File | Source | Role |
|------|--------|------|
| `external/phm2010_bundle_high_resolution.csv` | [katulu-io/uniwear-dataset](https://github.com/katulu-io/uniwear-dataset) `data/` (CC BY 4.0) | Smoothed multi-channel signals + `tool_wear` (mm) for c1, c4, c6 |
| `raw/phm2010_wear/c4_wear.csv`, `c6_wear.csv` | CDAR tool-wear reproduction package (local copy) | Per-flute wear in µm, 315 cuts |
| `raw/phm2010_wear/c1_wear_bundle.csv` | Derived from UniWear bundle steps | Max wear per segment (255 cuts) — **not** official per-flute file |
| `raw/cdar_npy/c4.npy`, `c6.npy` | CDAR package | Optional single-channel 20k samples × 313 cuts |

## NASA Milling (`data/external/nasa_mill.zip`)

If present and valid, run `cnc-rul audit --nasa`. Local placeholder archives may be invalid;
see `research_evidence_audit.md`.