import streamlit as st
import pandas as pd
from pathlib import Path

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📎 Thesis CSV Merger",
    layout="wide"
)

st.title("📎 Thesis CSV Merger")
st.caption("Merge thesis_tech.csv and thesis_tags.csv using `label`")

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

TECH_PATH = DATA_DIR / "thesis_tech.csv"
TAGS_PATH = DATA_DIR / "thesis_tags.csv"

# =========================================================
# ACTION BAR
# =========================================================

col1, col2 = st.columns([1, 6])

with col1:
    if st.button("🔄 Reload"):
        st.cache_data.clear()
        st.rerun()

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_csvs():
    if not TECH_PATH.exists():
        raise FileNotFoundError(f"{TECH_PATH} not found")

    if not TAGS_PATH.exists():
        raise FileNotFoundError(f"{TAGS_PATH} not found")

    tech_df = pd.read_csv(TECH_PATH)
    tags_df = pd.read_csv(TAGS_PATH)

    return tech_df, tags_df


try:
    tech_df, tags_df = load_csvs()
except Exception as e:
    st.error(str(e))
    st.stop()

# =========================================================
# VALIDATION
# =========================================================

REQUIRED_TECH_COLS = {"label", "bibtex_key"}
REQUIRED_TAGS_COLS = {"label"}

missing_tech = REQUIRED_TECH_COLS - set(tech_df.columns)
missing_tags = REQUIRED_TAGS_COLS - set(tags_df.columns)

if missing_tech:
    st.error(f"❌ thesis_tech.csv missing columns: {missing_tech}")
    st.stop()

if missing_tags:
    st.error(f"❌ thesis_tags.csv missing columns: {missing_tags}")
    st.stop()

# =========================================================
# PREVIEW INPUT TABLES
# =========================================================

with st.expander("📄 Preview: thesis_tech.csv", expanded=False):
    st.dataframe(tech_df, use_container_width=True)

with st.expander("📄 Preview: thesis_tags.csv", expanded=False):
    st.dataframe(tags_df, use_container_width=True)

# =========================================================
# MERGE CONFIG
# =========================================================

st.subheader("🔗 Merge Configuration")

merge_type = st.selectbox(
    "Merge type",
    options=["left", "inner", "right", "outer"],
    index=0,
    help="""
left  = keep all rows from thesis_tags  
inner = only matching labels  
right = keep all rows from thesis_tech  
outer = keep everything
"""
)

# =========================================================
# MERGE
# =========================================================

merged_df = tags_df.merge(
    tech_df[["label", "bibtex_key"]],
    on="label",
    how=merge_type
)

# =========================================================
# MERGE STATS
# =========================================================

total_tags = len(tags_df)
total_tech = len(tech_df)
total_merged = len(merged_df)

matched = merged_df["bibtex_key"].notna().sum()
unmatched = merged_df["bibtex_key"].isna().sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Tags rows", total_tags)
col2.metric("Tech rows", total_tech)
col3.metric("Merged rows", total_merged)
col4.metric("Matched bibtex", matched)

if unmatched > 0:
    st.warning(f"⚠️ {unmatched} rows have no matching bibtex_key")

# =========================================================
# OUTPUT TABLE
# =========================================================

st.subheader("📊 Merged Result")

st.dataframe(
    merged_df,
    use_container_width=True,
    height=520
)

# =========================================================
# DOWNLOAD
# =========================================================

csv_bytes = merged_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download merged CSV",
    data=csv_bytes,
    file_name="thesis_merged.csv",
    mime="text/csv"
)
