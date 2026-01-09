import streamlit as st
import pandas as pd
from pathlib import Path
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
import io

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="BibTeX Abstract Search", layout="wide")
st.title("🔍 BibTeX Abstract Search Dashboard")

st.markdown("""
This app loads **large BibTeX files (20–50MB+)**, parses entries, and lets you:

- 🔎 Search in **abstract / title / author**
- 🎯 Filter by year or venue
- 📄 Preview matching papers
- ⬇️ Export filtered results to CSV

Works well with ACL Anthology full BibTeX dumps.
""")

# =====================================================
# DATA INPUT
# =====================================================

st.sidebar.header("📥 Load BibTeX")

mode = st.sidebar.radio("Load mode", ["Upload file", "Load from path"])

bibtex_text = None

if mode == "Upload file":
    uploaded = st.sidebar.file_uploader("Upload .bib file", type=["bib"])
    if uploaded:
        bibtex_text = uploaded.read().decode("utf-8", errors="ignore")

else:
    path = st.sidebar.text_input("Path to .bib file", "data/anthology.bib")
    if path and Path(path).exists():
        bibtex_text = Path(path).read_text(encoding="utf-8", errors="ignore")

if not bibtex_text:
    st.info("Upload a BibTeX file or provide a valid path to begin.")
    st.stop()

# =====================================================
# PARSE BIBTEX (FAST MODE)
# =====================================================

st.subheader("📚 Parsing BibTeX")

parser = BibTexParser(common_strings=True)
parser.customization = convert_to_unicode

with st.spinner("Parsing entries (this may take ~10–30s for big files)..."):
    bib_database = bibtexparser.loads(bibtex_text, parser=parser)

entries = bib_database.entries

st.success(f"Loaded {len(entries)} BibTeX entries")

# =====================================================
# TO DATAFRAME
# =====================================================

rows = []

for e in entries:
    rows.append({
        "id": e.get("ID", ""),
        "type": e.get("ENTRYTYPE", ""),
        "title": e.get("title", ""),
        "author": e.get("author", ""),
        "editor": e.get("editor", ""),
        "year": e.get("year", ""),
        "booktitle": e.get("booktitle", ""),
        "journal": e.get("journal", ""),
        "url": e.get("url", ""),
        "abstract": e.get("abstract", ""),
    })

df = pd.DataFrame(rows)

# =====================================================
# SEARCH & FILTER
# =====================================================

st.subheader("🔎 Search & Filters")

c1, c2, c3 = st.columns(3)

query = c1.text_input("Search (title / abstract / author)")
year_filter = c2.text_input("Year (optional)")
venue_filter = c3.text_input("Venue / Booktitle contains")

mask = pd.Series(True, index=df.index)

if query:
    q = query.lower()
    mask &= (
        df["title"].str.lower().str.contains(q, na=False)
        | df["abstract"].str.lower().str.contains(q, na=False)
        | df["author"].str.lower().str.contains(q, na=False)
    )

if year_filter:
    mask &= df["year"].astype(str).str.contains(year_filter)

if venue_filter:
    v = venue_filter.lower()
    mask &= (
        df["booktitle"].str.lower().str.contains(v, na=False)
        | df["journal"].str.lower().str.contains(v, na=False)
    )

filtered = df[mask]

st.success(f"Matched {len(filtered)} entries")

# =====================================================
# RESULTS VIEW
# =====================================================

st.subheader("📄 Results")

show_cols = st.multiselect(
    "Columns to show",
    options=df.columns.tolist(),
    default=["title", "author", "year", "booktitle", "url"]
)

st.dataframe(filtered[show_cols], use_container_width=True)

# =====================================================
# ABSTRACT PREVIEW
# =====================================================

st.subheader("📝 Abstract Preview")

idx = st.number_input(
    "Row index in filtered table",
    min_value=0,
    max_value=max(len(filtered) - 1, 0),
    value=0
)

if len(filtered) > 0:
    row = filtered.iloc[int(idx)]
    st.markdown(f"### {row['title']}")
    st.markdown(f"**Authors:** {row['author']}")
    st.markdown(f"**Venue:** {row['booktitle'] or row['journal']}")
    st.markdown(f"**Year:** {row['year']}")
    st.markdown(f"**URL:** {row['url']}")
    st.markdown("---")
    st.write(row["abstract"])

# =====================================================
# EXPORT
# =====================================================

st.subheader("⬇️ Export")

st.download_button(
    "Download filtered CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="bibtex_filtered.csv",
    mime="text/csv"
)
