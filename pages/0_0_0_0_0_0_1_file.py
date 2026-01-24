import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parents[1]
BIB_DIR = BASE_DIR / "data/bib_new"
CSV_DIR = BASE_DIR / "data/csv_new"

st.title("📂 File Browser")

bib_files = list(BIB_DIR.glob("*.bib"))
csv_files = list(CSV_DIR.glob("*.csv"))

c1, c2 = st.columns(2)

with c1:
    st.subheader("📘 Bib Files")
    for f in bib_files:
        st.write("•", f.name)

with c2:
    st.subheader("📗 CSV Files")
    for f in csv_files:
        st.write("•", f.name)

st.success(f"Found {len(bib_files)} bib files and {len(csv_files)} csv files.")
