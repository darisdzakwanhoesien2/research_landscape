import streamlit as st
import pandas as pd
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="📝 Markdown Generator",
    layout="wide"
)

st.title("📝 Markdown Generator from Table")
st.caption("Generate concatenated markdown from Title + Abstract")

# =====================================================
# FILE UPLOAD
# =====================================================

uploaded = st.file_uploader(
    "Upload CSV table",
    type=["csv"]
)

if not uploaded:
    st.info("Upload your table CSV file")
    st.stop()

df = pd.read_csv(uploaded)

st.subheader("📊 Preview Input Table")
st.dataframe(df.head(20), use_container_width=True)

# =====================================================
# VALIDATION
# =====================================================

required_cols = ["Title", "Abstract", "Updated Abstract"]
missing = [c for c in required_cols if c not in df.columns]

if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# =====================================================
# TRANSFORMATION
# =====================================================

def resolve_abstract(row):
    abstract = str(row["Abstract"]).strip()
    updated = str(row["Updated Abstract"]).strip()

    if abstract.lower() == "(missing abstract)" or abstract == "":
        return updated
    return abstract


df["Final_Abstract"] = df.apply(resolve_abstract, axis=1)

df["Markdown"] = df.apply(
    lambda row: f"## {row['Title']}\n\n{row['Final_Abstract']}",
    axis=1
)

# =====================================================
# OUTPUT
# =====================================================

st.subheader("🧾 Generated Markdown Preview")

st.text_area(
    "Markdown Sample",
    value="\n\n---\n\n".join(df["Markdown"].head(5)),
    height=300
)

# =====================================================
# DOWNLOAD
# =====================================================

markdown_text = "\n\n---\n\n".join(df["Markdown"])

st.download_button(
    label="⬇️ Download Combined Markdown",
    data=markdown_text.encode("utf-8"),
    file_name="papers.md",
    mime="text/markdown"
)

# Optional CSV with Markdown column
csv_bytes = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download CSV with Markdown Column",
    data=csv_bytes,
    file_name="papers_with_markdown.csv",
    mime="text/csv"
)
