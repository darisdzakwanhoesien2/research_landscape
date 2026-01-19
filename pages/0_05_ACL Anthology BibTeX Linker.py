import streamlit as st
import pandas as pd
from pathlib import Path
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
import re

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="BibTeX Batch Abstract Search", layout="wide")
st.title("🔍 BibTeX Abstract Search (Batch Mode)")

DATA_DIR = Path("data/acl_anthology")

st.markdown("""
This app handles **very large BibTeX files** by:
- robustly splitting BibTeX entries
- parsing only selected ranges (batch)
- avoiding full in-memory parsing

Use batch ranges like:
- `0 → 10,000`
- `15,000 → 50,000`
""")

# =====================================================
# ROBUST BIBTEX SPLITTER
# =====================================================

def split_bibtex_entries(text: str):
    # normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # split before every BibTeX entry (case-insensitive, start-of-line, allow spaces)
    parts = re.split(r'(?i)(?=^\\s*@\\w+\\s*\\{)', text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]

@st.cache_data(show_spinner=False)
def load_entries(text):
    return split_bibtex_entries(text)

# =====================================================
# LOAD BIBTEX
# =====================================================

st.sidebar.header("📥 Load BibTeX")

bib_files = sorted(DATA_DIR.glob("*.bib"))

mode = st.sidebar.radio(
    "Load mode",
    ["Select from folder", "Upload file"],
    index=0
)

bibtex_text = None

# ---------- DROPDOWN MODE ----------
if mode == "Select from folder":
    if not bib_files:
        st.sidebar.error(f"No .bib files found in {DATA_DIR}")
    else:
        selected = st.sidebar.selectbox(
            "Select BibTeX file",
            bib_files,
            format_func=lambda p: p.name
        )

        with st.spinner(f"Loading {selected.name} ..."):
            bibtex_text = selected.read_text(encoding="utf-8", errors="ignore")

# ---------- UPLOAD MODE ----------
else:
    uploaded = st.sidebar.file_uploader("Upload .bib file", type=["bib"])
    if uploaded:
        bibtex_text = uploaded.read().decode("utf-8", errors="ignore")

if not bibtex_text:
    st.info("Load a BibTeX file to begin.")
    st.stop()

# =====================================================
# SPLIT & COUNT
# =====================================================

with st.spinner("Indexing BibTeX entries (fast)..."):
    all_entries = load_entries(bibtex_text)

TOTAL = len(all_entries)
st.success(f"Detected {TOTAL:,} BibTeX entries")

# =====================================================
# RANGE SELECTION
# =====================================================

st.subheader("📦 Select Batch Range")

c1, c2, c3 = st.columns(3)

start_idx = c1.number_input(
    "Start index",
    min_value=0,
    max_value=max(TOTAL - 1, 0),
    value=0,
    step=1000
)

end_idx = c2.number_input(
    "End index (exclusive)",
    min_value=1,
    max_value=TOTAL,
    value=min(1000, TOTAL),
    step=1000
)

if start_idx >= end_idx:
    st.error("Start must be smaller than End")
    st.stop()

subset_raw = all_entries[int(start_idx):int(end_idx)]
c3.metric("Entries in batch", len(subset_raw))

# =====================================================
# PARSE ONLY SELECTED BATCH
# =====================================================

parser = BibTexParser(common_strings=True)
parser.customization = convert_to_unicode

rows = []

with st.spinner("Parsing selected batch..."):
    for raw in subset_raw:
        try:
            db = bibtexparser.loads(raw, parser=parser)
            if db.entries:
                e = db.entries[0]
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
        except Exception:
            pass

df = pd.DataFrame(rows)
st.success(f"Parsed {len(df)} entries")

# =====================================================
# SEARCH & FILTER
# =====================================================

st.subheader("🔎 Search & Filter (within batch)")

c1, c2, c3 = st.columns(3)

query = c1.text_input("Search (title / abstract / author)")
year_filter = c2.text_input("Year")
venue_filter = c3.text_input("Venue / Booktitle")

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
st.success(f"Matched {len(filtered)} entries in batch")

# =====================================================
# TABLE VIEW
# =====================================================

st.subheader("📄 Results Table")

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

if len(filtered) > 0:
    idx = st.number_input(
        "Row index in filtered table",
        min_value=0,
        max_value=len(filtered) - 1,
        value=0
    )

    row = filtered.iloc[int(idx)]

    st.markdown(f"### {row['title']}")
    st.markdown(f"**Authors:** {row['author']}")
    st.markdown(f"**Venue:** {row['booktitle'] or row['journal']}")
    st.markdown(f"**Year:** {row['year']}")
    st.markdown(f"**URL:** {row['url']}")
    st.markdown("---")
    st.write(row["abstract"])
else:
    st.info("No results to preview.")

# =====================================================
# EXPORT
# =====================================================

st.subheader("⬇️ Export")

st.download_button(
    "Download filtered CSV (current batch)",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name=f"bibtex_batch_{start_idx}_{end_idx}_filtered.csv",
    mime="text/csv"
)



# import streamlit as st
# import pandas as pd
# from pathlib import Path
# import bibtexparser
# from bibtexparser.bparser import BibTexParser
# from bibtexparser.customization import convert_to_unicode

# # =====================================================
# # CONFIG
# # =====================================================

# st.set_page_config(page_title="BibTeX Batch Abstract Search", layout="wide")
# st.title("🔍 BibTeX Abstract Search (Batch Mode)")

# DEFAULT_PATH = "data/acl_anthology/anthology+abstracts.bib"

# st.markdown("""
# This app handles **very large BibTeX files** by:
# - streaming entries
# - parsing only selected ranges
# - avoiding full in-memory parsing

# Use batch ranges like:
# - 0 → 10,000
# - 15,000 → 50,000
# """)

# # =====================================================
# # STREAM BIBTEX ENTRY READER
# # =====================================================

# def iter_bibtex_entries(text):
#     entry = []
#     inside = False

#     for line in text.splitlines():
#         if line.startswith("@"):
#             if entry:
#                 yield "\n".join(entry)
#                 entry = []
#             inside = True

#         if inside:
#             entry.append(line)

#     if entry:
#         yield "\n".join(entry)

# @st.cache_data(show_spinner=False)
# def load_raw_entries_from_text(text):
#     return list(iter_bibtex_entries(text))

# # =====================================================
# # LOAD BIBTEX
# # =====================================================

# st.sidebar.header("📥 Load BibTeX")

# mode = st.sidebar.radio(
#     "Load mode",
#     ["Use default dataset", "Upload file", "Load from custom path"],
#     index=0
# )

# bibtex_text = None

# if mode == "Use default dataset":
#     if Path(DEFAULT_PATH).exists():
#         with st.spinner(f"Loading {DEFAULT_PATH} ..."):
#             bibtex_text = Path(DEFAULT_PATH).read_text(encoding="utf-8", errors="ignore")
#         st.sidebar.success("Loaded default dataset")
#     else:
#         st.sidebar.error(f"File not found: {DEFAULT_PATH}")

# elif mode == "Upload file":
#     uploaded = st.sidebar.file_uploader("Upload .bib file", type=["bib"])
#     if uploaded:
#         bibtex_text = uploaded.read().decode("utf-8", errors="ignore")

# else:
#     path = st.sidebar.text_input("Path to .bib file", DEFAULT_PATH)
#     if path and Path(path).exists():
#         bibtex_text = Path(path).read_text(encoding="utf-8", errors="ignore")

# if not bibtex_text:
#     st.info("Load a BibTeX file to begin.")
#     st.stop()

# # =====================================================
# # STREAM & COUNT ENTRIES
# # =====================================================

# with st.spinner("Indexing BibTeX entries (fast)..."):
#     all_entries = load_raw_entries_from_text(bibtex_text)

# TOTAL = len(all_entries)
# st.success(f"Detected {TOTAL:,} BibTeX entries")

# # =====================================================
# # RANGE SELECTION
# # =====================================================

# st.subheader("📦 Select Batch Range")

# c1, c2, c3 = st.columns(3)

# start_idx = c1.number_input(
#     "Start index",
#     min_value=0,
#     max_value=max(TOTAL - 1, 0),
#     value=0,
#     step=1000
# )

# end_idx = c2.number_input(
#     "End index (exclusive)",
#     min_value=1,
#     max_value=TOTAL,
#     value=min(1000, TOTAL),
#     step=1000
# )

# if start_idx >= end_idx:
#     st.error("Start must be smaller than End")
#     st.stop()

# subset_raw = all_entries[int(start_idx):int(end_idx)]

# c3.metric("Entries in batch", len(subset_raw))

# # =====================================================
# # PARSE ONLY SELECTED BATCH
# # =====================================================

# parser = BibTexParser(common_strings=True)
# parser.customization = convert_to_unicode

# rows = []

# with st.spinner("Parsing selected batch..."):
#     for raw in subset_raw:
#         try:
#             db = bibtexparser.loads(raw, parser=parser)
#             if db.entries:
#                 e = db.entries[0]
#                 rows.append({
#                     "id": e.get("ID", ""),
#                     "type": e.get("ENTRYTYPE", ""),
#                     "title": e.get("title", ""),
#                     "author": e.get("author", ""),
#                     "editor": e.get("editor", ""),
#                     "year": e.get("year", ""),
#                     "booktitle": e.get("booktitle", ""),
#                     "journal": e.get("journal", ""),
#                     "url": e.get("url", ""),
#                     "abstract": e.get("abstract", ""),
#                 })
#         except Exception:
#             pass

# df = pd.DataFrame(rows)

# st.success(f"Parsed {len(df)} entries")

# # =====================================================
# # SEARCH & FILTER
# # =====================================================

# st.subheader("🔎 Search & Filter (within batch)")

# c1, c2, c3 = st.columns(3)

# query = c1.text_input("Search (title / abstract / author)")
# year_filter = c2.text_input("Year")
# venue_filter = c3.text_input("Venue / Booktitle")

# mask = pd.Series(True, index=df.index)

# if query:
#     q = query.lower()
#     mask &= (
#         df["title"].str.lower().str.contains(q, na=False)
#         | df["abstract"].str.lower().str.contains(q, na=False)
#         | df["author"].str.lower().str.contains(q, na=False)
#     )

# if year_filter:
#     mask &= df["year"].astype(str).str.contains(year_filter)

# if venue_filter:
#     v = venue_filter.lower()
#     mask &= (
#         df["booktitle"].str.lower().str.contains(v, na=False)
#         | df["journal"].str.lower().str.contains(v, na=False)
#     )

# filtered = df[mask]

# st.success(f"Matched {len(filtered)} entries in batch")

# # =====================================================
# # TABLE VIEW
# # =====================================================

# st.subheader("📄 Results Table")

# show_cols = st.multiselect(
#     "Columns to show",
#     options=df.columns.tolist(),
#     default=["title", "author", "year", "booktitle", "url"]
# )

# st.dataframe(filtered[show_cols], use_container_width=True)

# # =====================================================
# # ABSTRACT PREVIEW
# # =====================================================

# st.subheader("📝 Abstract Preview")

# if len(filtered) > 0:
#     idx = st.number_input(
#         "Row index in filtered table",
#         min_value=0,
#         max_value=len(filtered) - 1,
#         value=0
#     )

#     row = filtered.iloc[int(idx)]

#     st.markdown(f"### {row['title']}")
#     st.markdown(f"**Authors:** {row['author']}")
#     st.markdown(f"**Venue:** {row['booktitle'] or row['journal']}")
#     st.markdown(f"**Year:** {row['year']}")
#     st.markdown(f"**URL:** {row['url']}")
#     st.markdown("---")
#     st.write(row["abstract"])
# else:
#     st.info("No results to preview.")

# # =====================================================
# # EXPORT
# # =====================================================

# st.subheader("⬇️ Export")

# st.download_button(
#     "Download filtered CSV (current batch)",
#     filtered.to_csv(index=False).encode("utf-8"),
#     file_name=f"bibtex_batch_{start_idx}_{end_idx}_filtered.csv",
#     mime="text/csv"
# )


# import streamlit as st
# import pandas as pd
# from pathlib import Path
# import bibtexparser
# from bibtexparser.bparser import BibTexParser
# from bibtexparser.customization import convert_to_unicode
# import io

# # =====================================================
# # CONFIG
# # =====================================================

# st.set_page_config(page_title="BibTeX Abstract Search", layout="wide")
# st.title("🔍 BibTeX Abstract Search Dashboard")

# st.markdown("""
# This app loads **large BibTeX files (20–50MB+)**, parses entries, and lets you:

# - 🔎 Search in **abstract / title / author**
# - 🎯 Filter by year or venue
# - 📄 Preview matching papers
# - ⬇️ Export filtered results to CSV

# Works well with ACL Anthology full BibTeX dumps.
# """)

# # =====================================================
# # DATA INPUT
# # =====================================================

# st.sidebar.header("📥 Load BibTeX")

# DEFAULT_PATH = "data/acl_anthology/anthology+abstracts.bib"

# st.sidebar.header("📥 Load BibTeX")

# mode = st.sidebar.radio(
#     "Load mode",
#     ["Use default dataset", "Upload file", "Load from custom path"],
#     index=0
# )

# bibtex_text = None

# # ---- DEFAULT PATH MODE ----
# if mode == "Use default dataset":
#     if Path(DEFAULT_PATH).exists():
#         with st.spinner(f"Loading {DEFAULT_PATH} ..."):
#             bibtex_text = Path(DEFAULT_PATH).read_text(encoding="utf-8", errors="ignore")
#         st.sidebar.success("Loaded default ACL anthology BibTeX")
#     else:
#         st.sidebar.error(f"Default file not found: {DEFAULT_PATH}")

# # ---- UPLOAD MODE ----
# elif mode == "Upload file":
#     uploaded = st.sidebar.file_uploader("Upload .bib file", type=["bib"])
#     if uploaded:
#         bibtex_text = uploaded.read().decode("utf-8", errors="ignore")

# # ---- CUSTOM PATH MODE ----
# else:
#     path = st.sidebar.text_input("Path to .bib file", DEFAULT_PATH)
#     if path and Path(path).exists():
#         bibtex_text = Path(path).read_text(encoding="utf-8", errors="ignore")

# if mode == "Upload file":
#     uploaded = st.sidebar.file_uploader("Upload .bib file", type=["bib"])
#     if uploaded:
#         bibtex_text = uploaded.read().decode("utf-8", errors="ignore")

# else:
#     path = st.sidebar.text_input("Path to .bib file", "data/anthology.bib")
#     if path and Path(path).exists():
#         bibtex_text = Path(path).read_text(encoding="utf-8", errors="ignore")

# if not bibtex_text:
#     st.info("Select a dataset mode and load a BibTeX file to begin.")
#     st.stop()
#     st.info("Upload a BibTeX file or provide a valid path to begin.")
#     st.stop()

# # =====================================================
# # PARSE BIBTEX (FAST MODE)
# # =====================================================

# st.subheader("📚 Parsing BibTeX")

# parser = BibTexParser(common_strings=True)
# parser.customization = convert_to_unicode

# with st.spinner("Parsing entries (this may take ~10–30s for big files)..."):
#     bib_database = bibtexparser.loads(bibtex_text, parser=parser)

# entries = bib_database.entries

# st.success(f"Loaded {len(entries)} BibTeX entries")

# # =====================================================
# # TO DATAFRAME
# # =====================================================

# rows = []

# for e in entries:
#     rows.append({
#         "id": e.get("ID", ""),
#         "type": e.get("ENTRYTYPE", ""),
#         "title": e.get("title", ""),
#         "author": e.get("author", ""),
#         "editor": e.get("editor", ""),
#         "year": e.get("year", ""),
#         "booktitle": e.get("booktitle", ""),
#         "journal": e.get("journal", ""),
#         "url": e.get("url", ""),
#         "abstract": e.get("abstract", ""),
#     })

# df = pd.DataFrame(rows)

# # =====================================================
# # SEARCH & FILTER
# # =====================================================

# st.subheader("🔎 Search & Filters")

# c1, c2, c3 = st.columns(3)

# query = c1.text_input("Search (title / abstract / author)")
# year_filter = c2.text_input("Year (optional)")
# venue_filter = c3.text_input("Venue / Booktitle contains")

# mask = pd.Series(True, index=df.index)

# if query:
#     q = query.lower()
#     mask &= (
#         df["title"].str.lower().str.contains(q, na=False)
#         | df["abstract"].str.lower().str.contains(q, na=False)
#         | df["author"].str.lower().str.contains(q, na=False)
#     )

# if year_filter:
#     mask &= df["year"].astype(str).str.contains(year_filter)

# if venue_filter:
#     v = venue_filter.lower()
#     mask &= (
#         df["booktitle"].str.lower().str.contains(v, na=False)
#         | df["journal"].str.lower().str.contains(v, na=False)
#     )

# filtered = df[mask]

# st.success(f"Matched {len(filtered)} entries")

# # =====================================================
# # RESULTS VIEW
# # =====================================================

# st.subheader("📄 Results")

# show_cols = st.multiselect(
#     "Columns to show",
#     options=df.columns.tolist(),
#     default=["title", "author", "year", "booktitle", "url"]
# )

# st.dataframe(filtered[show_cols], use_container_width=True)

# # =====================================================
# # ABSTRACT PREVIEW
# # =====================================================

# st.subheader("📝 Abstract Preview")

# idx = st.number_input(
#     "Row index in filtered table",
#     min_value=0,
#     max_value=max(len(filtered) - 1, 0),
#     value=0
# )

# if len(filtered) > 0:
#     row = filtered.iloc[int(idx)]
#     st.markdown(f"### {row['title']}")
#     st.markdown(f"**Authors:** {row['author']}")
#     st.markdown(f"**Venue:** {row['booktitle'] or row['journal']}")
#     st.markdown(f"**Year:** {row['year']}")
#     st.markdown(f"**URL:** {row['url']}")
#     st.markdown("---")
#     st.write(row["abstract"])

# # =====================================================
# # EXPORT
# # =====================================================

# st.subheader("⬇️ Export")

# st.download_button(
#     "Download filtered CSV",
#     filtered.to_csv(index=False).encode("utf-8"),
#     file_name="bibtex_filtered.csv",
#     mime="text/csv"
# )


# import streamlit as st
# import pandas as pd
# from pathlib import Path
# import bibtexparser
# from bibtexparser.bparser import BibTexParser
# from bibtexparser.customization import convert_to_unicode
# import io

# # =====================================================
# # CONFIG
# # =====================================================

# st.set_page_config(page_title="BibTeX Abstract Search", layout="wide")
# st.title("🔍 BibTeX Abstract Search Dashboard")

# st.markdown("""
# This app loads **large BibTeX files (20–50MB+)**, parses entries, and lets you:

# - 🔎 Search in **abstract / title / author**
# - 🎯 Filter by year or venue
# - 📄 Preview matching papers
# - ⬇️ Export filtered results to CSV

# Works well with ACL Anthology full BibTeX dumps.
# """)

# # =====================================================
# # DATA INPUT
# # =====================================================

# st.sidebar.header("📥 Load BibTeX")

# mode = st.sidebar.radio("Load mode", ["Upload file", "Load from path"])

# bibtex_text = None

# if mode == "Upload file":
#     uploaded = st.sidebar.file_uploader("Upload .bib file", type=["bib"])
#     if uploaded:
#         bibtex_text = uploaded.read().decode("utf-8", errors="ignore")

# else:
#     path = st.sidebar.text_input("Path to .bib file", "data/anthology.bib")
#     if path and Path(path).exists():
#         bibtex_text = Path(path).read_text(encoding="utf-8", errors="ignore")

# if not bibtex_text:
#     st.info("Upload a BibTeX file or provide a valid path to begin.")
#     st.stop()

# # =====================================================
# # PARSE BIBTEX (FAST MODE)
# # =====================================================

# st.subheader("📚 Parsing BibTeX")

# parser = BibTexParser(common_strings=True)
# parser.customization = convert_to_unicode

# with st.spinner("Parsing entries (this may take ~10–30s for big files)..."):
#     bib_database = bibtexparser.loads(bibtex_text, parser=parser)

# entries = bib_database.entries

# st.success(f"Loaded {len(entries)} BibTeX entries")

# # =====================================================
# # TO DATAFRAME
# # =====================================================

# rows = []

# for e in entries:
#     rows.append({
#         "id": e.get("ID", ""),
#         "type": e.get("ENTRYTYPE", ""),
#         "title": e.get("title", ""),
#         "author": e.get("author", ""),
#         "editor": e.get("editor", ""),
#         "year": e.get("year", ""),
#         "booktitle": e.get("booktitle", ""),
#         "journal": e.get("journal", ""),
#         "url": e.get("url", ""),
#         "abstract": e.get("abstract", ""),
#     })

# df = pd.DataFrame(rows)

# # =====================================================
# # SEARCH & FILTER
# # =====================================================

# st.subheader("🔎 Search & Filters")

# c1, c2, c3 = st.columns(3)

# query = c1.text_input("Search (title / abstract / author)")
# year_filter = c2.text_input("Year (optional)")
# venue_filter = c3.text_input("Venue / Booktitle contains")

# mask = pd.Series(True, index=df.index)

# if query:
#     q = query.lower()
#     mask &= (
#         df["title"].str.lower().str.contains(q, na=False)
#         | df["abstract"].str.lower().str.contains(q, na=False)
#         | df["author"].str.lower().str.contains(q, na=False)
#     )

# if year_filter:
#     mask &= df["year"].astype(str).str.contains(year_filter)

# if venue_filter:
#     v = venue_filter.lower()
#     mask &= (
#         df["booktitle"].str.lower().str.contains(v, na=False)
#         | df["journal"].str.lower().str.contains(v, na=False)
#     )

# filtered = df[mask]

# st.success(f"Matched {len(filtered)} entries")

# # =====================================================
# # RESULTS VIEW
# # =====================================================

# st.subheader("📄 Results")

# show_cols = st.multiselect(
#     "Columns to show",
#     options=df.columns.tolist(),
#     default=["title", "author", "year", "booktitle", "url"]
# )

# st.dataframe(filtered[show_cols], use_container_width=True)

# # =====================================================
# # ABSTRACT PREVIEW
# # =====================================================

# st.subheader("📝 Abstract Preview")

# idx = st.number_input(
#     "Row index in filtered table",
#     min_value=0,
#     max_value=max(len(filtered) - 1, 0),
#     value=0
# )

# if len(filtered) > 0:
#     row = filtered.iloc[int(idx)]
#     st.markdown(f"### {row['title']}")
#     st.markdown(f"**Authors:** {row['author']}")
#     st.markdown(f"**Venue:** {row['booktitle'] or row['journal']}")
#     st.markdown(f"**Year:** {row['year']}")
#     st.markdown(f"**URL:** {row['url']}")
#     st.markdown("---")
#     st.write(row["abstract"])

# # =====================================================
# # EXPORT
# # =====================================================

# st.subheader("⬇️ Export")

# st.download_button(
#     "Download filtered CSV",
#     filtered.to_csv(index=False).encode("utf-8"),
#     file_name="bibtex_filtered.csv",
#     mime="text/csv"
# )
