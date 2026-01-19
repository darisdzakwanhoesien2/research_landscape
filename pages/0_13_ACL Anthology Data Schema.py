import streamlit as st
import pandas as pd
import re
from pathlib import Path

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="ACL Abstract Explorer", layout="wide")
st.title("📚 ACL Bib Abstract Explorer (Upload Master Bib)")
st.caption("Venue bib + uploaded anthology+abstracts.bib (local join, no web scraping)")

BASE_DIR = Path(__file__).resolve().parents[1]
VENUE_DIR = BASE_DIR / "data" / "acl_anthology_new"

# =====================================================
# HELPERS
# =====================================================

def parse_bib_entries(text):
    entries = re.split(r'\n@', text)
    records = []

    for i, raw in enumerate(entries):
        body = raw if i == 0 else "@" + raw

        def get_field(name):
            m = re.search(rf'{name}\s*=\s*\{{([\s\S]*?)\}}', body, re.I)
            if not m:
                m = re.search(rf'{name}\s*=\s*"([\s\S]*?)"', body, re.I)
            return m.group(1).replace("\n", " ").strip() if m else ""

        url = get_field("url")

        acl_id = ""
        if "aclanthology.org/" in url:
            acl_id = url.split("aclanthology.org/")[-1].strip("/")

        records.append({
            "title": get_field("title"),
            "url": url,
            "acl_id": acl_id,
            "doi": get_field("doi"),
            "abstract": get_field("abstract"),
        })

    return pd.DataFrame(records)


@st.cache_data(show_spinner=True)
def build_master_lookup_from_upload(file_bytes):
    text = file_bytes.decode("utf-8", errors="ignore")
    df = parse_bib_entries(text)

    lookup = {}
    for _, r in df.iterrows():
        if r["acl_id"]:
            lookup[r["acl_id"]] = {
                "abstract": r["abstract"],
                "doi": r["doi"],
            }
    return lookup


# =====================================================
# STEP 1 — UPLOAD MASTER BIB
# =====================================================

st.subheader("📤 Upload Master Bib (anthology+abstracts.bib)")

master_file = st.file_uploader(
    "Upload anthology+abstracts.bib (large file, ~150MB)",
    type=["bib"],
    key="masterbib"
)

if not master_file:
    st.warning("Please upload anthology+abstracts.bib to enable abstract resolution.")
    st.stop()

# Build lookup once
with st.spinner("Indexing master abstract database (first time only)..."):
    MASTER_LOOKUP = build_master_lookup_from_upload(master_file.getvalue())

st.success(f"Master DB loaded: {len(MASTER_LOOKUP):,} papers indexed")

# =====================================================
# STEP 2 — VENUE DROPDOWN
# =====================================================

st.divider()
st.subheader("📁 Select ACL Venue Bib File")

if not VENUE_DIR.exists():
    st.error(f"Venue directory not found: {VENUE_DIR}")
    st.stop()

venue_files = sorted(VENUE_DIR.glob("*.bib"))

selected_bib = st.selectbox(
    "Venue Bib File",
    venue_files,
    format_func=lambda p: p.name
)

st.caption(f"Source: `{selected_bib.relative_to(BASE_DIR)}`")

# =====================================================
# STEP 3 — PARSE VENUE
# =====================================================

text = selected_bib.read_text(encoding="utf-8", errors="ignore")
df = parse_bib_entries(text)

# =====================================================
# STEP 4 — LOCAL JOIN
# =====================================================

st.divider()
st.subheader("🔗 Resolving Abstracts from Master Bib")

progress = st.progress(0)
status = st.empty()

abstracts = []
dois = []

for i, row in df.iterrows():
    abs_val = row["abstract"]
    doi_val = row["doi"]

    if row["acl_id"] in MASTER_LOOKUP:
        master = MASTER_LOOKUP[row["acl_id"]]
        abs_val = abs_val or master["abstract"]
        doi_val = doi_val or master["doi"]

    abstracts.append(abs_val)
    dois.append(doi_val)

    progress.progress((i + 1) / len(df))
    status.text(f"Resolving {i+1}/{len(df)}")

df["abstract"] = abstracts
df["doi"] = dois

status.text("Done.")

# =====================================================
# METRICS
# =====================================================

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total papers", len(df))
col2.metric("With Abstract", df["abstract"].str.len().gt(30).sum())
col3.metric("With DOI", df["doi"].astype(str).str.len().gt(5).sum())
col4.metric("Matched in Master DB", df["acl_id"].isin(MASTER_LOOKUP).sum())

# =====================================================
# TABLE
# =====================================================

st.subheader("📄 Extracted Records (Selected Venue Only)")

st.dataframe(
    df[["title", "doi", "abstract"]],
    use_container_width=True,
    height=600
)

# =====================================================
# DOWNLOAD
# =====================================================

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download Enriched CSV",
    data=csv,
    file_name=selected_bib.stem + "_with_abstracts.csv",
    mime="text/csv"
)



# import streamlit as st
# import pandas as pd
# import re
# from io import StringIO

# # =====================================================
# # CONFIG
# # =====================================================

# st.set_page_config(page_title="Large Bib Abstract Extractor", layout="wide")
# st.title("📚 Large BibTeX Abstract & DOI Extractor")
# st.caption("Upload large .bib files (100MB+) and extract Title, Abstract, DOI")

# # =====================================================
# # UPLOAD
# # =====================================================

# uploaded_files = st.file_uploader(
#     "Upload one or more .bib files (large files supported)",
#     type=["bib"],
#     accept_multiple_files=True
# )

# # =====================================================
# # HELPERS
# # =====================================================

# def parse_bib_stream(text, progress_cb=None):
#     """
#     Parse bib file entry-by-entry to avoid heavy regex on full file.
#     """

#     records = []

#     entries = re.split(r'\n@', text)
#     total = len(entries)

#     for i, raw in enumerate(entries):
#         if i == 0:
#             body = raw
#         else:
#             body = "@" + raw

#         def get_field(name):
#             m = re.search(rf'{name}\s*=\s*\{{([\s\S]*?)\}}', body, re.I)
#             if not m:
#                 m = re.search(rf'{name}\s*=\s*"([\s\S]*?)"', body, re.I)
#             return m.group(1).replace("\n", " ").strip() if m else ""

#         title = get_field("title")
#         abstract = get_field("abstract")
#         doi = get_field("doi")

#         if not doi:
#             url = get_field("url")
#             if "doi.org" in url:
#                 doi = url.split("doi.org/")[-1]

#         if title or abstract or doi:
#             records.append({
#                 "title": title,
#                 "doi": doi,
#                 "abstract": abstract
#             })

#         if progress_cb:
#             progress_cb(i + 1, total)

#     return pd.DataFrame(records)


# # =====================================================
# # PROCESS
# # =====================================================

# if uploaded_files:

#     all_dfs = []

#     for file in uploaded_files:

#         st.subheader(f"📄 Processing: {file.name}")

#         progress = st.progress(0)
#         status = st.empty()

#         # Read safely (no decode crash)
#         text = file.read().decode("utf-8", errors="ignore")

#         def update(i, total):
#             progress.progress(i / total)
#             status.text(f"Entries parsed: {i} / {total}")

#         df = parse_bib_stream(text, update)

#         st.success(f"Extracted {len(df)} records from {file.name}")
#         all_dfs.append(df)

#     # =================================================
#     # MERGE
#     # =================================================

#     final_df = pd.concat(all_dfs, ignore_index=True)

#     st.divider()
#     st.subheader("📊 Combined Results")

#     col1, col2, col3 = st.columns(3)
#     col1.metric("Total entries", len(final_df))
#     col2.metric("With DOI", (final_df["doi"] != "").sum())
#     col3.metric("With Abstract", (final_df["abstract"] != "").sum())

#     st.dataframe(final_df, use_container_width=True, height=600)

#     # =================================================
#     # DOWNLOAD
#     # =================================================

#     csv = final_df.to_csv(index=False).encode("utf-8")

#     st.download_button(
#         "⬇️ Download Extracted Data (CSV)",
#         data=csv,
#         file_name="bib_abstracts_combined.csv",
#         mime="text/csv"
#     )


# import streamlit as st
# from pathlib import Path
# import re
# import pandas as pd

# # =====================================================
# # CONFIG
# # =====================================================

# st.set_page_config(page_title="Bib Abstract Viewer", layout="wide")
# st.title("📚 Bib File Abstract Explorer")
# st.caption("Select a .bib file and view Title, DOI, and Abstract")

# BASE_DIR = Path(__file__).resolve().parents[1]
# BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"

# if not BIB_DIR.exists():
#     st.error(f"❌ Directory not found: {BIB_DIR}")
#     st.stop()

# # =====================================================
# # HELPERS
# # =====================================================

# def parse_bib_entries(text: str):
#     """
#     Very lightweight BibTeX parser:
#     Extracts title, doi, abstract per entry.
#     """
#     entries = re.findall(r'@.+?\{[^,]+,(.*?)\n\}', text, flags=re.S)

#     records = []

#     for body in entries:
#         def get_field(name):
#             m = re.search(rf'{name}\s*=\s*\{{([\s\S]*?)\}}', body, re.I)
#             if not m:
#                 m = re.search(rf'{name}\s*=\s*"([\s\S]*?)"', body, re.I)
#             return m.group(1).replace("\n", " ").strip() if m else ""

#         title = get_field("title")
#         doi = get_field("doi")
#         abstract = get_field("abstract")

#         if title or doi or abstract:
#             records.append({
#                 "title": title,
#                 "doi": doi,
#                 "abstract": abstract
#             })

#     return pd.DataFrame(records)


# # =====================================================
# # FILE DROPDOWN
# # =====================================================

# bib_files = sorted(BIB_DIR.glob("*.bib"))

# if not bib_files:
#     st.warning("⚠️ No .bib files found in directory.")
#     st.stop()

# selected_file = st.selectbox(
#     "Select BibTeX file",
#     options=bib_files,
#     format_func=lambda p: p.name
# )

# st.caption(f"Source: `{selected_file.relative_to(BASE_DIR)}`")

# # =====================================================
# # LOAD & PARSE
# # =====================================================

# with st.spinner("Parsing BibTeX file..."):
#     text = selected_file.read_text(encoding="utf-8", errors="ignore")
#     df = parse_bib_entries(text)

# # =====================================================
# # DISPLAY
# # =====================================================

# st.subheader("📄 Extracted Records")

# col1, col2, col3 = st.columns(3)
# col1.metric("Total entries", len(df))
# col2.metric("With DOI", (df["doi"] != "").sum())
# col3.metric("With Abstract", (df["abstract"] != "").sum())

# st.dataframe(df, use_container_width=True, height=500)

# # =====================================================
# # DOWNLOAD
# # =====================================================

# csv_data = df.to_csv(index=False).encode("utf-8")

# st.download_button(
#     "⬇️ Download as CSV",
#     data=csv_data,
#     file_name=selected_file.stem + "_abstracts.csv",
#     mime="text/csv"
# )
