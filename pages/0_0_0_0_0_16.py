import streamlit as st
import re
import pandas as pd
from pathlib import Path
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📚 LaTeX → BibTeX Extractor (Registry Driven)",
    layout="wide"
)

st.title("📚 LaTeX → BibTeX Extractor (Registry Driven)")
st.caption(
    "Generate clean .bib files based on LaTeX citations using registry + selected BibTeX databases"
)

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
TECH_PATH = DATA_DIR / "thesis_tech.csv"
TAGS_PATH = DATA_DIR / "thesis_tags.csv"
BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"

# =========================================================
# HELPERS
# =========================================================

def normalize_string(text: str) -> str:
    return str(text).strip().lower()


def extract_all_citations(text: str):
    patterns = [
        r'\\citep\{([^}]+)\}',
        r'\\cite\{([^}]+)\}',
        r'\\citation\{([^}]+)\}',
    ]
    keys = []
    for p in patterns:
        matches = re.findall(p, text)
        for m in matches:
            keys.extend([x.strip() for x in m.split(",") if x.strip()])
    return sorted(set(keys))


def rewrite_latex(tex, replace_map):
    def repl(match):
        items = [x.strip() for x in match.group(1).split(",")]
        new_items = [replace_map.get(i, i) for i in items]
        return r"\citep{" + ", ".join(new_items) + "}"

    tex = re.sub(r'\\citep\{([^}]+)\}', repl, tex)
    tex = re.sub(r'\\cite\{([^}]+)\}', repl, tex)
    return tex


def parse_bib_file(path: Path):
    """Parse a .bib file into raw BibDatabase entries."""
    parser = BibTexParser(common_strings=True)
    with open(path, encoding="utf-8") as f:
        return bibtexparser.load(f, parser=parser)


@st.cache_data(show_spinner=False)
def load_multiple_bib(files: list[Path]):
    """Merge multiple BibDatabase objects into one."""
    merged_db = BibDatabase()
    merged_db.entries = []

    for f in files:
        try:
            db = parse_bib_file(f)
            merged_db.entries.extend(db.entries)
        except Exception as e:
            st.warning(f"⚠️ Failed parsing {f.name}: {e}")

    return merged_db


# =========================================================
# LOAD REGISTRY
# =========================================================

@st.cache_data
def load_registry():
    tech = pd.read_csv(TECH_PATH)
    tags = pd.read_csv(TAGS_PATH)

    assert {"label", "bibtex_key"} <= set(tech.columns)
    assert {"label", "clean_bibtex"} <= set(tags.columns)

    merged = tags.merge(
        tech[["label", "bibtex_key"]],
        on="label",
        how="inner"
    )

    merged["bibtex_key"] = merged["bibtex_key"].astype(str).str.strip()
    merged["clean_bibtex"] = merged["clean_bibtex"].astype(str).str.strip()

    bibtex_to_clean = dict(zip(
        merged["bibtex_key"],
        merged["clean_bibtex"]
    ))

    clean_set = set(merged["clean_bibtex"])

    return merged, bibtex_to_clean, clean_set


try:
    registry_df, BIBTEX_TO_CLEAN, CLEAN_KEYS = load_registry()
    st.sidebar.success(f"📘 Loaded {len(BIBTEX_TO_CLEAN)} registry mappings")
except Exception as e:
    st.sidebar.error(f"❌ Registry load failed: {e}")
    registry_df = pd.DataFrame()
    BIBTEX_TO_CLEAN = {}
    CLEAN_KEYS = set()

# =========================================================
# SIDEBAR INPUTS
# =========================================================

st.sidebar.header("📥 Inputs")

tex_file = st.sidebar.file_uploader(
    "Upload LaTeX (.tex or .aux)",
    type=["tex", "aux"]
)

text_input = st.sidebar.text_area(
    "Or paste LaTeX content",
    height=160
)

# =========================================================
# BIB FILE SELECTION
# =========================================================

st.sidebar.divider()
st.sidebar.header("📂 BibTeX Selection")

bib_files = sorted(BIB_DIR.glob("*.bib"))

if not bib_files:
    st.sidebar.warning("No .bib files found.")
    selected_bibs = []
else:
    selected_bibs = st.sidebar.multiselect(
        "Select BibTeX files",
        bib_files,
        format_func=lambda p: p.name
    )

bib_db = load_multiple_bib(selected_bibs) if selected_bibs else None

# =========================================================
# LOAD LATEX
# =========================================================

latex_text = None
if tex_file:
    latex_text = tex_file.read().decode("utf-8")
elif text_input.strip():
    latex_text = text_input

# =========================================================
# PROCESS
# =========================================================

if latex_text and bib_db:

    st.success("Inputs loaded")

    cited_keys_raw = extract_all_citations(latex_text)

    rows = []
    final_bib_keys = set()

    # -----------------------------------------------------
    # Build Bib index
    # -----------------------------------------------------

    BIB_INDEX = {e["ID"]: e for e in bib_db.entries}

    # -----------------------------------------------------
    # Resolution Pipeline
    # -----------------------------------------------------

    for raw in cited_keys_raw:
        clean_key = None
        final_key = None

        # Registry normalization
        if raw in CLEAN_KEYS:
            clean_key = raw
            registry_source = "already-clean"

        elif raw in BIBTEX_TO_CLEAN:
            clean_key = BIBTEX_TO_CLEAN[raw]
            registry_source = "registry-map"

        else:
            registry_source = "unresolved"

        # Match against BibTeX database
        if clean_key and clean_key in BIB_INDEX:
            final_key = clean_key
            bib_source = "bib-direct"
            final_bib_keys.add(final_key)
        else:
            bib_source = "missing-in-bib"

        rows.append({
            "raw": raw,
            "clean_key": clean_key,
            "final_bib_key": final_key,
            "registry_source": registry_source,
            "bib_source": bib_source,
        })

    df = pd.DataFrame(rows)

    # -----------------------------------------------------
    # Rewrite LaTeX
    # -----------------------------------------------------

    replace_map = {
        r["raw"]: r["final_bib_key"]
        for r in rows
        if r["final_bib_key"]
    }

    fixed_tex = rewrite_latex(latex_text, replace_map)

    # -----------------------------------------------------
    # Build Filtered BibDatabase
    # -----------------------------------------------------

    filtered_db = BibDatabase()
    filtered_db.entries = [
        BIB_INDEX[k] for k in sorted(final_bib_keys) if k in BIB_INDEX
    ]

    writer = BibTexWriter()
    writer.indent = "    "
    writer.order_entries_by = ("ID",)

    filtered_bib_text = writer.write(filtered_db)

    # =====================================================
    # UI
    # =====================================================

    tab1, tab2, tab3 = st.tabs(
        ["✅ Results", "⚠ Unresolved", "📚 Export BibTeX"]
    )

    with tab1:
        st.subheader("Citation Resolution")
        st.dataframe(df, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original LaTeX")
            st.code(latex_text, language="latex")
        with col2:
            st.subheader("Fixed LaTeX")
            st.code(fixed_tex, language="latex")

        st.download_button(
            "⬇ Download Fixed LaTeX",
            fixed_tex,
            file_name="fixed.tex",
            mime="text/plain",
        )

    with tab2:
        unresolved = df[
            (df["registry_source"] == "unresolved") |
            (df["bib_source"] == "missing-in-bib")
        ]

        if unresolved.empty:
            st.success("No unresolved citations 🎉")
        else:
            st.error("Unresolved citations or missing BibTeX entries")
            st.dataframe(unresolved, use_container_width=True)

    with tab3:
        st.subheader("Generated BibTeX (.bib)")
        st.code(filtered_bib_text, language="bibtex")

        st.download_button(
            "⬇ Download .bib file",
            filtered_bib_text,
            file_name="references.bib",
            mime="text/plain",
        )

else:
    st.info("Upload LaTeX and select BibTeX files to generate .bib.")


# import streamlit as st
# import re
# import pandas as pd
# from pathlib import Path
# import bibtexparser
# from bibtexparser.bparser import BibTexParser

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📚 LaTeX BibTeX Registry Normalizer",
#     layout="wide"
# )

# st.title("📚 LaTeX Citation Normalizer — Registry + BibTeX")
# st.caption(
#     "Normalize LaTeX citations using thesis registry and selected BibTeX databases"
# )

# # =========================================================
# # PATH CONFIG  (MATCHES YOUR CURATOR)
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]

# DATA_DIR = BASE_DIR / "data"
# TECH_PATH = DATA_DIR / "thesis_tech.csv"
# TAGS_PATH = DATA_DIR / "thesis_tags.csv"

# BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"

# # =========================================================
# # UTILITIES (FROM YOUR CURATOR)
# # =========================================================

# def normalize_string(text: str) -> str:
#     return str(text).strip().lower()


# def parse_bib_file(path: Path) -> list[dict]:
#     """Parse one .bib file into a list of dict rows."""
#     parser = BibTexParser(common_strings=True)
#     with open(path, encoding="utf-8") as f:
#         bib_db = bibtexparser.load(f, parser=parser)

#     rows = []
#     for entry in bib_db.entries:
#         row = {
#             "bib_key": entry.get("ID", "").strip(),
#             "title": entry.get("title", "").strip(),
#             "__source_file": path.name,
#         }
#         rows.append(row)

#     return rows


# @st.cache_data(show_spinner=False)
# def load_multiple_bib(files: list[Path]) -> pd.DataFrame:
#     all_rows = []
#     for f in files:
#         try:
#             rows = parse_bib_file(f)
#             all_rows.extend(rows)
#         except Exception as e:
#             st.warning(f"⚠️ Failed to parse {f.name}: {e}")

#     if not all_rows:
#         return pd.DataFrame(columns=["bib_key", "title", "__source_file", "title_norm"])

#     df = pd.DataFrame(all_rows)
#     df["title_norm"] = df["title"].map(normalize_string)
#     return df


# def extract_all_citations(text: str):
#     patterns = [
#         r'\\citep\{([^}]+)\}',
#         r'\\cite\{([^}]+)\}',
#         r'\\citation\{([^}]+)\}',
#     ]
#     keys = []
#     for p in patterns:
#         matches = re.findall(p, text)
#         for m in matches:
#             keys.extend([x.strip() for x in m.split(",") if x.strip()])
#     return sorted(set(keys))


# def rewrite_latex(tex, replace_map):
#     def repl(match):
#         items = [x.strip() for x in match.group(1).split(",")]
#         new_items = [replace_map.get(i, i) for i in items]
#         return r"\citep{" + ", ".join(new_items) + "}"

#     tex = re.sub(r'\\citep\{([^}]+)\}', repl, tex)
#     tex = re.sub(r'\\cite\{([^}]+)\}', repl, tex)
#     return tex


# # =========================================================
# # LOAD REGISTRY (CSV IS SOURCE OF TRUTH)
# # =========================================================

# @st.cache_data
# def load_registry():
#     tech = pd.read_csv(TECH_PATH)
#     tags = pd.read_csv(TAGS_PATH)

#     assert {"label", "bibtex_key"} <= set(tech.columns)
#     assert {"label", "clean_bibtex"} <= set(tags.columns)

#     merged = tags.merge(
#         tech[["label", "bibtex_key"]],
#         on="label",
#         how="inner"
#     )

#     merged["bibtex_key"] = merged["bibtex_key"].astype(str).str.strip()
#     merged["clean_bibtex"] = merged["clean_bibtex"].astype(str).str.strip()

#     # Maps
#     bibtex_to_clean = dict(zip(
#         merged["bibtex_key"],
#         merged["clean_bibtex"]
#     ))

#     clean_set = set(merged["clean_bibtex"])

#     return merged, bibtex_to_clean, clean_set


# try:
#     registry_df, BIBTEX_TO_CLEAN, CLEAN_KEYS = load_registry()
#     st.sidebar.success(f"📘 Loaded {len(BIBTEX_TO_CLEAN)} registry mappings")
# except Exception as e:
#     st.sidebar.error(f"❌ Registry load failed: {e}")
#     registry_df = pd.DataFrame()
#     BIBTEX_TO_CLEAN = {}
#     CLEAN_KEYS = set()

# # =========================================================
# # SIDEBAR INPUTS
# # =========================================================

# st.sidebar.header("📥 Inputs")

# tex_file = st.sidebar.file_uploader(
#     "Upload LaTeX (.tex or .aux)",
#     type=["tex", "aux"]
# )

# text_input = st.sidebar.text_area(
#     "Or paste LaTeX content",
#     height=180
# )

# with st.sidebar.expander("📘 Registry Preview"):
#     if not registry_df.empty:
#         st.dataframe(
#             registry_df[["label", "bibtex_key", "clean_bibtex"]],
#             height=240,
#             use_container_width=True
#         )

# # =========================================================
# # SIDEBAR BIB SELECTION (SAME AS CURATOR)
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("📂 BibTeX Selection")

# bib_files = sorted(BIB_DIR.glob("*.bib"))

# if not bib_files:
#     st.sidebar.warning("⚠️ No .bib files found.")
#     selected_bibs = []
# else:
#     selected_bibs = st.sidebar.multiselect(
#         "Select BibTeX files",
#         bib_files,
#         format_func=lambda p: p.name
#     )

# bib_df = load_multiple_bib(selected_bibs) if selected_bibs else pd.DataFrame()

# with st.sidebar.expander("📘 Bib Preview"):
#     if not bib_df.empty:
#         st.dataframe(bib_df.head(30), use_container_width=True)

# # =========================================================
# # BUILD BIB LOOKUPS
# # =========================================================

# BIB_KEYS_SET = set(bib_df["bib_key"]) if not bib_df.empty else set()

# TITLE_TO_BIBKEY = {}
# for _, row in bib_df.iterrows():
#     TITLE_TO_BIBKEY.setdefault(row["title_norm"], []).append(row["bib_key"])

# # =========================================================
# # LOAD LATEX
# # =========================================================

# latex_text = None
# if tex_file:
#     latex_text = tex_file.read().decode("utf-8")
# elif text_input.strip():
#     latex_text = text_input

# # =========================================================
# # PROCESS
# # =========================================================

# if latex_text:

#     st.success("LaTeX loaded")

#     all_keys = extract_all_citations(latex_text)

#     rows = []
#     for raw in all_keys:
#         rows.append({
#             "raw": raw,
#             "clean_key": None,
#             "final_bib_key": None,
#             "registry_source": None,
#             "bib_source": None,
#         })

#     # -----------------------------------------------------
#     # Resolution Pipeline
#     # -----------------------------------------------------

#     for r in rows:
#         raw = r["raw"]
#         clean_key = None
#         final_bib_key = None

#         # Step 1 — Registry resolution
#         if raw in CLEAN_KEYS:
#             clean_key = raw
#             r["registry_source"] = "already-clean"

#         elif raw in BIBTEX_TO_CLEAN:
#             clean_key = BIBTEX_TO_CLEAN[raw]
#             r["registry_source"] = "registry-map"

#         else:
#             r["registry_source"] = "unresolved"

#         # Step 2 — Match against BibTeX
#         if clean_key:
#             if clean_key in BIB_KEYS_SET:
#                 final_bib_key = clean_key
#                 r["bib_source"] = "direct-bib-key"

#             else:
#                 r["bib_source"] = "missing-in-bib"

#         r["clean_key"] = clean_key
#         r["final_bib_key"] = final_bib_key

#     df = pd.DataFrame(rows)

#     # -----------------------------------------------------
#     # Build replace map
#     # -----------------------------------------------------

#     replace_map = {
#         r["raw"]: r["final_bib_key"]
#         for r in rows
#         if r["final_bib_key"]
#     }

#     fixed_tex = rewrite_latex(latex_text, replace_map)

#     # =====================================================
#     # UI
#     # =====================================================

#     tab1, tab2, tab3 = st.tabs(
#         ["✅ Results", "⚠ Unresolved", "📘 Loaded BibTeX"]
#     )

#     with tab1:
#         st.subheader("Citation Resolution Table")
#         st.dataframe(df, use_container_width=True)

#         col1, col2 = st.columns(2)

#         with col1:
#             st.subheader("Original LaTeX")
#             st.code(latex_text, language="latex")

#         with col2:
#             st.subheader("Fixed LaTeX")
#             st.code(fixed_tex, language="latex")

#         st.download_button(
#             "⬇ Download Fixed LaTeX",
#             fixed_tex,
#             file_name="fixed.tex",
#             mime="text/plain",
#         )

#         st.download_button(
#             "⬇ Download Resolution Log (CSV)",
#             df.to_csv(index=False).encode("utf-8"),
#             file_name="citation_log.csv",
#             mime="text/csv",
#         )

#     with tab2:
#         unresolved = df[
#             (df["registry_source"] == "unresolved") |
#             (df["bib_source"] == "missing-in-bib")
#         ]

#         if unresolved.empty:
#             st.success("No unresolved citations 🎉")
#         else:
#             st.error("Unresolved or missing BibTeX entries")
#             st.dataframe(unresolved, use_container_width=True)

#     with tab3:
#         st.subheader("Loaded BibTeX Entries")
#         st.dataframe(bib_df, use_container_width=True, height=520)

# else:
#     st.info("Upload LaTeX content and select BibTeX files to begin.")


# import streamlit as st
# import pandas as pd
# from pathlib import Path

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📚 Thesis CSV → BibTeX Generator",
#     layout="wide"
# )

# st.title("📚 Thesis CSV → BibTeX Generator")
# st.caption("Merge CSV files by label and export BibTeX entries")

# # =========================================================
# # PATHS
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# DATA_DIR = BASE_DIR / "data"

# TECH_PATH = DATA_DIR / "thesis_tech.csv"
# TAGS_PATH = DATA_DIR / "thesis_tags.csv"

# # =========================================================
# # ACTION BAR
# # =========================================================

# col1, col2 = st.columns([1, 6])

# with col1:
#     if st.button("🔄 Reload Data"):
#         st.cache_data.clear()
#         st.rerun()

# # =========================================================
# # LOAD DATA
# # =========================================================

# @st.cache_data
# def load_csvs():
#     if not TECH_PATH.exists():
#         raise FileNotFoundError(f"Missing file: {TECH_PATH}")

#     if not TAGS_PATH.exists():
#         raise FileNotFoundError(f"Missing file: {TAGS_PATH}")

#     tech_df = pd.read_csv(TECH_PATH)
#     tags_df = pd.read_csv(TAGS_PATH)

#     return tech_df, tags_df


# try:
#     tech_df, tags_df = load_csvs()
# except Exception as e:
#     st.error(str(e))
#     st.stop()

# # =========================================================
# # VALIDATION
# # =========================================================

# REQUIRED_TECH_COLS = {"label", "bibtex_key"}
# REQUIRED_TAGS_COLS = {"label"}

# missing_tech = REQUIRED_TECH_COLS - set(tech_df.columns)
# missing_tags = REQUIRED_TAGS_COLS - set(tags_df.columns)

# if missing_tech:
#     st.error(f"❌ thesis_tech.csv missing columns: {missing_tech}")
#     st.stop()

# if missing_tags:
#     st.error(f"❌ thesis_tags.csv missing columns: {missing_tags}")
#     st.stop()

# # =========================================================
# # PREVIEW INPUT DATA
# # =========================================================

# with st.expander("📄 Preview thesis_tech.csv"):
#     st.dataframe(tech_df, use_container_width=True)

# with st.expander("📄 Preview thesis_tags.csv"):
#     st.dataframe(tags_df, use_container_width=True)

# # =========================================================
# # MERGE CONFIG
# # =========================================================

# st.subheader("🔗 Merge Configuration")

# merge_type = st.selectbox(
#     "Merge Strategy",
#     ["left", "inner", "right", "outer"],
#     index=0,
#     help="left keeps all thesis_tags rows"
# )

# # =========================================================
# # MERGE
# # =========================================================

# merged_df = tags_df.merge(
#     tech_df[["label", "bibtex_key"]],
#     on="label",
#     how=merge_type
# )

# # =========================================================
# # MERGE STATS
# # =========================================================

# st.subheader("📊 Merge Statistics")

# total_tags = len(tags_df)
# total_tech = len(tech_df)
# total_merged = len(merged_df)
# matched = merged_df["bibtex_key"].notna().sum()
# unmatched = merged_df["bibtex_key"].isna().sum()

# c1, c2, c3, c4 = st.columns(4)
# c1.metric("Tags Rows", total_tags)
# c2.metric("Tech Rows", total_tech)
# c3.metric("Merged Rows", total_merged)
# c4.metric("Matched BibTeX", matched)

# if unmatched > 0:
#     st.warning(f"⚠️ {unmatched} rows have no matching bibtex_key")

# # =========================================================
# # MERGED TABLE VIEW
# # =========================================================

# st.subheader("📋 Merged Table")

# st.dataframe(
#     merged_df,
#     use_container_width=True,
#     height=420
# )

# # =========================================================
# # BIBTEX GENERATION
# # =========================================================

# def normalize_author(author_str: str) -> str:
#     """
#     Normalize author string to BibTeX format using 'and'.
#     """
#     if not isinstance(author_str, str):
#         return ""

#     author_str = author_str.replace(";", " and ")
#     author_str = author_str.replace("|", " and ")
#     author_str = " ".join(author_str.split())

#     return author_str.strip()


# def row_to_bibtex(row: pd.Series) -> str:
#     """
#     Convert one dataframe row into a BibTeX entry.
#     """
#     entry_type = str(row.get("type", "inproceedings")).lower()
#     key = row.get("bibtex_key", f"missing_{row.name}")

#     fields = {
#         "title": row.get("title"),
#         "author": normalize_author(row.get("author")),
#         "booktitle": row.get("conferences") or row.get("journal_type"),
#         "year": row.get("year"),
#         "address": row.get("location"),
#         "pages": row.get("page"),
#         "url": row.get("url"),
#     }

#     lines = [f"@{entry_type}{{{key},"]

#     for field, value in fields.items():
#         if pd.notna(value) and str(value).strip():
#             safe_value = str(value).replace("\n", " ").strip()
#             lines.append(f'    {field} = "{safe_value}",')

#     # Remove last comma
#     if len(lines) > 1:
#         lines[-1] = lines[-1].rstrip(",")

#     lines.append("}")

#     return "\n".join(lines)


# def generate_bibtex(df: pd.DataFrame) -> str:
#     entries = []

#     for _, row in df.iterrows():
#         if pd.notna(row.get("bibtex_key")):
#             entries.append(row_to_bibtex(row))

#     return "\n\n".join(entries)


# bibtex_text = generate_bibtex(merged_df)

# # =========================================================
# # BIBTEX VIEWER + DOWNLOAD
# # =========================================================

# st.subheader("📚 Loaded BibTeX Entries")

# st.text_area(
#     "BibTeX Output",
#     bibtex_text,
#     height=420
# )

# st.download_button(
#     "⬇️ Download BibTeX",
#     data=bibtex_text.encode("utf-8"),
#     file_name="thesis_references.bib",
#     mime="text/plain"
# )

# # =========================================================
# # MERGED CSV DOWNLOAD
# # =========================================================

# merged_csv = merged_df.to_csv(index=False).encode("utf-8")

# st.download_button(
#     "⬇️ Download Merged CSV",
#     data=merged_csv,
#     file_name="thesis_merged.csv",
#     mime="text/csv"
# )


# import streamlit as st
# import re
# import pandas as pd
# from pathlib import Path
# import bibtexparser
# from bibtexparser.bparser import BibTexParser

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="LaTeX Citation Normalizer (Registry + BibTeX)",
#     layout="wide"
# )

# st.title("📚 LaTeX Citation Normalizer — Registry + BibTeX")
# st.caption(
#     "Canonical mapping using thesis registry + validation against selected BibTeX files"
# )

# # =========================================================
# # PATHS
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# DATA_DIR = BASE_DIR / "data"

# TECH_PATH = DATA_DIR / "thesis_tech.csv"
# TAGS_PATH = DATA_DIR / "thesis_tags.csv"
# BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"

# # =========================================================
# # HELPERS
# # =========================================================

# def normalize_string(text: str) -> str:
#     return str(text).strip().lower()


# def extract_all_citations(text: str):
#     patterns = [
#         r'\\citep\{([^}]+)\}',
#         r'\\cite\{([^}]+)\}',
#         r'\\citation\{([^}]+)\}',
#     ]
#     keys = []
#     for p in patterns:
#         matches = re.findall(p, text)
#         for m in matches:
#             keys.extend([x.strip() for x in m.split(",") if x.strip()])
#     return sorted(set(keys))


# def rewrite_latex(tex, replace_map):
#     def repl(match):
#         items = [x.strip() for x in match.group(1).split(",")]
#         new_items = [replace_map.get(i, i) for i in items]
#         return r"\citep{" + ", ".join(new_items) + "}"

#     tex = re.sub(r'\\citep\{([^}]+)\}', repl, tex)
#     tex = re.sub(r'\\cite\{([^}]+)\}', repl, tex)
#     return tex


# def parse_bib_file(path: Path) -> list[dict]:
#     parser = BibTexParser(common_strings=True)
#     with open(path, encoding="utf-8") as f:
#         bib_db = bibtexparser.load(f, parser=parser)

#     rows = []
#     for entry in bib_db.entries:
#         rows.append({
#             "bib_key": entry.get("ID", "").strip(),
#             "title": entry.get("title", "").strip(),
#         })
#     return rows


# @st.cache_data
# def load_selected_bibs(files: list[Path]) -> pd.DataFrame:
#     all_rows = []
#     for f in files:
#         try:
#             all_rows.extend(parse_bib_file(f))
#         except Exception as e:
#             st.warning(f"⚠️ Failed parsing {f.name}: {e}")

#     if not all_rows:
#         return pd.DataFrame(columns=["bib_key", "title", "title_norm"])

#     df = pd.DataFrame(all_rows)
#     df["title_norm"] = df["title"].map(normalize_string)
#     return df


# # =========================================================
# # LOAD REGISTRY
# # =========================================================

# @st.cache_data
# def load_registry():
#     tech = pd.read_csv(TECH_PATH)
#     tags = pd.read_csv(TAGS_PATH)

#     assert {"label", "bibtex_key"} <= set(tech.columns)
#     assert {"label", "clean_bibtex"} <= set(tags.columns)

#     merged = tags.merge(
#         tech[["label", "bibtex_key"]],
#         on="label",
#         how="inner"
#     )

#     merged["bibtex_key"] = merged["bibtex_key"].astype(str).str.strip()
#     merged["clean_bibtex"] = merged["clean_bibtex"].astype(str).str.strip()

#     bibtex_to_clean = dict(zip(
#         merged["bibtex_key"],
#         merged["clean_bibtex"]
#     ))

#     clean_set = set(merged["clean_bibtex"])

#     return merged, bibtex_to_clean, clean_set


# try:
#     registry_df, BIBTEX_TO_CLEAN, CLEAN_KEYS = load_registry()
#     st.sidebar.success(f"📘 Loaded {len(BIBTEX_TO_CLEAN)} registry mappings")
# except Exception as e:
#     st.sidebar.error(f"❌ Registry load failed: {e}")
#     registry_df = pd.DataFrame()
#     BIBTEX_TO_CLEAN = {}
#     CLEAN_KEYS = set()

# # =========================================================
# # SIDEBAR INPUTS
# # =========================================================

# st.sidebar.header("📥 Inputs")

# tex_file = st.sidebar.file_uploader("Upload LaTeX (.tex or .aux)", type=["tex", "aux"])
# text_input = st.sidebar.text_area("Or paste LaTeX content", height=200)

# with st.sidebar.expander("📘 Registry Preview"):
#     if not registry_df.empty:
#         st.dataframe(
#             registry_df[["label", "bibtex_key", "clean_bibtex"]],
#             height=240,
#             use_container_width=True
#         )

# # =========================================================
# # SIDEBAR BIB SELECTION
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("📂 BibTeX Selection")

# bib_files = sorted(BIB_DIR.glob("*.bib"))

# if not bib_files:
#     st.sidebar.warning("No .bib files found.")
#     selected_bibs = []
# else:
#     selected_bibs = st.sidebar.multiselect(
#         "Select BibTeX files",
#         bib_files,
#         format_func=lambda p: p.name
#     )

# bib_df = load_selected_bibs(selected_bibs) if selected_bibs else pd.DataFrame()

# with st.sidebar.expander("📘 Bib Preview"):
#     if not bib_df.empty:
#         st.dataframe(bib_df.head(20), use_container_width=True)

# # =========================================================
# # BUILD BIB LOOKUPS
# # =========================================================

# BIB_KEYS_SET = set(bib_df["bib_key"]) if not bib_df.empty else set()

# TITLE_TO_BIBKEY = {}
# for _, row in bib_df.iterrows():
#     TITLE_TO_BIBKEY.setdefault(row["title_norm"], []).append(row["bib_key"])

# # =========================================================
# # LOAD LATEX
# # =========================================================

# latex_text = None
# if tex_file:
#     latex_text = tex_file.read().decode("utf-8")
# elif text_input.strip():
#     latex_text = text_input

# # =========================================================
# # PROCESS
# # =========================================================

# if latex_text:

#     st.success("LaTeX loaded")

#     all_keys = extract_all_citations(latex_text)

#     rows = []
#     for raw in all_keys:
#         rows.append({
#             "raw": raw,
#             "clean_key": None,
#             "final_key": None,
#             "registry_source": None,
#             "bib_source": None,
#         })

#     # -----------------------------------------------------
#     # Resolution Pipeline
#     # -----------------------------------------------------

#     for r in rows:
#         raw = r["raw"]
#         clean_key = None
#         final_bib_key = None

#         # 1. Already canonical clean key
#         if raw in CLEAN_KEYS:
#             clean_key = raw
#             r["registry_source"] = "already-clean"

#         # 2. Legacy bibtex_key → clean_bibtex
#         elif raw in BIBTEX_TO_CLEAN:
#             clean_key = BIBTEX_TO_CLEAN[raw]
#             r["registry_source"] = "registry-map"

#         else:
#             r["registry_source"] = "unresolved"

#         # 3. Resolve against BibTeX
#         if clean_key:
#             # Direct BibTeX key match
#             if clean_key in BIB_KEYS_SET:
#                 final_bib_key = clean_key
#                 r["bib_source"] = "direct-match"

#             # Fallback: title match (optional safety)
#             elif clean_key in TITLE_TO_BIBKEY:
#                 final_bib_key = TITLE_TO_BIBKEY[clean_key][0]
#                 r["bib_source"] = "title-fallback"

#             else:
#                 r["bib_source"] = "missing-in-bib"

#         r["clean_key"] = clean_key
#         r["final_key"] = final_bib_key

#     df = pd.DataFrame(rows)

#     # -----------------------------------------------------
#     # Build replace map
#     # -----------------------------------------------------

#     replace_map = {
#         r["raw"]: r["final_key"]
#         for r in rows
#         if r["final_key"]
#     }

#     fixed_tex = rewrite_latex(latex_text, replace_map)

#     # =====================================================
#     # UI
#     # =====================================================

#     tab1, tab2, tab3 = st.tabs(["✅ Results", "⚠ Unresolved", "📘 Bib Coverage"])

#     with tab1:
#         st.subheader("Citation Resolution Table")
#         st.dataframe(df, use_container_width=True)

#         col1, col2 = st.columns(2)
#         with col1:
#             st.subheader("Original LaTeX")
#             st.code(latex_text, language="latex")
#         with col2:
#             st.subheader("Fixed LaTeX")
#             st.code(fixed_tex, language="latex")

#         st.download_button(
#             "⬇ Download Fixed LaTeX",
#             fixed_tex,
#             file_name="fixed.tex",
#             mime="text/plain",
#         )

#         st.download_button(
#             "⬇ Download Resolution Log (CSV)",
#             df.to_csv(index=False).encode("utf-8"),
#             file_name="citation_log.csv",
#             mime="text/csv",
#         )

#     with tab2:
#         unresolved = df[
#             (df["registry_source"] == "unresolved") |
#             (df["bib_source"] == "missing-in-bib")
#         ]

#         if unresolved.empty:
#             st.success("No unresolved citations 🎉")
#         else:
#             st.error("Unresolved or missing BibTeX entries")
#             st.dataframe(unresolved, use_container_width=True)

#     with tab3:
#         st.subheader("Loaded BibTeX Entries")
#         st.dataframe(bib_df, use_container_width=True, height=400)

# else:
#     st.info("Upload LaTeX content and select BibTeX files to begin.")
