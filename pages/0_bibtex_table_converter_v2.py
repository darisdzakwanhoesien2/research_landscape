import streamlit as st
from pathlib import Path
import pandas as pd
import bibtexparser
from io import StringIO

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="📄 BibTeX → Table",
    layout="wide"
)

st.title("📄 BibTeX → Table Converter")
st.caption("Upload or select BibTeX files and view them as a table")

# =====================================================
# PATH DISCOVERY (DEPLOYMENT SAFE)
# =====================================================

def find_repo_root(start: Path) -> Path:
    """
    Walk upward until we find a directory containing 'data/'.
    Works on local, Docker, Streamlit Cloud.
    """
    start = start.resolve()

    for parent in [start] + list(start.parents):
        if (parent / "data").exists():
            return parent

    return start


PROJECT_ROOT = find_repo_root(Path.cwd())
DATA_DIR = PROJECT_ROOT / "data" / "acl_anthology_new"

DATA_DIR.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 Dataset folder: `{DATA_DIR}`")

# =====================================================
# FILE DISCOVERY
# =====================================================

@st.cache_data
def discover_bib_files():
    return sorted(DATA_DIR.rglob("*.bib"))

dataset_files = discover_bib_files()

# =====================================================
# INPUT MODE
# =====================================================

st.sidebar.subheader("📥 Input Source")

input_mode = st.sidebar.radio(
    "Choose source:",
    ["Upload BibTeX file", "Select from dataset folder"]
)

bib_texts = []

# -------------------------------
# Upload mode
# -------------------------------
if input_mode == "Upload BibTeX file":
    uploads = st.file_uploader(
        "Upload one or more .bib files",
        type=["bib"],
        accept_multiple_files=True
    )

    for file in uploads or []:
        content = file.read().decode("utf-8", errors="ignore")
        bib_texts.append((file.name, content))

# -------------------------------
# Dataset selection mode
# -------------------------------
else:
    if not dataset_files:
        st.warning("⚠️ No .bib files found in dataset folder.")
    else:
        selected_files = st.multiselect(
            "Select BibTeX files:",
            options=dataset_files,
            format_func=lambda p: p.name
        )

        for path in selected_files:
            bib_texts.append((path.name, path.read_text(encoding="utf-8")))

# =====================================================
# PARSING
# =====================================================

def parse_bibtex(text: str, source_name: str):
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)

    try:
        bib_db = bibtexparser.loads(text, parser=parser)
    except Exception as e:
        st.error(f"❌ Failed parsing {source_name}: {e}")
        return []

    entries = []
    for entry in bib_db.entries:
        entry["_source_file"] = source_name
        entries.append(entry)

    return entries


all_entries = []

for name, text in bib_texts:
    all_entries.extend(parse_bibtex(text, name))

st.info(f"📚 Parsed entries: {len(all_entries)}")

# =====================================================
# TABLE CONVERSION
# =====================================================

def entries_to_dataframe(entries):
    rows = []

    for e in entries:
        rows.append({
            "ID": e.get("ID"),
            "Type": e.get("ENTRYTYPE"),
            "Title": e.get("title"),
            "Authors": e.get("author"),
            "Year": e.get("year"),
            "Booktitle": e.get("booktitle"),
            "Journal": e.get("journal"),
            "Publisher": e.get("publisher"),
            "DOI": e.get("doi"),
            "URL": e.get("url"),
            "Pages": e.get("pages"),
            "Abstract": e.get("abstract"),
            "SourceFile": e.get("_source_file"),
        })

    return pd.DataFrame(rows)


if all_entries:
    df = entries_to_dataframe(all_entries)

    st.subheader("📊 BibTeX Table")
    st.dataframe(df, use_container_width=True)

    # =====================================================
    # DOWNLOAD
    # =====================================================

    csv_bytes = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download CSV",
        data=csv_bytes,
        file_name="bibtex_table.csv",
        mime="text/csv"
    )

else:
    st.warning("No BibTeX entries loaded yet.")
