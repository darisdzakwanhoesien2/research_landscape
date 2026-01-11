import streamlit as st
import pandas as pd
from io import StringIO

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="CSV → Markdown Blocks", layout="wide")
st.title("📝 CSV → Markdown (Title / DOI / Abstract Blocks)")
st.caption("Upload CSV with columns: title, doi, abstract")

# =====================================================
# UPLOAD CSV
# =====================================================

uploaded_file = st.file_uploader(
    "Upload CSV file (must contain: title, doi, abstract)",
    type=["csv"]
)

if not uploaded_file:
    st.info("Please upload a CSV file to continue.")
    st.stop()

# =====================================================
# LOAD CSV
# =====================================================

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

required_cols = {"title", "doi", "abstract"}
missing = required_cols - set(df.columns)

if missing:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

st.subheader("🔍 CSV Preview")
st.dataframe(df, use_container_width=True, height=300)

# =====================================================
# CONVERT TO MARKDOWN
# =====================================================

def row_to_md(row):
    parts = [
        str(row["title"]).strip(),
        str(row["doi"]).strip(),
        str(row["abstract"]).strip(),
    ]
    return "\n".join(parts)

md_blocks = []
for _, row in df.iterrows():
    block = row_to_md(row)
    if block.strip():
        md_blocks.append(block)

markdown_text = "\n\n".join(md_blocks) + "\n"

# =====================================================
# OUTPUT
# =====================================================

st.subheader("📝 Markdown Output")

st.download_button(
    "⬇️ Download Markdown File",
    data=markdown_text.encode("utf-8"),
    file_name="papers_blocks.md",
    mime="text/markdown"
)


st.code(markdown_text, language="markdown")

# =====================================================
# STATS
# =====================================================

col1, col2, col3 = st.columns(3)
col1.metric("Total rows", len(df))
col2.metric("With DOI", df["doi"].astype(str).str.len().gt(5).sum())
col3.metric("With Abstract", df["abstract"].astype(str).str.len().gt(30).sum())

# =====================================================
# DOWNLOAD
# =====================================================

