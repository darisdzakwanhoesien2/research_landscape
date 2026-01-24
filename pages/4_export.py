import streamlit as st
from pathlib import Path
from pipeline.export import export_all

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

st.title("⬇️ Export Merged Dataset")

if "merged_df" not in st.session_state:
    st.warning("Please run Merge step first.")
    st.stop()

df = st.session_state["merged_df"]

if st.button("🚀 Export"):
    outputs = export_all(df, PROCESSED_DIR)
    st.success("Export complete!")

    for k, path in outputs.items():
        st.write(f"✅ {k.upper()} → {path}")
