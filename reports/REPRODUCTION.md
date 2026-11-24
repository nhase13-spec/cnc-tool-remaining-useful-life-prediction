# Reproduction instructions

1. **Environment**: Python 3.10+, `pip install -r requirements.txt` (requires network for PyPI).
2. **PYTHONPATH**: `set PYTHONPATH=D:\AI\cnc-tool-remaining-useful-life-prediction\src` (or `pip install -e .` when PyPI works).
3. **Audit first**: `python -m cnc_rul.cli audit` — writes `research_evidence_audit.md`.
4. **Experiments**: `python -m cnc_rul.cli run` — figures under `results/figures/`, tables under `results/tables/`.
5. **Tests**: `pytest tests/`
6. **Reports**: `python scripts/build_reports.py` (needs `python-docx`; PDF needs Microsoft Word + `pywin32`).
7. **Dashboard**: `python -m cnc_rul.cli dashboard`

## Optional full-resolution PHM CSV

Download from Kaggle `rabahba/phm-data-challenge-2010` or PHM Society challenge page into:

`data/raw/phm2010/c1/*.csv` (etc.)

Re-run audit to confirm 315-cut alignment.