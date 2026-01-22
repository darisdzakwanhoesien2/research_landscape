import streamlit as st
import re
import pandas as pd
from pathlib import Path

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="LaTeX Citation Normalizer (Registry Only)",
    layout="wide"
)

st.title("📚 LaTeX Citation Normalizer — Registry Driven")
st.caption(
    "Canonical citation mapping using thesis_tags.csv + thesis_tech.csv only"
)

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

TECH_PATH = DATA_DIR / "thesis_tech.csv"
TAGS_PATH = DATA_DIR / "thesis_tags.csv"

# =========================================================
# HELPERS
# =========================================================

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


# =========================================================
# LOAD REGISTRY (REPLACES .bib)
# =========================================================

@st.cache_data
def load_registry():
    tech = pd.read_csv(TECH_PATH)
    tags = pd.read_csv(TAGS_PATH)

    assert {"label", "bibtex_key"} <= set(tech.columns), "Missing bibtex_key"
    assert {"label", "clean_bibtex"} <= set(tags.columns), "Missing clean_bibtex"

    merged = tags.merge(
        tech[["label", "bibtex_key"]],
        on="label",
        how="inner"
    )

    merged["bibtex_key"] = merged["bibtex_key"].astype(str).str.strip()
    merged["clean_bibtex"] = merged["clean_bibtex"].astype(str).str.strip()

    # Maps
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
# INPUTS
# =========================================================

st.sidebar.header("📥 Input")

tex_file = st.sidebar.file_uploader("Upload LaTeX (.tex or .aux)", type=["tex", "aux"])
text_input = st.sidebar.text_area("Or paste LaTeX content", height=200)

with st.sidebar.expander("📘 Registry Preview"):
    if not registry_df.empty:
        st.dataframe(
            registry_df[["label", "bibtex_key", "clean_bibtex"]],
            height=240,
            use_container_width=True
        )

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

if latex_text:

    st.success("LaTeX loaded")

    all_keys = extract_all_citations(latex_text)

    rows = []
    for raw in all_keys:
        rows.append({
            "raw": raw,
            "final_key": None,
            "source": None,
        })

    # -----------------------------------------------------
    # Resolution Pipeline (Registry Only)
    # -----------------------------------------------------

    for r in rows:
        raw = r["raw"]

        # 1. Already canonical
        if raw in CLEAN_KEYS:
            r["final_key"] = raw
            r["source"] = "already-clean"

        # 2. Legacy bibtex_key → clean_bibtex
        elif raw in BIBTEX_TO_CLEAN:
            r["final_key"] = BIBTEX_TO_CLEAN[raw]
            r["source"] = "registry-map"

        else:
            r["source"] = "unresolved"

    df = pd.DataFrame(rows)

    # -----------------------------------------------------
    # Build replace map for LaTeX rewrite
    # -----------------------------------------------------

    replace_map = {
        r["raw"]: r["final_key"]
        for r in rows
        if r["final_key"]
    }

    fixed_tex = rewrite_latex(latex_text, replace_map)

    # =====================================================
    # UI
    # =====================================================

    tab1, tab2 = st.tabs(["✅ Results", "⚠ Unresolved"])

    with tab1:
        st.subheader("Citation Resolution Table")
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

        st.download_button(
            "⬇ Download Resolution Log (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name="citation_log.csv",
            mime="text/csv",
        )

    with tab2:
        unresolved = df[df["source"] == "unresolved"]
        if unresolved.empty:
            st.success("No unresolved citations 🎉")
        else:
            st.error("Unresolved citations — add them to registry")
            st.dataframe(unresolved, use_container_width=True)

else:
    st.info("Upload or paste LaTeX content to begin.")


# import streamlit as st
# import re
# import pandas as pd
# from pathlib import Path

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="LaTeX Registry Citation Normalizer",
#     layout="wide"
# )

# st.title("📚 LaTeX Citation Normalizer (Registry-Driven)")
# st.caption(
#     "Normalize LaTeX citations using ONLY thesis registry CSVs (no external DOI DB)"
# )

# # =========================================================
# # PATHS
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# DATA_DIR = BASE_DIR / "data"

# TECH_PATH = DATA_DIR / "thesis_tech.csv"
# TAGS_PATH = DATA_DIR / "thesis_tags.csv"

# # =========================================================
# # HELPERS
# # =========================================================

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


# def parse_bibtex_keys(bib_text: str):
#     """
#     Extract BibTeX entry keys only
#     """
#     if not bib_text:
#         return set()
#     return set(re.findall(r'@\w+\{([^,]+),', bib_text))


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

#     merged["bibtex_key"] = merged["bibtex_key"].astype(str)
#     merged["clean_bibtex"] = merged["clean_bibtex"].astype(str)

#     # Build lookup maps
#     bibtex_to_clean = dict(zip(
#         merged["bibtex_key"],
#         merged["clean_bibtex"]
#     ))

#     clean_to_clean = dict(zip(
#         merged["clean_bibtex"],
#         merged["clean_bibtex"]
#     ))

#     return merged, bibtex_to_clean, clean_to_clean


# try:
#     registry_df, BIBTEX_TO_CLEAN, CLEAN_TO_CLEAN = load_registry()
#     st.sidebar.success(f"📘 Loaded {len(BIBTEX_TO_CLEAN)} registry mappings")
# except Exception as e:
#     st.sidebar.error(f"❌ Registry load failed: {e}")
#     registry_df = pd.DataFrame()
#     BIBTEX_TO_CLEAN = {}
#     CLEAN_TO_CLEAN = {}

# # =========================================================
# # SIDEBAR INPUT
# # =========================================================

# st.sidebar.header("📥 Inputs")

# bib_file = st.sidebar.file_uploader("Upload BibTeX (.bib)", type=["bib"])
# tex_file = st.sidebar.file_uploader("Upload LaTeX (.tex or .aux)", type=["tex", "aux"])
# text_input = st.sidebar.text_area("Or paste LaTeX/AUX content", height=200)

# with st.sidebar.expander("📘 Registry Preview"):
#     if not registry_df.empty:
#         st.dataframe(
#             registry_df[["label", "bibtex_key", "clean_bibtex"]],
#             height=240,
#             use_container_width=True
#         )
#     else:
#         st.info("Registry not loaded")

# # =========================================================
# # LOAD INPUTS
# # =========================================================

# bib_text = bib_file.read().decode("utf-8") if bib_file else None

# latex_text = None
# if tex_file:
#     latex_text = tex_file.read().decode("utf-8")
# elif text_input.strip():
#     latex_text = text_input

# # =========================================================
# # PROCESS
# # =========================================================

# if latex_text:

#     st.success("Input loaded successfully")

#     bibtex_keys_in_file = parse_bibtex_keys(bib_text)
#     all_keys = extract_all_citations(latex_text)

#     rows = []
#     for raw in all_keys:
#         rows.append({
#             "raw": raw,
#             "resolved_key": None,
#             "final_key": None,
#             "source": None,
#         })

#     # -----------------------------------------------------
#     # Resolution Pipeline (Registry Only)
#     # -----------------------------------------------------

#     for r in rows:
#         raw = r["raw"]

#         # 1. Already clean key
#         if raw in CLEAN_TO_CLEAN:
#             r["resolved_key"] = raw
#             r["final_key"] = raw
#             r["source"] = "already-clean"

#         # 2. bibtex_key → clean_bibtex
#         elif raw in BIBTEX_TO_CLEAN:
#             r["resolved_key"] = raw
#             r["final_key"] = BIBTEX_TO_CLEAN[raw]
#             r["source"] = "registry-map"

#         # 3. BibTeX file contains raw key (but not in registry)
#         elif raw in bibtex_keys_in_file:
#             r["resolved_key"] = raw
#             r["final_key"] = raw
#             r["source"] = "bibtex-file-only"

#         else:
#             r["source"] = "unresolved"

#     df = pd.DataFrame(rows)

#     # -----------------------------------------------------
#     # Build replace map for LaTeX rewrite
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

#     tab1, tab2, tab3 = st.tabs(["✅ Results", "⚠ Unresolved", "🔍 Debug"])

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
#         unresolved = df[df["source"] == "unresolved"]
#         if unresolved.empty:
#             st.success("No unresolved citations 🎉")
#         else:
#             st.error("Unresolved citations")
#             st.dataframe(unresolved, use_container_width=True)

#     with tab3:
#         st.subheader("Registry Mapping Sample")
#         st.dataframe(registry_df.head(20), use_container_width=True)

# else:
#     st.info("Upload or paste LaTeX/AUX content to begin.")
