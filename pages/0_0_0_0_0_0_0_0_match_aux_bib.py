import streamlit as st
import re
from typing import Dict, List

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AUX → ACL Anthology Exact BibTeX",
    layout="wide"
)

st.title("📚 AUX → ACL Anthology–Exact BibTeX Generator")

st.markdown("""
✔ Robust against malformed BibTeX  
✔ Ignores @comment / @string / @preamble  
✔ Preserves AUX citation order  
✔ Outputs **ACL Anthology–exact BibTeX**
""")

# =========================================================
# AUX PARSING
# =========================================================

def extract_citation_keys_from_aux(aux_text: str) -> List[str]:
    keys = []

    for block in re.findall(r"\\citation\{([^}]+)\}", aux_text):
        for k in block.split(","):
            keys.append(k.strip())

    for k in re.findall(r"\\bibcite\{([^}]+)\}", aux_text):
        keys.append(k.strip())

    # preserve order
    seen = set()
    ordered = []
    for k in keys:
        if k and k not in seen:
            ordered.append(k)
            seen.add(k)

    return ordered

# =========================================================
# SAFE BIBTEX PARSER (NO CRASH)
# =========================================================

def split_bibtex_entries(text: str) -> List[str]:
    """
    Splits BibTeX text into entry blocks using brace balancing.
    Safely ignores comments and malformed sections.
    """
    entries = []
    i = 0
    n = len(text)

    while i < n:
        if text[i] == "@":
            start = i
            brace_level = 0
            i += 1

            while i < n:
                if text[i] == "{":
                    brace_level += 1
                elif text[i] == "}":
                    brace_level -= 1
                    if brace_level == 0:
                        entries.append(text[start:i + 1])
                        break
                i += 1
        i += 1

    return entries


def parse_single_bibtex_entry(entry: str):
    """
    Parse one BibTeX entry safely.
    Returns None for @comment, @string, malformed entries.
    """
    entry = entry.strip()

    if not entry.startswith("@"):
        return None

    header_match = re.match(r"@(\w+)\s*\{\s*([^,]+)\s*,", entry)
    if not header_match:
        return None

    entry_type, entry_id = header_match.groups()

    if entry_type.lower() in {"comment", "string", "preamble"}:
        return None

    body = entry[header_match.end():].rstrip("}").strip()

    fields = {}
    for match in re.finditer(
        r"(\w+)\s*=\s*({(?:[^{}]|{[^}]*})*}|\"[^\"]*\"|[^,]+)",
        body,
        re.S
    ):
        field, value = match.groups()
        value = value.strip().rstrip(",")

        if value.startswith("{") and value.endswith("}"):
            value = value[1:-1]
        elif value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        fields[field.lower()] = value

    return {
        "ENTRYTYPE": entry_type,
        "ID": entry_id,
        **fields
    }


def parse_bibtex_entries(text: str) -> Dict[str, Dict]:
    index = {}
    for raw in split_bibtex_entries(text):
        parsed = parse_single_bibtex_entry(raw)
        if parsed:
            index[parsed["ID"]] = parsed
    return index

# =========================================================
# ACL-EXACT FORMATTER
# =========================================================

ACL_FIELD_ORDER = [
    "title",
    "author",
    "editor",
    "booktitle",
    "month",
    "year",
    "address",
    "publisher",
    "url",
    "pages",
    "isbn",
    "abstract",
]

def format_acl_entry(entry: Dict) -> str:
    lines = [f"@{entry['ENTRYTYPE']}{{{entry['ID']},"]
    for field in ACL_FIELD_ORDER:
        if field not in entry:
            continue

        value = entry[field]

        if field == "month":
            lines.append(f"    {field} = {value},")
        elif field in {"author", "editor"}:
            value = value.replace(" and ", "  and\n      ")
            lines.append(f"    {field} = \"{value}\",")
        else:
            lines.append(f"    {field} = \"{value}\",")

    lines.append("}")
    return "\n".join(lines)


def write_acl_bibtex(entries: List[Dict]) -> str:
    return "\n\n".join(format_acl_entry(e) for e in entries)

# =========================================================
# FILE UPLOAD
# =========================================================

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
    st.info("Upload at least one AUX and one BIB file.")
    st.stop()

# =========================================================
# PROCESS AUX
# =========================================================

citation_order = []

with st.expander("📄 Parsed AUX"):
    for aux in aux_files:
        text = aux.read().decode("utf-8", errors="ignore")
        keys = extract_citation_keys_from_aux(text)
        citation_order.extend(keys)
        st.markdown(f"**{aux.name}** → {len(keys)} citations")
        st.code(keys)

citation_order = list(dict.fromkeys(citation_order))
st.success(f"🔑 Total citations (ordered): {len(citation_order)}")

# =========================================================
# LOAD BIB FILES
# =========================================================

bib_index = {}

for bib in bib_files:
    text = bib.read().decode("utf-8", errors="ignore")
    bib_index.update(parse_bibtex_entries(text))

# =========================================================
# MATCH
# =========================================================

matched, missing = [], []

for key in citation_order:
    if key in bib_index:
        matched.append(bib_index[key])
    else:
        missing.append(key)

# =========================================================
# RESULTS
# =========================================================

c1, c2 = st.columns(2)

with c1:
    st.subheader("✅ Matched (ACL Order)")
    st.metric("Matched", len(matched))
    for e in matched:
        st.markdown(f"**{e['ID']}** — {e.get('title', 'N/A')}")

with c2:
    st.subheader("⚠️ Missing")
    st.metric("Missing", len(missing))
    if missing:
        st.code(missing)

# =========================================================
# EXPORT
# =========================================================

if matched:
    acl_bib = write_acl_bibtex(matched)

    st.download_button(
        "⬇️ Download ACL-Exact BibTeX",
        acl_bib,
        "acl_exact_references.bib",
        "text/plain"
    )

    with st.expander("📦 Preview ACL BibTeX"):
        st.code(acl_bib)


# import streamlit as st
# import re
# import bibtexparser
# from typing import Set, List

# # =========================================================
# # PAGE CONFIG
# # =========================================================
# st.set_page_config(
#     page_title="AUX → Filter BibTeX",
#     layout="wide"
# )

# st.title("📚 AUX → Filter BibTeX References")

# st.markdown("""
# Upload:
# - ✅ One or more **`.aux` files**
# - ✅ One or more **`.bib` files**

# The app will:
# 1. Extract citation keys from AUX files  
# 2. Match them against BibTeX entries  
# 3. Show matched & missing references  
# 4. Export a **clean, LaTeX-ready `.bib` file**
# """)

# # =========================================================
# # HELPERS
# # =========================================================

# def extract_citation_keys_from_aux(aux_text: str) -> Set[str]:
#     """
#     Extract citation keys from:
#     - \\citation{key1,key2}
#     - \\bibcite{key}{...}
#     """
#     keys = set()

#     citation_blocks = re.findall(r"\\citation\{([^}]+)\}", aux_text)
#     for block in citation_blocks:
#         for k in block.split(","):
#             keys.add(k.strip())

#     bibcite_matches = re.findall(r"\\bibcite\{([^}]+)\}", aux_text)
#     for k in bibcite_matches:
#         keys.add(k.strip())

#     return keys


# def load_bib_entries(bib_file) -> List[dict]:
#     parser = bibtexparser.bparser.BibTexParser(common_strings=True)
#     db = bibtexparser.load(bib_file, parser=parser)
#     return db.entries


# def write_filtered_bib(entries: List[dict]) -> str:
#     """
#     Write a clean BibTeX file:
#     - Removes Streamlit/UI-only fields
#     - Produces LaTeX-safe output
#     """
#     clean_entries = []

#     for e in entries:
#         e_clean = dict(e)
#         e_clean.pop("_source_bib", None)
#         clean_entries.append(e_clean)

#     db = bibtexparser.bibdatabase.BibDatabase()
#     db.entries = clean_entries

#     writer = bibtexparser.bwriter.BibTexWriter()
#     writer.indent = "  "
#     writer.comma_first = False
#     writer.order_entries_by = None
#     writer.encoding = "utf-8"

#     return writer.write(db)

# # =========================================================
# # FILE UPLOAD
# # =========================================================

# col1, col2 = st.columns(2)

# with col1:
#     aux_files = st.file_uploader(
#         "📄 Upload AUX files",
#         type=["aux"],
#         accept_multiple_files=True
#     )

# with col2:
#     bib_files = st.file_uploader(
#         "📘 Upload BIB files",
#         type=["bib"],
#         accept_multiple_files=True
#     )

# if not aux_files or not bib_files:
#     st.info("Please upload at least one AUX file and one BIB file.")
#     st.stop()

# # =========================================================
# # PROCESS AUX FILES
# # =========================================================

# all_citation_keys = set()

# with st.expander("📄 Parsed AUX Files"):
#     for aux in aux_files:
#         aux_text = aux.read().decode("utf-8", errors="ignore")
#         keys = extract_citation_keys_from_aux(aux_text)
#         all_citation_keys.update(keys)

#         st.markdown(f"**{aux.name}** → `{len(keys)}` citations")
#         st.code(sorted(keys))

# st.success(f"🔑 Total unique citation keys found: {len(all_citation_keys)}")

# # =========================================================
# # LOAD BIB FILES
# # =========================================================

# all_bib_entries = []

# for bib in bib_files:
#     entries = load_bib_entries(bib)
#     for e in entries:
#         e["_source_bib"] = bib.name  # UI-only
#         all_bib_entries.append(e)

# st.info(f"📘 Loaded `{len(all_bib_entries)}` BibTeX entries from `{len(bib_files)}` files")

# # =========================================================
# # MATCH REFERENCES
# # =========================================================

# matched = []
# missing = []

# bib_index = {e.get("ID"): e for e in all_bib_entries}

# for key in sorted(all_citation_keys):
#     if key in bib_index:
#         matched.append(bib_index[key])
#     else:
#         missing.append(key)

# # =========================================================
# # RESULTS
# # =========================================================

# c1, c2 = st.columns(2)

# with c1:
#     st.subheader("✅ Matched References")
#     st.metric("Matched", len(matched))

#     for e in matched:
#         st.markdown(f"""
# **{e.get('ID')}**  
# - **Title:** {e.get('title', 'N/A')}  
# - **Author:** {e.get('author', 'N/A')}  
# - **Year:** {e.get('year', 'N/A')}  
# - **Source:** `{e.get('_source_bib')}`
# ---
# """)

# with c2:
#     st.subheader("⚠️ Missing References")
#     st.metric("Missing", len(missing))

#     if missing:
#         st.code(missing)

# # =========================================================
# # EXPORT FILTERED BIB
# # =========================================================

# if matched:
#     filtered_bib_text = write_filtered_bib(matched)

#     st.download_button(
#         label="⬇️ Download Filtered BibTeX (.bib)",
#         data=filtered_bib_text,
#         file_name="filtered_references.bib",
#         mime="text/plain"
#     )

#     with st.expander("📦 Preview Filtered BibTeX"):
#         st.code(filtered_bib_text)
# else:
#     st.warning("No matched references found.")


# import streamlit as st
# from pathlib import Path
# import tempfile
# import re
# import bibtexparser

# # ======================================
# # PAGE CONFIG
# # ======================================
# st.set_page_config(layout="wide")
# st.title("📚 AUX → Filter BibTeX References")

# st.markdown("""
# Upload:
# - ✅ One or more **`.aux` files**
# - ✅ One or more **`.bib` files**

# The app will:
# 1. Extract citation keys from AUX files  
# 2. Find matching BibTeX entries  
# 3. Display matched references  
# 4. Export a filtered `.bib` file  
# """)

# # ======================================
# # HELPERS
# # ======================================

# def extract_citation_keys_from_aux(aux_text: str) -> set:
#     """
#     Extract citation keys from \\citation{...} and \\bibcite{...}
#     """
#     keys = set()

#     # \citation{key1,key2}
#     citation_matches = re.findall(r"\\citation\{([^}]+)\}", aux_text)
#     for block in citation_matches:
#         for k in block.split(","):
#             keys.add(k.strip())

#     # \bibcite{key}{...}
#     bibcite_matches = re.findall(r"\\bibcite\{([^}]+)\}", aux_text)
#     for k in bibcite_matches:
#         keys.add(k.strip())

#     return keys


# def load_bib_entries(bib_file) -> list:
#     db = bibtexparser.load(bib_file)
#     return db.entries


# def write_filtered_bib(entries: list) -> str:
#     db = bibtexparser.bibdatabase.BibDatabase()
#     db.entries = entries
#     writer = bibtexparser.bwriter.BibTexWriter()
#     return writer.write(db)


# # ======================================
# # UPLOAD FILES
# # ======================================

# col1, col2 = st.columns(2)

# with col1:
#     aux_files = st.file_uploader(
#         "📄 Upload AUX files",
#         type=["aux"],
#         accept_multiple_files=True
#     )

# with col2:
#     bib_files = st.file_uploader(
#         "📘 Upload BIB files",
#         type=["bib"],
#         accept_multiple_files=True
#     )

# if not aux_files or not bib_files:
#     st.info("Please upload at least one AUX file and one BIB file.")
#     st.stop()

# # ======================================
# # PROCESS AUX FILES
# # ======================================

# all_citation_keys = set()

# with st.expander("📄 Parsed AUX Files", expanded=False):
#     for aux in aux_files:
#         aux_text = aux.read().decode("utf-8", errors="ignore")
#         keys = extract_citation_keys_from_aux(aux_text)
#         all_citation_keys.update(keys)

#         st.write(f"**{aux.name}** → {len(keys)} citations")
#         st.code(sorted(keys))

# st.success(f"🔑 Total unique citation keys found: {len(all_citation_keys)}")

# # ======================================
# # LOAD BIB FILES
# # ======================================

# all_bib_entries = []
# bib_source_map = {}

# for bib in bib_files:
#     entries = load_bib_entries(bib)
#     for e in entries:
#         e["_source_bib"] = bib.name
#         all_bib_entries.append(e)
#         bib_source_map.setdefault(bib.name, 0)
#         bib_source_map[bib.name] += 1

# st.info(f"📘 Loaded {len(all_bib_entries)} BibTeX entries from {len(bib_files)} files.")

# # ======================================
# # MATCH REFERENCES
# # ======================================

# matched = []
# missing = []

# for key in sorted(all_citation_keys):
#     found = False
#     for entry in all_bib_entries:
#         if entry.get("ID") == key:
#             matched.append(entry)
#             found = True
#             break
#     if not found:
#         missing.append(key)

# # ======================================
# # RESULTS
# # ======================================

# c1, c2 = st.columns(2)

# with c1:
#     st.subheader("✅ Matched References")
#     st.metric("Matched", len(matched))

#     if matched:
#         for e in matched:
#             st.markdown(
#                 f"""
# **{e.get('ID')}**  
# - Title: {e.get('title', 'N/A')}  
# - Author: {e.get('author', 'N/A')}  
# - Year: {e.get('year', 'N/A')}  
# - Source: `{e.get('_source_bib')}`
# ---
# """
#             )

# with c2:
#     st.subheader("⚠️ Missing References")
#     st.metric("Missing", len(missing))

#     if missing:
#         st.code(missing)

# # ======================================
# # EXPORT FILTERED BIB
# # ======================================

# if matched:
#     filtered_bib_text = write_filtered_bib(matched)

#     st.download_button(
#         label="⬇️ Download Filtered BibTeX",
#         data=filtered_bib_text,
#         file_name="filtered_references.bib",
#         mime="text/plain"
#     )

# # ======================================
# # OPTIONAL: RAW BIB PREVIEW
# # ======================================

# with st.expander("📦 Preview Filtered BibTeX"):
#     st.code(filtered_bib_text if matched else "No matched entries.")
