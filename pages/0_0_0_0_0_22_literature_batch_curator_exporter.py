import json
import hashlib
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
import textwrap

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📦 Literature Batch Curator & Exporter",
    layout="wide"
)

st.title("📦 Literature Batch Curator & Exporter")
st.caption(
    "Batch select CSV datasets from data/csv, curate them, "
    "and auto-exclude papers already covered in registry JSON. https://notebooklm.google.com/notebook/df6ae55f-b784-45c3-9e06-7877f2f95acf and open 0_0_0_0_25_reference_coverage_analyzer to check the unique matched references"
)

# =========================================================
# GLOBAL RELOAD CONTROL
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

CSV_DIR = BASE_DIR / "data" / "csv"
EXPORT_DIR = BASE_DIR / "outputs"
REGISTRY_DIR = BASE_DIR / "data" / "research_registry"

for d in [CSV_DIR, EXPORT_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")
st.sidebar.caption(f"📚 Registry Folder: `{REGISTRY_DIR}`")

# =========================================================
# UTILITIES
# =========================================================

def normalize_string(text: str) -> str:
    return str(text).strip().lower()


def normalize_text(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


def parse_excluded_titles(text: str) -> set[str]:
    return {
        normalize_string(line)
        for line in text.splitlines()
        if line.strip()
    }


def directory_fingerprint(path: Path) -> str:
    parts = []
    for p in sorted(path.glob("*")):
        if p.is_file():
            stat = p.stat()
            parts.append(f"{p.name}:{stat.st_mtime_ns}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


# =========================================================
# DATA LOADERS
# =========================================================

@st.cache_data
def discover_csv_files():
    return sorted(CSV_DIR.glob("*.csv"))


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def load_multiple(files):
    frames = []
    for f in files:
        df = load_csv(f)
        df["__source_file"] = f.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


@st.cache_data(show_spinner=False)
def load_registry_references(_fingerprint: str) -> pd.DataFrame:
    rows = []
    files = sorted(REGISTRY_DIR.glob("*.json"))

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        root = data.get("research_plan_references", {})
        if not isinstance(root, dict):
            continue

        for layer_key, layer in root.items():
            focus = layer.get("focus", "")

            for ref in layer.get("literature_references", []):
                rows.append({
                    "registry_file": path.name,
                    "objective_layer": layer_key,
                    "focus": focus,
                    "json_title": ref.get("title", ""),
                    "json_authors": ref.get("authors", ""),
                    "json_source_index": ref.get("source_index"),
                    "json_relevance": ref.get("relevance", ""),
                })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["title_norm"] = df["json_title"].map(normalize_string)

    return df


def build_unique_key(df: pd.DataFrame) -> pd.Series:
    if "DOI" in df.columns:
        return (
            df["DOI"]
            .fillna(df["title_norm"])
            .fillna(df["json_title"])
            .astype(str)
            .str.strip()
            .str.lower()
        )
    else:
        return (
            df["title_norm"]
            .fillna(df["json_title"])
            .astype(str)
            .str.strip()
            .str.lower()
        )


@st.cache_data(show_spinner=False)
def compute_unique_matched(
    registry_fp: str,
    csv_fp: str
) -> pd.DataFrame:

    json_df = load_registry_references(registry_fp)
    csv_files = discover_csv_files()
    if not csv_files:
        return pd.DataFrame()

    csv_df = load_multiple(csv_files)

    if json_df.empty or csv_df.empty:
        return pd.DataFrame()

    if "Title" not in csv_df.columns:
        return pd.DataFrame()

    csv_df = csv_df.copy()
    csv_df["title_norm"] = csv_df["Title"].map(normalize_string)

    merged = json_df.merge(
        csv_df,
        on="title_norm",
        how="left"
    )

    matched = merged[merged["Title"].notna()].copy()

    if matched.empty:
        return matched

    matched["__dedup_key"] = build_unique_key(matched)

    unique_matched = (
        matched
        .drop_duplicates(subset="__dedup_key")
        .drop(columns="__dedup_key")
    )

    return unique_matched


# =========================================================
# EXPORTERS
# =========================================================

def export_csv(df: pd.DataFrame) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"curated_batch_{ts}.csv"
    df.to_csv(path, index=False)
    return path


def export_markdown(df: pd.DataFrame) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"curated_batch_{ts}.md"

    blocks = []
    blocks.append("# 📚 Curated Literature Dataset\n")
    blocks.append(f"_Generated at: {datetime.now().isoformat()}_")
    blocks.append(f"_Total papers: {len(df)}_\n")

    for _, row in df.iterrows():
        title = str(row.get("Title", "")).strip() or "Untitled"

        block = f"""
## {title}

- **DOI:** {row.get("DOI","")}
- **Authors:** {row.get("Authors","")}
- **Journal:** {row.get("Journal","")}
- **Year:** {row.get("Year","")}
- **Source File:** {row.get("__source_file","")}

### Abstract
{textwrap.fill(str(row.get("Abstract","")), width=100)}
"""
        blocks.append(block.strip())
        blocks.append("\n---\n")

    path.write_text("\n".join(blocks), encoding="utf-8")
    return path


# =========================================================
# DATA SOURCE SELECTION
# =========================================================

st.sidebar.header("📂 Dataset Selection")

files = discover_csv_files()

if not files:
    st.warning("⚠️ No CSV files found in data/csv/")
    st.stop()

selected_files = st.sidebar.multiselect(
    "Select CSV files to merge",
    files,
    default=files[:1],
    format_func=lambda p: p.name
)

if not selected_files:
    st.info("Please select at least one CSV file.")
    st.stop()

raw_df = load_multiple(selected_files)
st.sidebar.metric("Total loaded rows", len(raw_df))

# =========================================================
# UNIQUE MATCHED REFERENCES (IN MEMORY)
# =========================================================

registry_fp = directory_fingerprint(REGISTRY_DIR)
csv_fp = directory_fingerprint(CSV_DIR)

unique_matched = compute_unique_matched(registry_fp, csv_fp)

unique_reference_titles = set()

if not unique_matched.empty and "json_title" in unique_matched.columns:
    unique_reference_titles = {
        normalize_string(t)
        for t in unique_matched["json_title"].dropna()
    }

st.sidebar.caption(
    f"📌 Registry-covered titles detected: {len(unique_reference_titles)}"
)

# =========================================================
# TITLE EXCLUSION CONTROLS
# =========================================================

st.sidebar.divider()
st.sidebar.header("🚫 Title Exclusion")

# --- Manual select
all_titles = (
    raw_df["Title"]
    .dropna()
    .astype(str)
    .str.strip()
    .sort_values()
    .unique()
    .tolist()
    if "Title" in raw_df.columns else []
)

selected_titles = st.sidebar.multiselect(
    "Select titles to exclude",
    all_titles
)

# --- Paste titles
exclude_titles_text = st.sidebar.text_area(
    "Paste titles to exclude (one per line)",
    height=130
)

# --- Registry toggle
use_unique_refs = st.sidebar.checkbox(
    "Exclude titles already covered in registry",
    value=True
)

# =========================================================
# MERGE EXCLUSIONS
# =========================================================

manual_titles = {
    normalize_string(t) for t in selected_titles
}
pasted_titles = parse_excluded_titles(exclude_titles_text)

excluded_titles = manual_titles | pasted_titles

if use_unique_refs:
    excluded_titles |= unique_reference_titles

if excluded_titles:
    st.sidebar.caption(
        f"🧹 Excluding {len(excluded_titles)} titles "
        f"(Manual {len(manual_titles)}, "
        f"Pasted {len(pasted_titles)}, "
        f"Registry {len(unique_reference_titles) if use_unique_refs else 0})"
    )

# =========================================================
# FILTER CONTROLS
# =========================================================

st.sidebar.divider()
st.sidebar.header("🧪 Filters")

remove_missing_abstract = st.sidebar.checkbox(
    "Remove '(missing abstract)'", True
)
remove_empty_doi = st.sidebar.checkbox(
    "Remove empty DOI", True
)
remove_empty_title = st.sidebar.checkbox(
    "Remove empty Title", True
)
deduplicate = st.sidebar.checkbox(
    "Deduplicate (DOI + Title)", True
)

min_abstract_len = st.sidebar.slider(
    "Minimum abstract length",
    0, 500, 40
)

exclude_keywords = st.sidebar.text_input(
    "Exclude keywords in Abstract",
    placeholder="survey, review"
)

# Year filter
if "Year" in raw_df.columns:
    year_series = pd.to_numeric(raw_df["Year"], errors="coerce")
    year_min = int(year_series.min() or 1900)
    year_max = int(year_series.max() or datetime.now().year)

    year_range = st.sidebar.slider(
        "Year range",
        year_min,
        year_max,
        (year_min, year_max)
    )
else:
    year_range = None

# =========================================================
# APPLY FILTERS
# =========================================================

df = raw_df.copy()
removed_by_titles = 0

# --- Title exclusion
if excluded_titles and "Title" in df.columns:
    df["_title_norm"] = normalize_text(df["Title"])
    before = len(df)
    df = df[~df["_title_norm"].isin(excluded_titles)]
    removed_by_titles = before - len(df)
    df = df.drop(columns=["_title_norm"])

# --- Missing abstract
if "Abstract" in df.columns and remove_missing_abstract:
    df = df[
        normalize_text(df["Abstract"]) != "(missing abstract)"
    ]

# --- Empty DOI
if "DOI" in df.columns and remove_empty_doi:
    df = df[
        normalize_text(df["DOI"]) != ""
    ]

# --- Empty Title
if "Title" in df.columns and remove_empty_title:
    df = df[
        normalize_text(df["Title"]) != ""
    ]

# --- Year range
if year_range and "Year" in df.columns:
    df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df[
        (df["Year_num"] >= year_range[0]) &
        (df["Year_num"] <= year_range[1])
    ]

# --- Abstract length
if "Abstract" in df.columns and min_abstract_len > 0:
    df = df[
        df["Abstract"].astype(str).str.len() >= min_abstract_len
    ]

# --- Keyword exclusion
if "Abstract" in df.columns and exclude_keywords.strip():
    keywords = [
        k.strip().lower()
        for k in exclude_keywords.split(",")
        if k.strip()
    ]
    mask = df["Abstract"].astype(str).str.lower().apply(
        lambda txt: any(k in txt for k in keywords)
    )
    df = df[~mask]

# --- Deduplicate
if deduplicate and {"DOI", "Title"}.issubset(df.columns):
    df["_doi_norm"] = normalize_text(df["DOI"])
    df["_title_norm"] = normalize_text(df["Title"])
    df = df.drop_duplicates(subset=["_doi_norm", "_title_norm"])
    df = df.drop(columns=["_doi_norm", "_title_norm"])

df = df.drop(columns=["Year_num"], errors="ignore")

# =========================================================
# METRICS
# =========================================================

st.divider()
st.subheader("📊 Batch Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Loaded Rows", len(raw_df))
c2.metric("After Filtering", len(df))
c3.metric(
    "Unique Journals",
    df["Journal"].nunique(dropna=True) if "Journal" in df.columns else 0
)
c4.metric("Removed by Title Filter", removed_by_titles)

# =========================================================
# PREVIEW
# =========================================================

st.divider()
st.subheader("🔍 Preview")
st.dataframe(df.head(300), use_container_width=True)

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


# import pandas as pd
# import streamlit as st
# from pathlib import Path
# from datetime import datetime
# import textwrap

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📦 Literature Batch Curator & Exporter",
#     layout="wide"
# )

# st.title("📦 Literature Batch Curator & Exporter")
# st.caption("Batch select CSV datasets from data/csv, curate them, and export to CSV or Markdown")

# # =========================================================
# # GLOBAL RELOAD CONTROL
# # =========================================================

# with st.sidebar:
#     st.divider()
#     if st.button("🔄 Reload Data"):
#         st.cache_data.clear()
#         st.toast("Cache cleared — reloading data...")
#         st.rerun()

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# CSV_DIR = BASE_DIR / "data" / "csv"
# EXPORT_DIR = BASE_DIR / "outputs"

# CSV_DIR.mkdir(parents=True, exist_ok=True)
# EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
# st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# @st.cache_data
# def discover_csv_files():
#     return sorted(CSV_DIR.glob("*.csv"))


# @st.cache_data
# def load_csv(path: Path) -> pd.DataFrame:
#     df = pd.read_csv(path)
#     df.columns = df.columns.str.strip()
#     return df


# def load_multiple(files):
#     frames = []
#     for f in files:
#         df = load_csv(f)
#         df["__source_file"] = f.name
#         frames.append(df)
#     return pd.concat(frames, ignore_index=True)


# def export_csv(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.csv"
#     df.to_csv(path, index=False)
#     return path


# def export_markdown(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.md"

#     blocks = []
#     blocks.append("# 📚 Curated Literature Dataset\n")
#     blocks.append(f"_Generated at: {datetime.now().isoformat()}_")
#     blocks.append(f"_Total papers: {len(df)}_\n")

#     for _, row in df.iterrows():
#         title = str(row.get("Title", "")).strip() or "Untitled"

#         block = f"""
# ## {title}

# - **DOI:** {row.get("DOI","")}
# - **Authors:** {row.get("Authors","")}
# - **Journal:** {row.get("Journal","")}
# - **Year:** {row.get("Year","")}
# - **Source File:** {row.get("__source_file","")}

# ### Abstract
# {textwrap.fill(str(row.get("Abstract","")), width=100)}
# """
#         blocks.append(block.strip())
#         blocks.append("\n---\n")

#     path.write_text("\n".join(blocks), encoding="utf-8")
#     return path


# def normalize_text(series):
#     return series.astype(str).str.strip().str.lower()


# def normalize_string(text: str):
#     return str(text).strip().lower()


# def parse_excluded_titles(text: str):
#     return {
#         normalize_string(line)
#         for line in text.splitlines()
#         if line.strip()
#     }


# # =========================================================
# # DATA SOURCE SELECTION
# # =========================================================

# st.sidebar.header("📂 Dataset Selection")

# files = discover_csv_files()

# if not files:
#     st.warning("⚠️ No CSV files found in data/csv/")
#     st.stop()

# selected_files = st.sidebar.multiselect(
#     "Select CSV files to merge",
#     files,
#     default=files[:1],
#     format_func=lambda p: p.name
# )

# if not selected_files:
#     st.info("Please select at least one CSV file.")
#     st.stop()

# raw_df = load_multiple(selected_files)
# st.sidebar.metric("Total loaded rows", len(raw_df))

# # =========================================================
# # TITLE EXCLUSION (BOTH MODES)
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🚫 Title Exclusion")

# # --- Dropdown selection
# all_titles = (
#     raw_df["Title"]
#     .dropna()
#     .astype(str)
#     .str.strip()
#     .sort_values()
#     .unique()
#     .tolist()
#     if "Title" in raw_df.columns else []
# )

# selected_titles = st.sidebar.multiselect(
#     "Select titles to exclude (click)",
#     all_titles,
#     help="Click-select titles to remove"
# )

# # --- Paste box
# exclude_titles_text = st.sidebar.text_area(
#     "Paste titles to exclude (one per line)",
#     placeholder=(
#         "Paste exact paper titles here.\n"
#         "One title per line.\n\n"
#         "Example:\n"
#         "MEXMA: Token-level objectives improve sentence representations\n"
#         "LACA: Improving Cross-lingual Aspect-Based Sentiment Analysis with LLM Data Augmentation"
#     ),
#     height=160
# )

# # --- Merge both sources
# excluded_titles = {
#     normalize_string(t) for t in selected_titles
# }.union(
#     parse_excluded_titles(exclude_titles_text)
# )

# if excluded_titles:
#     st.sidebar.caption(f"🧹 {len(excluded_titles)} titles selected for exclusion")

# # =========================================================
# # FILTER CONTROLS
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🧪 Filters")

# remove_missing_abstract = st.sidebar.checkbox(
#     "Remove '(missing abstract)'", True
# )

# remove_empty_doi = st.sidebar.checkbox(
#     "Remove empty DOI", True
# )

# remove_empty_title = st.sidebar.checkbox(
#     "Remove empty Title", True
# )

# deduplicate = st.sidebar.checkbox(
#     "Deduplicate (DOI + Title)", True
# )

# min_abstract_len = st.sidebar.slider(
#     "Minimum abstract length",
#     0, 500, 40
# )

# exclude_keywords = st.sidebar.text_input(
#     "Exclude keywords in Abstract",
#     placeholder="survey, review"
# )

# # Year filter
# if "Year" in raw_df.columns:
#     year_series = pd.to_numeric(raw_df["Year"], errors="coerce")
#     year_min = int(year_series.min() or 1900)
#     year_max = int(year_series.max() or datetime.now().year)

#     year_range = st.sidebar.slider(
#         "Year range",
#         year_min,
#         year_max,
#         (year_min, year_max)
#     )
# else:
#     year_range = None

# # =========================================================
# # APPLY FILTERS
# # =========================================================

# df = raw_df.copy()
# removed_by_titles = 0

# # --- Title exclusion
# if excluded_titles and "Title" in df.columns:
#     df["_title_norm"] = normalize_text(df["Title"])
#     before = len(df)
#     df = df[~df["_title_norm"].isin(excluded_titles)]
#     removed_by_titles = before - len(df)
#     df = df.drop(columns=["_title_norm"])

# # --- Missing abstract
# if "Abstract" in df.columns and remove_missing_abstract:
#     df = df[
#         normalize_text(df["Abstract"]) != "(missing abstract)"
#     ]

# # --- Empty DOI
# if "DOI" in df.columns and remove_empty_doi:
#     df = df[
#         normalize_text(df["DOI"]) != ""
#     ]

# # --- Empty Title
# if "Title" in df.columns and remove_empty_title:
#     df = df[
#         normalize_text(df["Title"]) != ""
#     ]

# # --- Year range
# if year_range and "Year" in df.columns:
#     df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
#     df = df[
#         (df["Year_num"] >= year_range[0]) &
#         (df["Year_num"] <= year_range[1])
#     ]

# # --- Abstract length
# if "Abstract" in df.columns and min_abstract_len > 0:
#     df = df[
#         df["Abstract"].astype(str).str.len() >= min_abstract_len
#     ]

# # --- Keyword exclusion
# if "Abstract" in df.columns and exclude_keywords.strip():
#     keywords = [
#         k.strip().lower()
#         for k in exclude_keywords.split(",")
#         if k.strip()
#     ]
#     mask = df["Abstract"].astype(str).str.lower().apply(
#         lambda txt: any(k in txt for k in keywords)
#     )
#     df = df[~mask]

# # --- Deduplicate
# if deduplicate and {"DOI", "Title"}.issubset(df.columns):
#     df["_doi_norm"] = normalize_text(df["DOI"])
#     df["_title_norm"] = normalize_text(df["Title"])
#     df = df.drop_duplicates(subset=["_doi_norm", "_title_norm"])
#     df = df.drop(columns=["_doi_norm", "_title_norm"])

# df = df.drop(columns=["Year_num"], errors="ignore")

# # =========================================================
# # METRICS
# # =========================================================

# st.divider()
# st.subheader("📊 Batch Summary")

# c1, c2, c3, c4 = st.columns(4)
# c1.metric("Loaded Rows", len(raw_df))
# c2.metric("After Filtering", len(df))
# c3.metric(
#     "Unique Journals",
#     df["Journal"].nunique(dropna=True) if "Journal" in df.columns else 0
# )
# c4.metric("Removed by Title Filter", removed_by_titles)

# # =========================================================
# # PREVIEW
# # =========================================================

# st.divider()
# st.subheader("🔍 Preview")
# st.dataframe(df.head(300), use_container_width=True)

# # =========================================================
# # EXPORT
# # =========================================================

# st.divider()
# st.subheader("💾 Export")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("⬇️ Export CSV", type="primary"):
#         path = export_csv(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download CSV",
#                 f,
#                 file_name=path.name,
#                 mime="text/csv"
#             )
#         st.success(f"Saved to: {path}")

# with col2:
#     if st.button("📝 Export Markdown"):
#         path = export_markdown(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download Markdown",
#                 f,
#                 file_name=path.name,
#                 mime="text/markdown"
#             )
#         st.success(f"Saved to: {path}")


# import pandas as pd
# import streamlit as st
# from pathlib import Path
# from datetime import datetime
# import textwrap

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📦 Literature Batch Curator & Exporter",
#     layout="wide"
# )

# st.title("📦 Literature Batch Curator & Exporter")
# st.caption("Batch select CSV datasets from data/csv, curate them, and export to CSV or Markdown")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# CSV_DIR = BASE_DIR / "data" / "csv"
# EXPORT_DIR = BASE_DIR / "outputs"

# CSV_DIR.mkdir(parents=True, exist_ok=True)
# EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
# st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# @st.cache_data
# def discover_csv_files():
#     return sorted(CSV_DIR.glob("*.csv"))


# @st.cache_data
# def load_csv(path: Path) -> pd.DataFrame:
#     df = pd.read_csv(path)
#     df.columns = df.columns.str.strip()
#     return df


# def load_multiple(files):
#     frames = []
#     for f in files:
#         df = load_csv(f)
#         df["__source_file"] = f.name
#         frames.append(df)
#     return pd.concat(frames, ignore_index=True)


# def export_csv(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.csv"
#     df.to_csv(path, index=False)
#     return path


# def export_markdown(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.md"

#     blocks = []
#     blocks.append("# 📚 Curated Literature Dataset\n")
#     blocks.append(f"_Generated at: {datetime.now().isoformat()}_")
#     blocks.append(f"_Total papers: {len(df)}_\n")

#     for _, row in df.iterrows():
#         title = str(row.get("Title", "")).strip() or "Untitled"

#         block = f"""
# ## {title}

# - **DOI:** {row.get("DOI","")}
# - **Authors:** {row.get("Authors","")}
# - **Journal:** {row.get("Journal","")}
# - **Year:** {row.get("Year","")}
# - **Source File:** {row.get("__source_file","")}

# ### Abstract
# {textwrap.fill(str(row.get("Abstract","")), width=100)}
# """
#         blocks.append(block.strip())
#         blocks.append("\n---\n")

#     path.write_text("\n".join(blocks), encoding="utf-8")
#     return path


# def normalize_text(series):
#     return series.astype(str).str.strip().str.lower()


# def normalize_string(text: str):
#     return str(text).strip().lower()


# def parse_excluded_titles(text: str):
#     return {
#         normalize_string(line)
#         for line in text.splitlines()
#         if line.strip()
#     }


# # =========================================================
# # DATA SOURCE SELECTION
# # =========================================================

# st.sidebar.header("📂 Dataset Selection")

# files = discover_csv_files()

# if not files:
#     st.warning("⚠️ No CSV files found in data/csv/")
#     st.stop()

# selected_files = st.sidebar.multiselect(
#     "Select CSV files to merge",
#     files,
#     default=files[:1],
#     format_func=lambda p: p.name
# )

# if not selected_files:
#     st.info("Please select at least one CSV file.")
#     st.stop()

# raw_df = load_multiple(selected_files)
# st.sidebar.metric("Total loaded rows", len(raw_df))

# # =========================================================
# # TITLE EXCLUSION (BOTH MODES)
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🚫 Title Exclusion")

# # --- Dropdown selection
# all_titles = (
#     raw_df["Title"]
#     .dropna()
#     .astype(str)
#     .str.strip()
#     .sort_values()
#     .unique()
#     .tolist()
#     if "Title" in raw_df.columns else []
# )

# selected_titles = st.sidebar.multiselect(
#     "Select titles to exclude (click)",
#     all_titles,
#     help="Click-select titles to remove"
# )

# # --- Paste box
# exclude_titles_text = st.sidebar.text_area(
#     "Paste titles to exclude (one per line)",
#     placeholder=(
#         "Paste exact paper titles here.\n"
#         "One title per line.\n\n"
#         "Example:\n"
#         "MEXMA: Token-level objectives improve sentence representations\n"
#         "LACA: Improving Cross-lingual Aspect-Based Sentiment Analysis with LLM Data Augmentation"
#     ),
#     height=160
# )

# # --- Merge both sources
# excluded_titles = {
#     normalize_string(t) for t in selected_titles
# }.union(
#     parse_excluded_titles(exclude_titles_text)
# )

# if excluded_titles:
#     st.sidebar.caption(f"🧹 {len(excluded_titles)} titles selected for exclusion")

# # =========================================================
# # FILTER CONTROLS
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🧪 Filters")

# remove_missing_abstract = st.sidebar.checkbox(
#     "Remove '(missing abstract)'", True
# )

# remove_empty_doi = st.sidebar.checkbox(
#     "Remove empty DOI", True
# )

# remove_empty_title = st.sidebar.checkbox(
#     "Remove empty Title", True
# )

# deduplicate = st.sidebar.checkbox(
#     "Deduplicate (DOI + Title)", True
# )

# min_abstract_len = st.sidebar.slider(
#     "Minimum abstract length",
#     0, 500, 40
# )

# exclude_keywords = st.sidebar.text_input(
#     "Exclude keywords in Abstract",
#     placeholder="survey, review"
# )

# # Year filter
# if "Year" in raw_df.columns:
#     year_series = pd.to_numeric(raw_df["Year"], errors="coerce")
#     year_min = int(year_series.min() or 1900)
#     year_max = int(year_series.max() or datetime.now().year)

#     year_range = st.sidebar.slider(
#         "Year range",
#         year_min,
#         year_max,
#         (year_min, year_max)
#     )
# else:
#     year_range = None

# # =========================================================
# # APPLY FILTERS
# # =========================================================

# df = raw_df.copy()
# removed_by_titles = 0

# # --- Title exclusion
# if excluded_titles and "Title" in df.columns:
#     df["_title_norm"] = normalize_text(df["Title"])
#     before = len(df)
#     df = df[~df["_title_norm"].isin(excluded_titles)]
#     removed_by_titles = before - len(df)
#     df = df.drop(columns=["_title_norm"])

# # --- Missing abstract
# if "Abstract" in df.columns and remove_missing_abstract:
#     df = df[
#         normalize_text(df["Abstract"]) != "(missing abstract)"
#     ]

# # --- Empty DOI
# if "DOI" in df.columns and remove_empty_doi:
#     df = df[
#         normalize_text(df["DOI"]) != ""
#     ]

# # --- Empty Title
# if "Title" in df.columns and remove_empty_title:
#     df = df[
#         normalize_text(df["Title"]) != ""
#     ]

# # --- Year range
# if year_range and "Year" in df.columns:
#     df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
#     df = df[
#         (df["Year_num"] >= year_range[0]) &
#         (df["Year_num"] <= year_range[1])
#     ]

# # --- Abstract length
# if "Abstract" in df.columns and min_abstract_len > 0:
#     df = df[
#         df["Abstract"].astype(str).str.len() >= min_abstract_len
#     ]

# # --- Keyword exclusion
# if "Abstract" in df.columns and exclude_keywords.strip():
#     keywords = [
#         k.strip().lower()
#         for k in exclude_keywords.split(",")
#         if k.strip()
#     ]
#     mask = df["Abstract"].astype(str).str.lower().apply(
#         lambda txt: any(k in txt for k in keywords)
#     )
#     df = df[~mask]

# # --- Deduplicate
# if deduplicate and {"DOI", "Title"}.issubset(df.columns):
#     df["_doi_norm"] = normalize_text(df["DOI"])
#     df["_title_norm"] = normalize_text(df["Title"])
#     df = df.drop_duplicates(subset=["_doi_norm", "_title_norm"])
#     df = df.drop(columns=["_doi_norm", "_title_norm"])

# df = df.drop(columns=["Year_num"], errors="ignore")

# # =========================================================
# # METRICS
# # =========================================================

# st.divider()
# st.subheader("📊 Batch Summary")

# c1, c2, c3, c4 = st.columns(4)
# c1.metric("Loaded Rows", len(raw_df))
# c2.metric("After Filtering", len(df))
# c3.metric(
#     "Unique Journals",
#     df["Journal"].nunique(dropna=True) if "Journal" in df.columns else 0
# )
# c4.metric("Removed by Title Filter", removed_by_titles)

# # =========================================================
# # PREVIEW
# # =========================================================

# st.divider()
# st.subheader("🔍 Preview")
# st.dataframe(df.head(300), use_container_width=True)

# # =========================================================
# # EXPORT
# # =========================================================

# st.divider()
# st.subheader("💾 Export")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("⬇️ Export CSV", type="primary"):
#         path = export_csv(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download CSV",
#                 f,
#                 file_name=path.name,
#                 mime="text/csv"
#             )
#         st.success(f"Saved to: {path}")

# with col2:
#     if st.button("📝 Export Markdown"):
#         path = export_markdown(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download Markdown",
#                 f,
#                 file_name=path.name,
#                 mime="text/markdown"
#             )
#         st.success(f"Saved to: {path}")


# import pandas as pd
# import streamlit as st
# from pathlib import Path
# from datetime import datetime
# import textwrap

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📦 Literature Batch Curator & Exporter",
#     layout="wide"
# )

# st.title("📦 Literature Batch Curator & Exporter")
# st.caption("Batch select CSV datasets from data/csv, curate them, and export to CSV or Markdown")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# CSV_DIR = BASE_DIR / "data" / "csv"
# EXPORT_DIR = BASE_DIR / "outputs"

# CSV_DIR.mkdir(parents=True, exist_ok=True)
# EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
# st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# @st.cache_data
# def discover_csv_files():
#     return sorted(CSV_DIR.glob("*.csv"))


# @st.cache_data
# def load_csv(path: Path) -> pd.DataFrame:
#     df = pd.read_csv(path)
#     df.columns = df.columns.str.strip()
#     return df


# def load_multiple(files):
#     frames = []
#     for f in files:
#         df = load_csv(f)
#         df["__source_file"] = f.name
#         frames.append(df)
#     return pd.concat(frames, ignore_index=True)


# def export_csv(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.csv"
#     df.to_csv(path, index=False)
#     return path


# def export_markdown(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.md"

#     blocks = []
#     blocks.append("# 📚 Curated Literature Dataset\n")
#     blocks.append(f"_Generated at: {datetime.now().isoformat()}_")
#     blocks.append(f"_Total papers: {len(df)}_\n")

#     for idx, row in df.iterrows():
#         title = str(row.get("Title", "")).strip() or "Untitled"

#         block = f"""
# ## {title}

# - **DOI:** {row.get("DOI","")}
# - **Authors:** {row.get("Authors","")}
# - **Journal:** {row.get("Journal","")}
# - **Year:** {row.get("Year","")}
# - **Source File:** {row.get("__source_file","")}

# ### Abstract
# {textwrap.fill(str(row.get("Abstract","")), width=100)}
# """
#         blocks.append(block.strip())
#         blocks.append("\n---\n")

#     path.write_text("\n".join(blocks), encoding="utf-8")
#     return path


# def normalize_text(series):
#     return series.astype(str).str.strip().str.lower()


# def parse_excluded_titles(text: str):
#     """
#     Parse pasted multi-line titles into a normalized set.
#     """
#     return {
#         line.strip().lower()
#         for line in text.splitlines()
#         if line.strip()
#     }


# # =========================================================
# # DATA SOURCE SELECTION
# # =========================================================

# st.sidebar.header("📂 Dataset Selection")

# files = discover_csv_files()

# if not files:
#     st.warning("⚠️ No CSV files found in data/csv/")
#     st.stop()

# selected_files = st.sidebar.multiselect(
#     "Select CSV files to merge",
#     files,
#     default=files[:1],
#     format_func=lambda p: p.name
# )

# if not selected_files:
#     st.info("Please select at least one CSV file.")
#     st.stop()

# raw_df = load_multiple(selected_files)
# st.sidebar.metric("Total loaded rows", len(raw_df))

# # =========================================================
# # TITLE EXCLUSION (PASTE LIST)
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🚫 Title Exclusion")

# exclude_titles_text = st.sidebar.text_area(
#     "Exclude Titles (one per line)",
#     placeholder=(
#         "Paste exact paper titles here.\n"
#         "One title per line.\n\n"
#         "Example:\n"
#         "MEXMA: Token-level objectives improve sentence representations\n"
#         "LACA: Improving Cross-lingual Aspect-Based Sentiment Analysis with LLM Data Augmentation"
#     ),
#     height=200
# )

# excluded_titles = parse_excluded_titles(exclude_titles_text)

# if excluded_titles:
#     st.sidebar.caption(f"🧹 {len(excluded_titles)} titles loaded for exclusion")

# # =========================================================
# # FILTER CONTROLS
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🧪 Filters")

# remove_missing_abstract = st.sidebar.checkbox(
#     "Remove '(missing abstract)'", True
# )

# remove_empty_doi = st.sidebar.checkbox(
#     "Remove empty DOI", True
# )

# remove_empty_title = st.sidebar.checkbox(
#     "Remove empty Title", True
# )

# deduplicate = st.sidebar.checkbox(
#     "Deduplicate (DOI + Title)", True
# )

# min_abstract_len = st.sidebar.slider(
#     "Minimum abstract length",
#     0, 500, 40
# )

# exclude_keywords = st.sidebar.text_input(
#     "Exclude keywords in Abstract",
#     placeholder="survey, review"
# )

# # Year filter
# if "Year" in raw_df.columns:
#     year_series = pd.to_numeric(raw_df["Year"], errors="coerce")
#     year_min = int(year_series.min() or 1900)
#     year_max = int(year_series.max() or datetime.now().year)

#     year_range = st.sidebar.slider(
#         "Year range",
#         year_min,
#         year_max,
#         (year_min, year_max)
#     )
# else:
#     year_range = None

# # =========================================================
# # APPLY FILTERS
# # =========================================================

# df = raw_df.copy()
# removed_by_titles = 0

# # --- Title exclusion (manual pasted list)
# if excluded_titles and "Title" in df.columns:
#     df["_title_norm"] = normalize_text(df["Title"])
#     before = len(df)
#     df = df[~df["_title_norm"].isin(excluded_titles)]
#     removed_by_titles = before - len(df)
#     df = df.drop(columns=["_title_norm"])

# # --- Missing abstract
# if "Abstract" in df.columns and remove_missing_abstract:
#     df = df[
#         normalize_text(df["Abstract"]) != "(missing abstract)"
#     ]

# # --- Empty DOI
# if "DOI" in df.columns and remove_empty_doi:
#     df = df[
#         normalize_text(df["DOI"]) != ""
#     ]

# # --- Empty Title
# if "Title" in df.columns and remove_empty_title:
#     df = df[
#         normalize_text(df["Title"]) != ""
#     ]

# # --- Year range
# if year_range and "Year" in df.columns:
#     df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
#     df = df[
#         (df["Year_num"] >= year_range[0]) &
#         (df["Year_num"] <= year_range[1])
#     ]

# # --- Abstract length
# if "Abstract" in df.columns and min_abstract_len > 0:
#     df = df[
#         df["Abstract"].astype(str).str.len() >= min_abstract_len
#     ]

# # --- Keyword exclusion
# if "Abstract" in df.columns and exclude_keywords.strip():
#     keywords = [
#         k.strip().lower()
#         for k in exclude_keywords.split(",")
#         if k.strip()
#     ]
#     mask = df["Abstract"].astype(str).str.lower().apply(
#         lambda txt: any(k in txt for k in keywords)
#     )
#     df = df[~mask]

# # --- Deduplicate
# if deduplicate and {"DOI", "Title"}.issubset(df.columns):
#     df["_doi_norm"] = normalize_text(df["DOI"])
#     df["_title_norm"] = normalize_text(df["Title"])
#     df = df.drop_duplicates(subset=["_doi_norm", "_title_norm"])
#     df = df.drop(columns=["_doi_norm", "_title_norm"])

# df = df.drop(columns=["Year_num"], errors="ignore")

# # =========================================================
# # METRICS
# # =========================================================

# st.divider()
# st.subheader("📊 Batch Summary")

# c1, c2, c3, c4 = st.columns(4)
# c1.metric("Loaded Rows", len(raw_df))
# c2.metric("After Filtering", len(df))
# c3.metric(
#     "Unique Journals",
#     df["Journal"].nunique(dropna=True) if "Journal" in df.columns else 0
# )
# c4.metric("Removed by Title List", removed_by_titles)

# # =========================================================
# # PREVIEW
# # =========================================================

# st.divider()
# st.subheader("🔍 Preview")
# st.dataframe(df.head(300), use_container_width=True)

# # =========================================================
# # EXPORT
# # =========================================================

# st.divider()
# st.subheader("💾 Export")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("⬇️ Export CSV", type="primary"):
#         path = export_csv(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download CSV",
#                 f,
#                 file_name=path.name,
#                 mime="text/csv"
#             )
#         st.success(f"Saved to: {path}")

# with col2:
#     if st.button("📝 Export Markdown"):
#         path = export_markdown(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download Markdown",
#                 f,
#                 file_name=path.name,
#                 mime="text/markdown"
#             )
#         st.success(f"Saved to: {path}")


# import pandas as pd
# import streamlit as st
# from pathlib import Path
# from datetime import datetime
# import textwrap

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📦 Literature Batch Curator & Exporter",
#     layout="wide"
# )

# st.title("📦 Literature Batch Curator & Exporter")
# st.caption("Batch select CSV datasets from data/csv, curate them, and export to CSV or Markdown")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# CSV_DIR = BASE_DIR / "data" / "csv"
# EXPORT_DIR = BASE_DIR / "outputs"

# CSV_DIR.mkdir(parents=True, exist_ok=True)
# EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
# st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# @st.cache_data
# def discover_csv_files():
#     return sorted(CSV_DIR.glob("*.csv"))


# @st.cache_data
# def load_csv(path: Path) -> pd.DataFrame:
#     df = pd.read_csv(path)
#     df.columns = df.columns.str.strip()
#     return df


# def load_multiple(files):
#     frames = []
#     for f in files:
#         df = load_csv(f)
#         df["__source_file"] = f.name
#         frames.append(df)
#     return pd.concat(frames, ignore_index=True)


# def export_csv(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.csv"
#     df.to_csv(path, index=False)
#     return path


# def export_markdown(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.md"

#     blocks = []
#     blocks.append("# 📚 Curated Literature Dataset\n")
#     blocks.append(f"_Generated at: {datetime.now().isoformat()}_")
#     blocks.append(f"_Total papers: {len(df)}_\n")

#     for idx, row in df.iterrows():
#         title = str(row.get("Title", "")).strip() or "Untitled"

#         block = f"""
# ## {title}

# - **DOI:** {row.get("DOI","")}
# - **Authors:** {row.get("Authors","")}
# - **Journal:** {row.get("Journal","")}
# - **Year:** {row.get("Year","")}
# - **Source File:** {row.get("__source_file","")}

# ### Abstract
# {textwrap.fill(str(row.get("Abstract","")), width=100)}
# """
#         blocks.append(block.strip())
#         blocks.append("\n---\n")

#     path.write_text("\n".join(blocks), encoding="utf-8")
#     return path


# def normalize_text(series):
#     return series.astype(str).str.strip().str.lower()


# # =========================================================
# # DATA SOURCE SELECTION
# # =========================================================

# st.sidebar.header("📂 Dataset Selection")

# files = discover_csv_files()

# if not files:
#     st.warning("⚠️ No CSV files found in data/csv/")
#     st.stop()

# selected_files = st.sidebar.multiselect(
#     "Select CSV files to merge",
#     files,
#     default=files[:1],
#     format_func=lambda p: p.name
# )

# if not selected_files:
#     st.info("Please select at least one CSV file.")
#     st.stop()

# raw_df = load_multiple(selected_files)
# st.sidebar.metric("Total loaded rows", len(raw_df))

# # =========================================================
# # JOURNAL EXCLUSION (NEW)
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🏷️ Journal Filter")

# if "Title" in raw_df.columns:
#     journals = (
#         raw_df["Title"]
#         .dropna()
#         .astype(str)
#         .str.strip()
#         .sort_values()
#         .unique()
#         .tolist()
#     )

#     excluded_journals = st.sidebar.multiselect(
#         "Exclude titles",
#         journals,
#         help="Remove all papers published in selected journals"
#     )
# else:
#     excluded_journals = []
#     st.sidebar.info("No Journal column detected.")

# # =========================================================
# # FILTER CONTROLS
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🧪 Filters")

# remove_missing_abstract = st.sidebar.checkbox(
#     "Remove '(missing abstract)'", True
# )

# remove_empty_doi = st.sidebar.checkbox(
#     "Remove empty DOI", True
# )

# remove_empty_title = st.sidebar.checkbox(
#     "Remove empty Title", True
# )

# deduplicate = st.sidebar.checkbox(
#     "Deduplicate (DOI + Title)", True
# )

# min_abstract_len = st.sidebar.slider(
#     "Minimum abstract length",
#     0, 500, 40
# )

# exclude_keywords = st.sidebar.text_input(
#     "Exclude keywords in Abstract",
#     placeholder="survey, review"
# )

# # Year filter
# if "Year" in raw_df.columns:
#     year_series = pd.to_numeric(raw_df["Year"], errors="coerce")
#     year_min = int(year_series.min() or 1900)
#     year_max = int(year_series.max() or datetime.now().year)

#     year_range = st.sidebar.slider(
#         "Year range",
#         year_min,
#         year_max,
#         (year_min, year_max)
#     )
# else:
#     year_range = None

# # =========================================================
# # APPLY FILTERS
# # =========================================================

# df = raw_df.copy()

# # --- Journal exclusion
# if excluded_journals and "Journal" in df.columns:
#     excluded_norm = [j.strip().lower() for j in excluded_journals]
#     df = df[
#         ~df["Journal"]
#         .astype(str)
#         .str.strip()
#         .str.lower()
#         .isin(excluded_norm)
#     ]

# # --- Missing abstract
# if "Abstract" in df.columns and remove_missing_abstract:
#     df = df[
#         normalize_text(df["Abstract"]) != "(missing abstract)"
#     ]

# # --- Empty DOI
# if "DOI" in df.columns and remove_empty_doi:
#     df = df[
#         normalize_text(df["DOI"]) != ""
#     ]

# # --- Empty Title
# if "Title" in df.columns and remove_empty_title:
#     df = df[
#         normalize_text(df["Title"]) != ""
#     ]

# # --- Year range
# if year_range and "Year" in df.columns:
#     df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
#     df = df[
#         (df["Year_num"] >= year_range[0]) &
#         (df["Year_num"] <= year_range[1])
#     ]

# # --- Abstract length
# if "Abstract" in df.columns and min_abstract_len > 0:
#     df = df[
#         df["Abstract"].astype(str).str.len() >= min_abstract_len
#     ]

# # --- Keyword exclusion
# if "Abstract" in df.columns and exclude_keywords.strip():
#     keywords = [
#         k.strip().lower()
#         for k in exclude_keywords.split(",")
#         if k.strip()
#     ]
#     mask = df["Abstract"].astype(str).str.lower().apply(
#         lambda txt: any(k in txt for k in keywords)
#     )
#     df = df[~mask]

# # --- Deduplicate
# if deduplicate and {"DOI", "Title"}.issubset(df.columns):
#     df["_doi_norm"] = normalize_text(df["DOI"])
#     df["_title_norm"] = normalize_text(df["Title"])
#     df = df.drop_duplicates(subset=["_doi_norm", "_title_norm"])
#     df = df.drop(columns=["_doi_norm", "_title_norm"])

# df = df.drop(columns=["Year_num"], errors="ignore")

# # =========================================================
# # METRICS
# # =========================================================

# st.divider()
# st.subheader("📊 Batch Summary")

# c1, c2, c3 = st.columns(3)
# c1.metric("Loaded Rows", len(raw_df))
# c2.metric("After Filtering", len(df))
# c3.metric("Unique Journals", df["Journal"].nunique(dropna=True) if "Journal" in df.columns else 0)

# # =========================================================
# # PREVIEW
# # =========================================================

# st.divider()
# st.subheader("🔍 Preview")
# st.dataframe(df.head(300), use_container_width=True)

# # =========================================================
# # EXPORT
# # =========================================================

# st.divider()
# st.subheader("💾 Export")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("⬇️ Export CSV", type="primary"):
#         path = export_csv(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download CSV",
#                 f,
#                 file_name=path.name,
#                 mime="text/csv"
#             )
#         st.success(f"Saved to: {path}")

# with col2:
#     if st.button("📝 Export Markdown"):
#         path = export_markdown(df)
#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download Markdown",
#                 f,
#                 file_name=path.name,
#                 mime="text/markdown"
#             )
#         st.success(f"Saved to: {path}")


# import pandas as pd
# import streamlit as st
# from pathlib import Path
# from datetime import datetime
# import textwrap

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📦 Literature Batch Curator & Exporter",
#     layout="wide"
# )

# st.title("📦 Literature Batch Curator & Exporter")
# st.caption("Batch select CSV datasets from data/csv, curate them, and export to CSV or Markdown")

# # =========================================================
# # PATH CONFIG (ALIGNED WITH YOUR PROJECT)
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# CSV_DIR = BASE_DIR / "data" / "csv"
# EXPORT_DIR = BASE_DIR / "outputs"

# CSV_DIR.mkdir(parents=True, exist_ok=True)
# EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
# st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# @st.cache_data
# def discover_csv_files():
#     return sorted(CSV_DIR.glob("*.csv"))


# @st.cache_data
# def load_csv(path: Path) -> pd.DataFrame:
#     df = pd.read_csv(path)
#     df.columns = df.columns.str.strip()
#     return df


# def load_multiple(files):
#     frames = []
#     for f in files:
#         df = load_csv(f)
#         df["__source_file"] = f.name
#         frames.append(df)
#     return pd.concat(frames, ignore_index=True)


# def export_csv(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.csv"
#     df.to_csv(path, index=False)
#     return path


# def export_markdown(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = EXPORT_DIR / f"curated_batch_{ts}.md"

#     blocks = []
#     blocks.append("# 📚 Curated Literature Dataset\n")
#     blocks.append(f"_Generated at: {datetime.now().isoformat()}_")
#     blocks.append(f"_Total papers: {len(df)}_\n")

#     for idx, row in df.iterrows():
#         title = str(row.get("Title", "")).strip() or "Untitled"

#         block = f"""
# ## {title}

# - **DOI:** {row.get("DOI","")}
# - **Authors:** {row.get("Authors","")}
# - **Journal:** {row.get("Journal","")}
# - **Year:** {row.get("Year","")}
# - **Source File:** {row.get("__source_file","")}

# ### Abstract
# {textwrap.fill(str(row.get("Abstract","")), width=100)}
# """
#         blocks.append(block.strip())
#         blocks.append("\n---\n")

#     path.write_text("\n".join(blocks), encoding="utf-8")
#     return path


# def normalize_text(series):
#     return series.astype(str).str.strip().str.lower()


# # =========================================================
# # DATA SOURCE SELECTION
# # =========================================================

# st.sidebar.header("📂 Dataset Selection")

# files = discover_csv_files()

# if not files:
#     st.warning("⚠️ No CSV files found in data/csv/")
#     st.stop()

# selected_files = st.sidebar.multiselect(
#     "Select CSV files to merge",
#     files,
#     default=files[:1],
#     format_func=lambda p: p.name
# )

# if not selected_files:
#     st.info("Please select at least one CSV file.")
#     st.stop()

# raw_df = load_multiple(selected_files)

# st.sidebar.metric("Total loaded rows", len(raw_df))

# # =========================================================
# # FILTER CONTROLS
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🧪 Filters")

# remove_missing_abstract = st.sidebar.checkbox(
#     "Remove '(missing abstract)'", True
# )

# remove_empty_doi = st.sidebar.checkbox(
#     "Remove empty DOI", True
# )

# remove_empty_title = st.sidebar.checkbox(
#     "Remove empty Title", True
# )

# deduplicate = st.sidebar.checkbox(
#     "Deduplicate (DOI + Title)", True
# )

# min_abstract_len = st.sidebar.slider(
#     "Minimum abstract length",
#     0, 500, 40
# )

# exclude_keywords = st.sidebar.text_input(
#     "Exclude keywords in Abstract",
#     placeholder="survey, review"
# )

# # Year filter (if exists)
# if "Year" in raw_df.columns:
#     year_series = pd.to_numeric(raw_df["Year"], errors="coerce")
#     year_min = int(year_series.min() or 1900)
#     year_max = int(year_series.max() or datetime.now().year)

#     year_range = st.sidebar.slider(
#         "Year range",
#         year_min,
#         year_max,
#         (year_min, year_max)
#     )
# else:
#     year_range = None

# # =========================================================
# # APPLY FILTERS
# # =========================================================

# df = raw_df.copy()

# if "Abstract" in df.columns and remove_missing_abstract:
#     df = df[
#         normalize_text(df["Abstract"]) != "(missing abstract)"
#     ]

# if "DOI" in df.columns and remove_empty_doi:
#     df = df[
#         normalize_text(df["DOI"]) != ""
#     ]

# if "Title" in df.columns and remove_empty_title:
#     df = df[
#         normalize_text(df["Title"]) != ""
#     ]

# if year_range and "Year" in df.columns:
#     df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
#     df = df[
#         (df["Year_num"] >= year_range[0]) &
#         (df["Year_num"] <= year_range[1])
#     ]

# if "Abstract" in df.columns and min_abstract_len > 0:
#     df = df[
#         df["Abstract"].astype(str).str.len() >= min_abstract_len
#     ]

# if "Abstract" in df.columns and exclude_keywords.strip():
#     keywords = [
#         k.strip().lower()
#         for k in exclude_keywords.split(",")
#         if k.strip()
#     ]
#     mask = df["Abstract"].astype(str).str.lower().apply(
#         lambda txt: any(k in txt for k in keywords)
#     )
#     df = df[~mask]

# # Deduplicate
# if deduplicate and {"DOI", "Title"}.issubset(df.columns):
#     df["_doi_norm"] = normalize_text(df["DOI"])
#     df["_title_norm"] = normalize_text(df["Title"])
#     df = df.drop_duplicates(subset=["_doi_norm", "_title_norm"])
#     df = df.drop(columns=["_doi_norm", "_title_norm"])

# df = df.drop(columns=["Year_num"], errors="ignore")

# # =========================================================
# # METRICS
# # =========================================================

# st.divider()
# st.subheader("📊 Batch Summary")

# c1, c2, c3 = st.columns(3)
# c1.metric("Loaded Rows", len(raw_df))
# c2.metric("After Filtering", len(df))
# c3.metric("Unique DOIs", df["DOI"].nunique(dropna=True) if "DOI" in df.columns else 0)

# # =========================================================
# # PREVIEW
# # =========================================================

# st.divider()
# st.subheader("🔍 Preview")
# st.dataframe(df.head(300), use_container_width=True)

# # =========================================================
# # EXPORT
# # =========================================================

# st.divider()
# st.subheader("💾 Export")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("⬇️ Export CSV", type="primary"):
#         path = export_csv(df)

#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download CSV",
#                 f,
#                 file_name=path.name,
#                 mime="text/csv"
#             )

#         st.success(f"Saved to: {path}")

# with col2:
#     if st.button("📝 Export Markdown"):
#         path = export_markdown(df)

#         with open(path, "rb") as f:
#             st.download_button(
#                 "Download Markdown",
#                 f,
#                 file_name=path.name,
#                 mime="text/markdown"
#             )

#         st.success(f"Saved to: {path}")
