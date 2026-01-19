import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.title("🧼 Clean, Enrich & Download Dataset")

if "raw_df" not in st.session_state:
    st.warning("Please upload a file first in Page 1.")
    st.stop()

df = st.session_state["raw_df"].copy()

# =========================================================
# STEP 1 — Keep relevant ACL columns
# =========================================================

keep_cols = [
    c for c in df.columns
    if (
        "badge" in c.lower()
        or "align-middle" in c.lower()
        or "card" in c.lower()
        or c.lower().startswith("d-block")
    )
]

df = df[keep_cols]

st.subheader("Kept Columns")
st.code(keep_cols)

# =========================================================
# STEP 2 — Detect abstract-only rows
# =========================================================

first_col = df.columns[0]
last_col = df.columns[-1]

df["__is_abstract__"] = df[first_col].isna() & df[last_col].notna()

# =========================================================
# STEP 3 — Merge abstract rows upward
# =========================================================

rows = []
current_abstract = ""

for _, row in df.iterrows():
    if row["__is_abstract__"]:
        current_abstract += " " + str(row[last_col])
    else:
        if current_abstract and rows:
            rows[-1]["abstract"] = current_abstract.strip()
            current_abstract = ""

        r = row.to_dict()
        r["abstract"] = ""
        rows.append(r)

clean = pd.DataFrame(rows)

# =========================================================
# STEP 4 — Extract Title (align-middle / card-body)
# =========================================================

title_cols = [
    c for c in clean.columns
    if "align-middle" in c.lower() or "card" in c.lower()
]

def get_title(row):
    for c in title_cols:
        v = row.get(c)
        if isinstance(v, str) and len(v) > 10:
            return v.strip()
    return ""

clean["title"] = clean.apply(get_title, axis=1)

# =========================================================
# STEP 5 — Extract Authors
# =========================================================

author_cols = [
    c for c in clean.columns
    if c.lower().startswith("d-block") and "href" not in c.lower()
]

def collect_authors(row):
    names = []
    for c in author_cols:
        v = row.get(c)
        if isinstance(v, str) and 2 < len(v) < 60:
            names.append(v.strip())
    return ", ".join(names)

clean["authors"] = clean.apply(collect_authors, axis=1)

# =========================================================
# STEP 6 — Extract PDF & Bib URLs
# =========================================================

pdf_col = next((c for c in clean.columns if c.lower() == "badge href"), None)
bib_col = next((c for c in clean.columns if c.lower() == "badge href 2"), None)

clean["pdf"] = clean[pdf_col] if pdf_col else None
clean["bib_url"] = clean[bib_col] if bib_col else None

# =========================================================
# STEP 7 — Fetch BibTeX entries
# =========================================================

st.subheader("Fetching BibTeX entries")

bibtex_entries = []
bib_errors = 0

progress = st.progress(0)

for i, url in enumerate(clean["bib_url"]):
    if isinstance(url, str) and url.startswith("http"):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                bibtex_entries.append(r.text.strip())
            else:
                bib_errors += 1
        except Exception:
            bib_errors += 1
    progress.progress((i + 1) / len(clean))

combined_bibtex = "\n\n".join(bibtex_entries)

st.success(f"Fetched {len(bibtex_entries)} BibTeX entries | Errors: {bib_errors}")

# =========================================================
# STEP 8 — Build Markdown Literature File
# =========================================================

md_blocks = []

for _, row in clean.iterrows():
    md = f"""### {row['title']}

**Authors:** {row['authors']}  
**PDF:** {row['pdf']}  
**BibTeX:** {row['bib_url']}

**Abstract:**  
{row['abstract']}

---
"""
    md_blocks.append(md)

combined_md = "\n".join(md_blocks)

# =========================================================
# STEP 9 — Final Clean CSV
# =========================================================

final = pd.DataFrame({
    "title": clean["title"],
    "authors": clean["authors"],
    "pdf": clean["pdf"],
    "bib_url": clean["bib_url"],
    "abstract": clean["abstract"],
})

final = final.dropna(subset=["title"])

# =========================================================
# DISPLAY
# =========================================================

st.subheader("Preview Clean Dataset")
st.dataframe(final.head(20))

# =========================================================
# DOWNLOADS
# =========================================================

st.subheader("Downloads")

st.download_button(
    "⬇️ Download Clean CSV",
    final.to_csv(index=False).encode("utf-8"),
    file_name="acl_clean.csv",
    mime="text/csv"
)

st.download_button(
    "⬇️ Download Combined BibTeX",
    combined_bibtex.encode("utf-8"),
    file_name="acl_combined.bib",
    mime="text/plain"
)

st.download_button(
    "⬇️ Download Combined Markdown",
    combined_md.encode("utf-8"),
    file_name="acl_literature.md",
    mime="text/markdown"
)


# import streamlit as st
# import pandas as pd

# st.title("🧼 Clean & Download CSV")

# if "raw_df" not in st.session_state:
#     st.warning("Please upload a file first in Page 1.")
#     st.stop()

# df = st.session_state["raw_df"].copy()

# # =========================================================
# # STEP 1 — Keep only relevant columns
# # =========================================================

# keep_cols = [
#     c for c in df.columns
#     if (
#         "badge" in c.lower()
#         or "card" in c.lower()
#         or c.lower().startswith("d-block")
#     )
# ]

# df = df[keep_cols]

# st.write("Kept columns:")
# st.code(keep_cols)

# # =========================================================
# # STEP 2 — Detect abstract-only rows
# # =========================================================

# first_col = df.columns[0]
# last_col = df.columns[-1]

# df["__is_abstract__"] = df[first_col].isna() & df[last_col].notna()

# # =========================================================
# # STEP 3 — Merge abstract rows upward
# # =========================================================

# rows = []
# current_abstract = ""

# for _, row in df.iterrows():
#     if row["__is_abstract__"]:
#         current_abstract += " " + str(row[last_col])
#     else:
#         if current_abstract and rows:
#             rows[-1]["abstract"] = current_abstract.strip()
#             current_abstract = ""

#         r = row.to_dict()
#         r["abstract"] = ""
#         rows.append(r)

# clean = pd.DataFrame(rows)

# # =========================================================
# # STEP 4 — Extract authors
# # =========================================================

# author_cols = [
#     c for c in clean.columns
#     if c.lower().startswith("d-block") and "href" not in c.lower()
# ]

# def collect_authors(row):
#     names = []
#     for c in author_cols:
#         v = row.get(c)
#         if isinstance(v, str) and 2 < len(v) < 60:
#             names.append(v.strip())
#     return ", ".join(names)

# clean["authors"] = clean.apply(collect_authors, axis=1)

# # =========================================================
# # STEP 5 — Extract title
# # =========================================================

# def get_title(row):
#     for c in author_cols:
#         v = row.get(c)
#         if isinstance(v, str) and len(v) > 40:
#             return v.strip()
#     return ""

# clean["title"] = clean.apply(get_title, axis=1)

# # =========================================================
# # STEP 6 — Final schema
# # =========================================================

# pdf_col = next((c for c in clean.columns if "badge href" in c.lower()), None)
# bib_col = next((c for c in clean.columns if "badge href 2" in c.lower()), None)

# final = pd.DataFrame({
#     "pdf": clean[pdf_col] if pdf_col else None,
#     "bib": clean[bib_col] if bib_col else None,
#     "title": clean["title"],
#     "authors": clean["authors"],
#     "abstract": clean["abstract"],
# })

# final = final.dropna(subset=["title"])

# # =========================================================
# # DISPLAY
# # =========================================================

# st.success(f"Cleaned dataset: {final.shape[0]} papers")

# st.subheader("Preview Clean Data")
# st.dataframe(final.head(20))

# # =========================================================
# # DOWNLOAD
# # =========================================================

# csv = final.to_csv(index=False).encode("utf-8")

# st.download_button(
#     "⬇️ Download Clean CSV",
#     data=csv,
#     file_name="acl_clean.csv",
#     mime="text/csv"
# )
