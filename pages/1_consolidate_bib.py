import streamlit as st
from pathlib import Path
import pandas as pd
import bibtexparser
from io import StringIO

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="🔎 Consolidate BibTeX",
    layout="wide"
)

st.title("🔎 BibTeX Consolidator")
st.caption("Filter and merge BibTeX entries from multiple .bib files")

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
EXPORT_DIR = PROJECT_ROOT / "exports"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 Bib Folder: `{DATA_DIR}`")

if not DATA_DIR.exists():
    st.error(f"❌ Data folder not found: {DATA_DIR}")
    st.stop()

# =====================================================
# FILE DISCOVERY
# =====================================================

@st.cache_data
def discover_bib_files():
    return sorted(DATA_DIR.rglob("*.bib"))

bib_files = discover_bib_files()

if not bib_files:
    st.warning("⚠️ No .bib files found")
    st.stop()

st.sidebar.success(f"📄 Found {len(bib_files)} BibTeX files")

# =====================================================
# LOAD + PARSE
# =====================================================

@st.cache_data
def load_all_bib_entries(paths):
    all_entries = []

    for path in paths:
        try:
            with open(path, encoding="utf-8") as bibfile:
                parser = bibtexparser.bparser.BibTexParser(common_strings=True)
                bib_database = bibtexparser.load(bibfile, parser=parser)

                for entry in bib_database.entries:
                    entry["_source_file"] = path.name
                    all_entries.append(entry)

        except Exception as e:
            print(f"Failed to load {path}: {e}")

    return all_entries


all_entries = load_all_bib_entries(tuple(bib_files))
st.success(f"✅ Loaded {len(all_entries)} BibTeX entries")

# =====================================================
# FILTER CONTROLS
# =====================================================

st.subheader("🔍 Filter")

col1, col2 = st.columns(2)

with col1:
    keyword = st.text_input(
        "Keyword (search in title, abstract, author, booktitle)",
        placeholder="e.g. sentiment, transformer, ESG, reasoning"
    )

with col2:
    year_filter = st.text_input(
        "Year filter (optional)",
        placeholder="e.g. 2020"
    )

# =====================================================
# FILTER LOGIC
# =====================================================

def normalize(text):
    return (text or "").lower()


def entry_matches(entry):
    if keyword:
        blob = " ".join([
            normalize(entry.get("title")),
            normalize(entry.get("abstract")),
            normalize(entry.get("author")),
            normalize(entry.get("booktitle")),
        ])
        if keyword.lower() not in blob:
            return False

    if year_filter:
        if year_filter not in str(entry.get("year", "")):
            return False

    return True


filtered_entries = [e for e in all_entries if entry_matches(e)]

st.info(f"🎯 Matched entries: {len(filtered_entries)}")

# =====================================================
# DISPLAY TABLE
# =====================================================

def entries_to_dataframe(entries):
    rows = []
    for e in entries:
        rows.append({
            "ID": e.get("ID"),
            "Title": e.get("title"),
            "Author": e.get("author"),
            "Year": e.get("year"),
            "Venue": e.get("booktitle") or e.get("journal"),
            "SourceFile": e.get("_source_file"),
        })
    return pd.DataFrame(rows)


if filtered_entries:
    df = entries_to_dataframe(filtered_entries)
    st.dataframe(df, use_container_width=True)

else:
    st.warning("No matching entries")

# =====================================================
# EXPORT CONSOLIDATED BIB
# =====================================================

st.divider()
st.subheader("📤 Export Consolidated BibTeX")

export_name = st.text_input(
    "Output filename",
    value="consolidated.bib"
)

if st.button("🚀 Generate BibTeX"):
    if not filtered_entries:
        st.error("No entries to export")
        st.stop()

    db = bibtexparser.bibdatabase.BibDatabase()
    clean_entries = []

    for e in filtered_entries:
        e2 = dict(e)
        e2.pop("_source_file", None)  # remove internal field
        clean_entries.append(e2)

    db.entries = clean_entries
    writer = bibtexparser.bwriter.BibTexWriter()

    bib_str = writer.write(db)

    output_path = EXPORT_DIR / export_name
    output_path.write_text(bib_str, encoding="utf-8")

    st.success(f"✅ Saved: {output_path}")

    st.download_button(
        label="⬇️ Download BibTeX",
        data=bib_str,
        file_name=export_name,
        mime="text/plain"
    )
