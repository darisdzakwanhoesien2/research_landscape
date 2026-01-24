import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"

st.title("📥 Upload Raw Files")

rq = st.selectbox("Select Research Question", ["rq1", "rq2"])
target_dir = RAW_DIR / rq
target_dir.mkdir(parents=True, exist_ok=True)

files = st.file_uploader(
    "Upload CSV or BibTeX",
    type=["csv", "bib"],
    accept_multiple_files=True
)

if files:
    for file in files:
        path = target_dir / file.name
        path.write_bytes(file.read())
        st.success(f"Saved → {path}")
