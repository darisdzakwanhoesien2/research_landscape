import streamlit as st
from pathlib import Path
import tempfile
import re
import bibtexparser

# ======================================
# PAGE CONFIG
# ======================================
st.set_page_config(layout="wide")
st.title("📚 AUX → Filter BibTeX References")

st.markdown("""
Upload:
- ✅ One or more **`.aux` files**
- ✅ One or more **`.bib` files**

The app will:
1. Extract citation keys from AUX files  
2. Find matching BibTeX entries  
3. Display matched references  
4. Export a filtered `.bib` file  
""")

# ======================================
# HELPERS
# ======================================

def extract_citation_keys_from_aux(aux_text: str) -> set:
    """
    Extract citation keys from \\citation{...} and \\bibcite{...}
    """
    keys = set()

    # \citation{key1,key2}
    citation_matches = re.findall(r"\\citation\{([^}]+)\}", aux_text)
    for block in citation_matches:
        for k in block.split(","):
            keys.add(k.strip())

    # \bibcite{key}{...}
    bibcite_matches = re.findall(r"\\bibcite\{([^}]+)\}", aux_text)
    for k in bibcite_matches:
        keys.add(k.strip())

    return keys


def load_bib_entries(bib_file) -> list:
    db = bibtexparser.load(bib_file)
    return db.entries


def write_filtered_bib(entries: list) -> str:
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = entries
    writer = bibtexparser.bwriter.BibTexWriter()
    return writer.write(db)


# ======================================
# UPLOAD FILES
# ======================================

col1, col2 = st.columns(2)

with col1:
    aux_files = st.file_uploader(
        "📄 Upload AUX files",
        type=["aux"],
        accept_multiple_files=True
    )

with col2:
    bib_files = st.file_uploader(
        "📘 Upload BIB files",
        type=["bib"],
        accept_multiple_files=True
    )

if not aux_files or not bib_files:
    st.info("Please upload at least one AUX file and one BIB file.")
    st.stop()

# ======================================
# PROCESS AUX FILES
# ======================================

all_citation_keys = set()

with st.expander("📄 Parsed AUX Files", expanded=False):
    for aux in aux_files:
        aux_text = aux.read().decode("utf-8", errors="ignore")
        keys = extract_citation_keys_from_aux(aux_text)
        all_citation_keys.update(keys)

        st.write(f"**{aux.name}** → {len(keys)} citations")
        st.code(sorted(keys))

st.success(f"🔑 Total unique citation keys found: {len(all_citation_keys)}")

# ======================================
# LOAD BIB FILES
# ======================================

all_bib_entries = []
bib_source_map = {}

for bib in bib_files:
    entries = load_bib_entries(bib)
    for e in entries:
        e["_source_bib"] = bib.name
        all_bib_entries.append(e)
        bib_source_map.setdefault(bib.name, 0)
        bib_source_map[bib.name] += 1

st.info(f"📘 Loaded {len(all_bib_entries)} BibTeX entries from {len(bib_files)} files.")

# ======================================
# MATCH REFERENCES
# ======================================

matched = []
missing = []

for key in sorted(all_citation_keys):
    found = False
    for entry in all_bib_entries:
        if entry.get("ID") == key:
            matched.append(entry)
            found = True
            break
    if not found:
        missing.append(key)

# ======================================
# RESULTS
# ======================================

c1, c2 = st.columns(2)

with c1:
    st.subheader("✅ Matched References")
    st.metric("Matched", len(matched))

    if matched:
        for e in matched:
            st.markdown(
                f"""
**{e.get('ID')}**  
- Title: {e.get('title', 'N/A')}  
- Author: {e.get('author', 'N/A')}  
- Year: {e.get('year', 'N/A')}  
- Source: `{e.get('_source_bib')}`
---
"""
            )

with c2:
    st.subheader("⚠️ Missing References")
    st.metric("Missing", len(missing))

    if missing:
        st.code(missing)

# ======================================
# EXPORT FILTERED BIB
# ======================================

if matched:
    filtered_bib_text = write_filtered_bib(matched)

    st.download_button(
        label="⬇️ Download Filtered BibTeX",
        data=filtered_bib_text,
        file_name="filtered_references.bib",
        mime="text/plain"
    )

# ======================================
# OPTIONAL: RAW BIB PREVIEW
# ======================================

with st.expander("📦 Preview Filtered BibTeX"):
    st.code(filtered_bib_text if matched else "No matched entries.")
