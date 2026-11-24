"""Research-only decision-support demonstrator (does not control machinery)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

MASTER = ROOT / "results" / "tables" / "master_cut_features.csv"
PREDS = ROOT / "results" / "tables" / "predictions_loro.csv"

st.set_page_config(page_title="Tool RUL Research Demo", layout="wide")
st.title("Data-driven tool life — research demonstrator")
st.caption("Predictions are illustrative. Operator / engineering approval is required for replacement.")

if not MASTER.exists():
    st.warning("Run `python scripts/run_all.py` from the repository root first.")
    st.stop()

master = pd.read_csv(MASTER)
tool = st.selectbox("Tool", sorted(master["tool"].unique()))
cut = st.slider("Cut index", int(master["cut_index"].min()), int(master["cut_index"].max()), 50)
row = master[(master["tool"] == tool) & (master["cut_index"] == cut)]
if row.empty:
    st.error("No row for selection")
    st.stop()
row = row.iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Wear (µm)", f"{row.get('wear_um', float('nan')):.1f}")
col2.metric("RUL physical target", f"{row.get('rul_physical_cycles', float('nan')):.0f} cuts")
col3.metric("Target type", str(row.get("target_type", "n/a")))

risk_th = st.slider("Illustrative wear alert (µm)", 150, 350, 300)
if float(row.get("wear_um", 0)) >= risk_th:
    st.error("Recommend engineering review for tool replacement (threshold exceeded or alert).")
elif float(row.get("wear_um", 0)) >= 0.8 * risk_th:
    st.warning("Inspect or obtain further evidence.")
else:
    st.success("Continue approved operation (subject to plant procedures).")

if PREDS.exists():
    pred = pd.read_csv(PREDS)
    sub = pred[(pred["tool"] == tool) & (pred["cut_index"] == cut)]
    if not sub.empty:
        st.subheader("Held-out model predictions at this cut")
        st.dataframe(sub[["model", "y_true", "y_pred", "error"]].head(10))

st.line_chart(master[master["tool"] == tool].set_index("cut_index")["wear_um"])