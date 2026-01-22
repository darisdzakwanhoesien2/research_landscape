import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
import textwrap
import hashlib

import bibtexparser
from bibtexparser.bparser import BibTexParser


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📚 BibTeX Batch Curator & Exporter",
    layout="wide"
)

st.title("📚 BibTeX Batch Curator & Exporter")
st.caption(
    "Select BibTeX databases from data/bib, flatten entries, "
    "select papers by title, and export curated datasets."
)

# =========================================================
# GLOBAL RELOAD
# =========================================================

with st.sidebar:
    st.divider()
    if st.button("🔄 Reload Data"):
        st.cache_data.clear()
        st.toast("Cache cleared — reloading data...")
        st.rerun()

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"
EXPORT_DIR = BASE_DIR / "outputs"

for d in [BIB_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 Bib Folder: `{BIB_DIR}`")
st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")

# =========================================================
# UTILITIES
# =========================================================

def normalize_string(text: str) -> str:
    return str(text).strip().lower()


def directory_fingerprint(path: Path) -> str:
    parts = []
    for p in sorted(path.glob("*")):
        if p.is_file():
            stat = p.stat()
            parts.append(f"{p.name}:{stat.st_mtime_ns}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def parse_bib_file(path: Path) -> list[dict]:
    """Parse one .bib file into a list of dict rows."""
    parser = BibTexParser(common_strings=True)
    with open(path, encoding="utf-8") as f:
        bib_db = bibtexparser.load(f, parser=parser)

    rows = []
    for entry in bib_db.entries:
        row = {
            "bib_key": entry.get("ID", ""),
            "entry_type": entry.get("ENTRYTYPE", ""),
            "title": entry.get("title", ""),
            "authors": entry.get("author", entry.get("editor", "")),
            "year": entry.get("year", ""),
            "booktitle": entry.get("booktitle", ""),
            "journal": entry.get("journal", ""),
            "publisher": entry.get("publisher", ""),
            "address": entry.get("address", ""),
            "pages": entry.get("pages", ""),
            "url": entry.get("url", ""),
            "__source_file": path.name,
        }
        rows.append(row)

    return rows


# =========================================================
# DATA LOADERS
# =========================================================

@st.cache_data
def discover_bib_files():
    return sorted(BIB_DIR.glob("*.bib"))


@st.cache_data(show_spinner=False)
def load_multiple_bib(files: list[Path]) -> pd.DataFrame:
    all_rows = []
    for f in files:
        try:
            rows = parse_bib_file(f)
            all_rows.extend(rows)
        except Exception as e:
            st.warning(f"⚠️ Failed to parse {f.name}: {e}")

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["title_norm"] = df["title"].map(normalize_string)
    return df


# =========================================================
# EXPORTERS
# =========================================================

def export_csv(df: pd.DataFrame) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"bib_curated_{ts}.csv"
    df.to_csv(path, index=False)
    return path


def export_markdown(df: pd.DataFrame) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"bib_curated_{ts}.md"

    blocks = []
    blocks.append("# 📚 Curated BibTeX Dataset\n")
    blocks.append(f"_Generated at: {datetime.now().isoformat()}_")
    blocks.append(f"_Total papers: {len(df)}_\n")

    for _, row in df.iterrows():
        title = row.get("title", "").strip() or "Untitled"

        block = f"""
## {title}

- **Authors:** {row.get("authors","")}
- **Year:** {row.get("year","")}
- **Entry Type:** {row.get("entry_type","")}
- **Booktitle / Journal:** {row.get("booktitle") or row.get("journal")}
- **Publisher:** {row.get("publisher","")}
- **Pages:** {row.get("pages","")}
- **URL:** {row.get("url","")}
- **Source File:** {row.get("__source_file","")}

"""
        blocks.append(block.strip())
        blocks.append("\n---\n")

    path.write_text("\n".join(blocks), encoding="utf-8")
    return path


# =========================================================
# DATA SOURCE SELECTION
# =========================================================

st.sidebar.header("📂 Bib Dataset Selection")

bib_files = discover_bib_files()

if not bib_files:
    st.warning("⚠️ No .bib files found in data/bib/")
    st.stop()

selected_files = st.sidebar.multiselect(
    "Select BibTeX files to load",
    bib_files,
    default=bib_files[:1],
    format_func=lambda p: p.name
)

if not selected_files:
    st.info("Please select at least one BibTeX file.")
    st.stop()

raw_df = load_multiple_bib(selected_files)

st.sidebar.metric("Total loaded entries", len(raw_df))

if raw_df.empty:
    st.warning("No entries parsed from selected BibTeX files.")
    st.stop()

# =========================================================
# TITLE SELECTION (POSITIVE FILTER)
# =========================================================

st.sidebar.divider()
st.sidebar.header("✅ Select Papers")

all_titles = (
    raw_df["title"]
    .dropna()
    .astype(str)
    .str.strip()
    .sort_values()
    .unique()
    .tolist()
)

selected_titles = st.sidebar.multiselect(
    "Select titles to INCLUDE",
    all_titles
)

# Optional bulk paste
paste_titles_text = st.sidebar.text_area(
    "Paste titles to include (one per line)",
    height=120
)

manual_titles = {normalize_string(t) for t in selected_titles}
pasted_titles = {
    normalize_string(t)
    for t in paste_titles_text.splitlines()
    if t.strip()
}

selected_title_norms = manual_titles | pasted_titles

# =========================================================
# APPLY SELECTION
# =========================================================

df = raw_df.copy()

if selected_title_norms:
    df = df[df["title_norm"].isin(selected_title_norms)]

# Optional deduplication
st.sidebar.divider()
st.sidebar.header("🧪 Options")

deduplicate = st.sidebar.checkbox("Deduplicate by title", True)

if deduplicate:
    df = df.drop_duplicates(subset=["title_norm"])

df = df.drop(columns=["title_norm"], errors="ignore")

# =========================================================
# METRICS
# =========================================================

st.divider()
st.subheader("📊 Batch Summary")

c1, c2, c3 = st.columns(3)
c1.metric("Loaded Entries", len(raw_df))
c2.metric("Selected Entries", len(df))
c3.metric("Unique Source Files", df["__source_file"].nunique())

# =========================================================
# PREVIEW
# =========================================================

st.divider()
st.subheader("🔍 Preview")
st.dataframe(df, use_container_width=True, height=520)

# =========================================================
# EXPORT
# =========================================================

st.divider()
st.subheader("💾 Export")

col1, col2 = st.columns(2)

with col1:
    if st.button("⬇️ Export CSV", type="primary"):
        path = export_csv(df)
        with open(path, "rb") as f:
            st.download_button(
                "Download CSV",
                f,
                file_name=path.name,
                mime="text/csv"
            )
        st.success(f"Saved to: {path}")

with col2:
    if st.button("📝 Export Markdown"):
        path = export_markdown(df)
        with open(path, "rb") as f:
            st.download_button(
                "Download Markdown",
                f,
                file_name=path.name,
                mime="text/markdown"
            )
        st.success(f"Saved to: {path}")
