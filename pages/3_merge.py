import streamlit as st
import pandas as pd
from pathlib import Path
from pipeline.merger import deduplicate

BASE_DIR = Path(__file__).resolve().parents[1]
INTERIM_DIR = BASE_DIR / "data" / "interim"

st.title("🔗 Merge & Deduplicate")

files = list(INTERIM_DIR.glob("*.csv"))

if not files:
    st.warning("No normalized files available.")
    st.stop()

dfs = [pd.read_csv(f) for f in files]
combined = pd.concat(dfs, ignore_index=True)

st.metric("Raw Records", len(combined))

deduped = deduplicate(combined)
st.metric("After Deduplication", len(deduped))

st.dataframe(deduped.head(100), use_container_width=True)

st.session_state["merged_df"] = deduped
