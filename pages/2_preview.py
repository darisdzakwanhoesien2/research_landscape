import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
INTERIM_DIR = BASE_DIR / "data" / "interim"

st.title("👀 Preview Normalized Data")

files = list(INTERIM_DIR.glob("*.csv"))

if not files:
    st.info("No normalized files yet. Run ingestion first.")
    st.stop()

file = st.selectbox("Select file", files)

df = pd.read_csv(file)
st.dataframe(df, use_container_width=True)
