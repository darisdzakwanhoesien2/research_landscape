import streamlit as st
from pathlib import Path
from utils.exporter import export_csv, export_markdown

BASE_DIR = Path(__file__).parents[1]
OUTPUT_DIR = BASE_DIR / "data/output"
OUTPUT_DIR.mkdir(exist_ok=True)

st.title("⬇️ Export")

if "clean_df" not in st.session_state:
    st.warning("Please consolidate data first.")
    st.stop()

df = st.session_state["clean_df"]

csv_path = OUTPUT_DIR / "consolidated.csv"
md_path = OUTPUT_DIR / "consolidated.md"

if st.button("💾 Export CSV"):
    export_csv(df, csv_path)
    st.success(f"Saved: {csv_path}")

if st.button("📝 Export Markdown"):
    export_markdown(df, md_path)
    st.success(f"Saved: {md_path}")
