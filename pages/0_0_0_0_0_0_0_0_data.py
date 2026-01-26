import streamlit as st
import pandas as pd
from pathlib import Path
import bibtexparser
import re

# ===============================
# CONFIG
# ===============================

BASE_DIR = Path(__file__).resolve().parents[1]

LITMAP_DIR = BASE_DIR / "data" / "litmap_paper"
BIB_DIR = BASE_DIR / "data" / "bib_paper"
AUX_DIR = BASE_DIR / "data" / "aux_paper"
PDF_DIR = BASE_DIR / "data" / "pdf_paper"

st.set_page_config(layout="wide")
st.title("📚 Academic Resource Mapper")

# ===============================
# LOADERS
# ===============================

@st.cache_data
def load_litmap():
    dfs = []
    for csv in LITMAP_DIR.glob("*.csv"):
        df = pd.read_csv(csv)
        df["_source"] = csv.name
        dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

@st.cache_data
def load_bib_files():
    entries = []
    for bib_file in BIB_DIR.glob("*.bib"):
        with open(bib_file, encoding="utf-8") as f:
            db = bibtexparser.load(f)
            for e in db.entries:
                e["_source_bib"] = bib_file.name
                entries.append(e)
    return pd.DataFrame(entries)

def extract_aux_citations(aux_path):
    text = aux_path.read_text(errors="ignore")
    keys = re.findall(r"\\citation\{([^}]+)\}", text)
    flat_keys = set()
    for group in keys:
        for k in group.split(","):
            flat_keys.add(k.strip())
    return sorted(flat_keys)

# ===============================
# LOAD DATA
# ===============================

litmap_df = load_litmap()
bib_df = load_bib_files()

aux_files = sorted(AUX_DIR.glob("*.aux"))
pdf_files = sorted(PDF_DIR.glob("*.pdf"))

# ===============================
# UI - FILE SELECTION
# ===============================

st.sidebar.header("📂 Resource Selection")

selected_aux = st.sidebar.selectbox(
    "Select AUX file",
    aux_files,
    format_func=lambda p: p.name
)

linked_pdf = PDF_DIR / selected_aux.with_suffix(".pdf").name

st.sidebar.markdown("### Linked PDF")
if linked_pdf.exists():
    st.sidebar.success(linked_pdf.name)
else:
    st.sidebar.warning("No matching PDF found")

# ===============================
# EXTRACT CITATIONS
# ===============================

citation_keys = extract_aux_citations(selected_aux)

st.subheader("📑 Extracted Citations")
st.write(f"Found **{len(citation_keys)}** citation keys")

st.dataframe(pd.DataFrame({"citation_key": citation_keys}), height=200)

# ===============================
# RESOLVE BIB ENTRIES
# ===============================

resolved_bib = bib_df[bib_df["ID"].isin(citation_keys)].copy()
missing_keys = sorted(set(citation_keys) - set(resolved_bib["ID"]))

st.subheader("📚 Resolved Bib Entries")

if not resolved_bib.empty:
    st.dataframe(
        resolved_bib[["ID", "title", "author", "year", "_source_bib"]],
        height=300
    )
else:
    st.warning("No Bib entries matched.")

if missing_keys:
    st.error(f"⚠️ Missing Bib entries: {missing_keys}")

# ===============================
# MAP TO LITMAP
# ===============================

def normalize(text):
    return str(text).lower()

def map_to_litmap(bib_row, litmap_df):
    title = normalize(bib_row.get("title", ""))
    matches = []

    for _, row in litmap_df.iterrows():
        keywords = normalize(row.get("keywords", ""))
        if any(k in title for k in keywords.split(",")):
            matches.append(row)

    return pd.DataFrame(matches)

st.subheader("🧭 Litmap Mapping")

mapped_rows = []

for _, bib_row in resolved_bib.iterrows():
    mapped = map_to_litmap(bib_row, litmap_df)
    if not mapped.empty:
        mapped["citation_key"] = bib_row["ID"]
        mapped["paper_title"] = bib_row.get("title")
        mapped_rows.append(mapped)

if mapped_rows:
    mapped_df = pd.concat(mapped_rows, ignore_index=True)
    st.dataframe(mapped_df, height=350)
else:
    st.info("No Litmap matches found.")

# ===============================
# COVERAGE ANALYTICS
# ===============================

st.subheader("📊 Coverage Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Citations", len(citation_keys))
col2.metric("Resolved Bib", len(resolved_bib))
col3.metric("Mapped to Litmap", len(mapped_df) if mapped_rows else 0)

# ===============================
# EXPORT
# ===============================

if mapped_rows:
    export_path = BASE_DIR / "outputs" / f"{selected_aux.stem}_mapping.csv"
    export_path.parent.mkdir(exist_ok=True)

    mapped_df.to_csv(export_path, index=False)

    st.success(f"Mapping saved to: {export_path}")
