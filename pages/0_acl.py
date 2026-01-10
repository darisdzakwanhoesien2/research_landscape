import streamlit as st
from pathlib import Path
import re
import pandas as pd

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="Bib Abstract Viewer", layout="wide")
st.title("📚 Bib File Abstract Explorer")
st.caption("Select a .bib file and view Title, DOI, and Abstract")

BASE_DIR = Path(__file__).resolve().parents[1]
BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"

if not BIB_DIR.exists():
    st.error(f"❌ Directory not found: {BIB_DIR}")
    st.stop()

# =====================================================
# HELPERS
# =====================================================

def parse_bib_entries(text: str):
    """
    Very lightweight BibTeX parser:
    Extracts title, doi, abstract per entry.
    """
    entries = re.findall(r'@.+?\{[^,]+,(.*?)\n\}', text, flags=re.S)

    records = []

    for body in entries:
        def get_field(name):
            m = re.search(rf'{name}\s*=\s*\{{([\s\S]*?)\}}', body, re.I)
            if not m:
                m = re.search(rf'{name}\s*=\s*"([\s\S]*?)"', body, re.I)
            return m.group(1).replace("\n", " ").strip() if m else ""

        title = get_field("title")
        doi = get_field("doi")
        abstract = get_field("abstract")

        if title or doi or abstract:
            records.append({
                "title": title,
                "doi": doi,
                "abstract": abstract
            })

    return pd.DataFrame(records)


# =====================================================
# FILE DROPDOWN
# =====================================================

bib_files = sorted(BIB_DIR.glob("*.bib"))

if not bib_files:
    st.warning("⚠️ No .bib files found in directory.")
    st.stop()

selected_file = st.selectbox(
    "Select BibTeX file",
    options=bib_files,
    format_func=lambda p: p.name
)

st.caption(f"Source: `{selected_file.relative_to(BASE_DIR)}`")

# =====================================================
# LOAD & PARSE
# =====================================================

with st.spinner("Parsing BibTeX file..."):
    text = selected_file.read_text(encoding="utf-8", errors="ignore")
    df = parse_bib_entries(text)

# =====================================================
# DISPLAY
# =====================================================

st.subheader("📄 Extracted Records")

col1, col2, col3 = st.columns(3)
col1.metric("Total entries", len(df))
col2.metric("With DOI", (df["doi"] != "").sum())
col3.metric("With Abstract", (df["abstract"] != "").sum())

st.dataframe(df, use_container_width=True, height=500)

# =====================================================
# DOWNLOAD
# =====================================================

csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download as CSV",
    data=csv_data,
    file_name=selected_file.stem + "_abstracts.csv",
    mime="text/csv"
)
