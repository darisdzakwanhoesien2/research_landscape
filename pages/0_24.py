import streamlit as st
import pandas as pd
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "data" / "source_registry.json"

st.set_page_config(layout="wide")
st.title("📚 Source Registry Viewer")

if not REGISTRY_PATH.exists():
    st.error("Registry not found.")
    st.stop()

registry = json.loads(REGISTRY_PATH.read_text())

df = pd.DataFrame.from_dict(registry, orient="index").reset_index()
df.rename(columns={"index": "source_id"}, inplace=True)

st.dataframe(df, use_container_width=True)

st.download_button(
    "⬇ Download CSV",
    df.to_csv(index=False).encode("utf-8"),
    "source_registry.csv",
    "text/csv"
)
