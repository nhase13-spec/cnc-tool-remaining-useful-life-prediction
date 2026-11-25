# CNC tool remaining useful life prediction

Independent academic proof-of-concept for **data-driven tool-life prediction** using the PHM Society 2010 milling challenge (cutters **c1, c4, c6**).  
Aligned with Sheffield MADE4Manufacturing / GKN Aerospace EngD *themes* — **not** a GKN production system.

## Quick start

```bash
cd D:\AI\cnc-tool-remaining-useful-life-prediction
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

python scripts/run_all.py
# or:
python -m cnc_rul.cli audit
python -m cnc_rul.cli run
python -m cnc_rul.cli dashboard
```

## Data

See [`data/README.md`](data/README.md). Full ~800 MB per-cut CSV archives are **not** committed.  
Bundled inputs: Katulu **UniWear** PHM high-resolution bundle (CC BY 4.0), local **c4/c6** flute wear tables, optional CDAR `c4.npy`/`c6.npy`.

Place official PHM CSV folders under `data/raw/phm2010/{c1,c4,c6}/` when you obtain them (Kaggle / PHM Society).

## Reuse from other projects

- Statistical feature ideas adapted from `D:\AI\_vibracnc` (separate Sandvik / anomaly stack — not a dependency).
- Surface-roughness ML tooling lives under `engD_milling_ml_starter` and is intentionally separate.

## Outputs (local only — not committed)

Run `python scripts/run_all.py` then, optionally, portfolio builders under `scripts/`.

| Path | Content |
|------|---------|
| `research_evidence_audit.md` | Committed audit template; refreshed by `cnc-rul audit` |
| `results/` | Figures and metrics (gitignored) |
| `reports/` | DOCX/PDF reports (gitignored); see `reports/REPRODUCTION.md` |
| `dashboard/app.py` | Streamlit demonstrator (needs `results/` from a pipeline run) |

## Tests

```bash
pytest tests/
```

## Academic integrity

- No fabricated threshold crossings.
- Experimental endpoints are **not** assumed to be catastrophic failure.
- Overlapping 315-cut experimental design is tested for trivial remaining-recorded-life prediction.