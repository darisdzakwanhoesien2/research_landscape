import streamlit as st
import pandas as pd
from pathlib import Path

from utils.bib_parser import parse_bib_file
from utils.csv_loader import load_csv_file
from utils.normalizer import normalize_dataframe, deduplicate

BASE_DIR = Path(__file__).parents[1]
BIB_DIR = BASE_DIR / "data/bib"
CSV_DIR = BASE_DIR / "data/csv"

st.title("🔄 Consolidate Data")

@st.cache_data
def load_all_data():
    frames = []

    for f in BIB_DIR.glob("*.bib"):
        df = parse_bib_file(f)
        frames.append(normalize_dataframe(df))

    for f in CSV_DIR.glob("*.csv"):
        df = load_csv_file(f)
        frames.append(normalize_dataframe(df))

    merged = pd.concat(frames, ignore_index=True)
    deduped = deduplicate(merged)
    return merged, deduped

if st.button("🚀 Load & Consolidate"):
    raw, clean = load_all_data()

    st.session_state["raw_df"] = raw
    st.session_state["clean_df"] = clean

    st.success(f"Loaded {len(raw)} rows → {len(clean)} after deduplication")

    st.subheader("Preview")
    st.dataframe(clean.head(50), use_container_width=True)
