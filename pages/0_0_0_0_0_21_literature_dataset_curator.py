import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="🧹 Literature Dataset Curator",
    layout="wide"
)

st.title("🧹 Literature Dataset Curator")
st.caption("Curate, filter and export CSV datasets from data/csv")

# =========================================================
# PATH CONFIG (FIXED)
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_DIR = BASE_DIR / "data" / "csv"
EXPORT_DIR = BASE_DIR / "outputs"

CSV_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")

# =========================================================
# UTILITIES
# =========================================================

@st.cache_data
def discover_csv_files():
    return sorted(CSV_DIR.glob("*.csv"))


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def export_csv(df: pd.DataFrame) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"curated_literature_{ts}.csv"
    df.to_csv(path, index=False)
    return path


def normalize_text(series):
    return series.astype(str).str.strip().str.lower()


# =========================================================
# DATA SOURCE SELECTION
# =========================================================

st.sidebar.header("📂 Dataset Source")

files = discover_csv_files()

if not files:
    st.warning("⚠️ No CSV files found in data/csv/")
    st.stop()

selected_file = st.sidebar.selectbox(
    "Select CSV file",
    files,
    format_func=lambda p: p.name
)

df_raw = load_csv(selected_file)
st.sidebar.metric("Rows loaded", len(df_raw))

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

# Year range
if "Year" in df_raw.columns:
    year_series = pd.to_numeric(df_raw["Year"], errors="coerce")
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

exclude_keywords = st.sidebar.text_input(
    "Exclude keywords in Abstract",
    placeholder="survey, review"
)

# =========================================================
# APPLY FILTERS
# =========================================================

df = df_raw.copy()

if "Abstract" in df.columns and remove_missing_abstract:
    df = df[
        normalize_text(df["Abstract"]) != "(missing abstract)"
    ]

if "DOI" in df.columns and remove_empty_doi:
    df = df[
        normalize_text(df["DOI"]) != ""
    ]

if "Title" in df.columns and remove_empty_title:
    df = df[
        normalize_text(df["Title"]) != ""
    ]

if year_range and "Year" in df.columns:
    df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df[
        (df["Year_num"] >= year_range[0]) &
        (df["Year_num"] <= year_range[1])
    ]

if "Abstract" in df.columns and min_abstract_len > 0:
    df = df[
        df["Abstract"].astype(str).str.len() >= min_abstract_len
    ]

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

# Deduplicate
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
st.subheader("📊 Dataset Health")

c1, c2, c3 = st.columns(3)
c1.metric("Remaining Rows", len(df))
c2.metric("Removed Rows", len(df_raw) - len(df))
c3.metric("Unique DOIs", df["DOI"].nunique(dropna=True) if "DOI" in df.columns else 0)

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

if st.button("💾 Export Curated Dataset", type="primary"):
    export_path = export_csv(df)

    with open(export_path, "rb") as f:
        st.download_button(
            "⬇️ Download CSV",
            f,
            file_name=export_path.name,
            mime="text/csv"
        )

    st.success(f"Saved to: {export_path}")


# import pandas as pd
# import streamlit as st
# from pathlib import Path
# from datetime import datetime

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="🧹 Literature Dataset Curator",
#     layout="wide"
# )

# st.title("🧹 Literature Dataset Curator")
# st.caption("Curate, clean, deduplicate and export merged literature datasets")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# OUTPUT_DIR = BASE_DIR / "outputs"
# OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# # =========================================================
# # UTILITIES
# # =========================================================

# @st.cache_data
# def discover_files():
#     return sorted(OUTPUT_DIR.glob("merged_literature_*.csv"))


# @st.cache_data
# def load_csv(path: Path) -> pd.DataFrame:
#     df = pd.read_csv(path)
#     df.columns = df.columns.str.strip()
#     return df


# def export_csv(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = OUTPUT_DIR / f"curated_literature_{ts}.csv"
#     df.to_csv(path, index=False)
#     return path


# def normalize_text(series):
#     return series.astype(str).str.strip().str.lower()


# # =========================================================
# # SESSION STATE INIT
# # =========================================================

# if "excluded_dois" not in st.session_state:
#     st.session_state.excluded_dois = set()

# if "excluded_titles" not in st.session_state:
#     st.session_state.excluded_titles = set()

# # =========================================================
# # SIDEBAR – DATA SOURCE
# # =========================================================

# st.sidebar.header("📂 Dataset")

# files = discover_files()
# if not files:
#     st.warning("No merged datasets found in outputs/")
#     st.stop()

# selected_file = st.sidebar.selectbox("Select merged dataset", files)

# raw_df = load_csv(selected_file)

# st.sidebar.metric("Total rows", len(raw_df))

# # =========================================================
# # SIDEBAR – FILTERS
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🧪 Filters")

# remove_missing_abstract = st.sidebar.checkbox("Remove '(missing abstract)'", True)
# remove_empty_doi = st.sidebar.checkbox("Remove empty DOI", True)
# remove_empty_title = st.sidebar.checkbox("Remove empty Title", True)
# deduplicate = st.sidebar.checkbox("Deduplicate (DOI + Title)", True)

# min_abstract_len = st.sidebar.slider("Minimum abstract length", 0, 500, 40)

# year_series = pd.to_numeric(raw_df.get("Year"), errors="coerce")
# year_min = int(year_series.min() or 1900)
# year_max = int(year_series.max() or datetime.now().year)

# year_range = st.sidebar.slider(
#     "Year range",
#     min_value=year_min,
#     max_value=year_max,
#     value=(year_min, year_max)
# )

# exclude_keywords = st.sidebar.text_input(
#     "Exclude keywords in Abstract",
#     placeholder="survey, review"
# )

# # =========================================================
# # APPLY FILTERS
# # =========================================================

# df = raw_df.copy()

# if remove_missing_abstract:
#     df = df[normalize_text(df["Abstract"]) != "(missing abstract)"]

# if remove_empty_doi:
#     df = df[normalize_text(df["DOI"]) != ""]

# if remove_empty_title:
#     df = df[normalize_text(df["Title"]) != ""]

# df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
# df = df[(df["Year_num"] >= year_range[0]) & (df["Year_num"] <= year_range[1])]

# if min_abstract_len > 0:
#     df = df[df["Abstract"].astype(str).str.len() >= min_abstract_len]

# if exclude_keywords.strip():
#     keywords = [k.strip().lower() for k in exclude_keywords.split(",") if k.strip()]
#     mask = df["Abstract"].astype(str).str.lower().apply(
#         lambda txt: any(k in txt for k in keywords)
#     )
#     df = df[~mask]

# # Deduplicate
# if deduplicate:
#     df["_doi_norm"] = normalize_text(df["DOI"])
#     df["_title_norm"] = normalize_text(df["Title"])
#     df = df.drop_duplicates(subset=["_doi_norm", "_title_norm"])
#     df = df.drop(columns=["_doi_norm", "_title_norm"])

# # Manual exclusions
# if st.session_state.excluded_dois:
#     df = df[~normalize_text(df["DOI"]).isin(st.session_state.excluded_dois)]

# if st.session_state.excluded_titles:
#     df = df[~normalize_text(df["Title"]).isin(st.session_state.excluded_titles)]

# df = df.drop(columns=["Year_num"], errors="ignore")

# # =========================================================
# # METRICS
# # =========================================================

# st.divider()
# st.subheader("📊 Dataset Health")

# c1, c2, c3, c4 = st.columns(4)
# c1.metric("Remaining", len(df))
# c2.metric("Removed", len(raw_df) - len(df))
# c3.metric("Unique DOI", df["DOI"].nunique(dropna=True))
# c4.metric("Avg Abstract Length", int(df["Abstract"].astype(str).str.len().mean() or 0))

# # =========================================================
# # MANUAL EXCLUSION PANEL
# # =========================================================

# st.divider()
# st.subheader("🚫 Manual Exclusion")

# col1, col2 = st.columns(2)

# with col1:
#     doi_input = st.text_area("Exclude DOI (one per line)", height=120)

#     if st.button("➕ Add DOI Exclusions"):
#         for x in doi_input.splitlines():
#             if x.strip():
#                 st.session_state.excluded_dois.add(x.strip().lower())
#         st.success("DOIs added")

# with col2:
#     title_input = st.text_area("Exclude Title (one per line)", height=120)

#     if st.button("➕ Add Title Exclusions"):
#         for x in title_input.splitlines():
#             if x.strip():
#                 st.session_state.excluded_titles.add(x.strip().lower())
#         st.success("Titles added")

# if st.session_state.excluded_dois or st.session_state.excluded_titles:
#     with st.expander("📄 Current Exclusions"):
#         st.write("DOI:", list(st.session_state.excluded_dois))
#         st.write("Title:", list(st.session_state.excluded_titles))

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
# if st.button("💾 Export Curated Dataset", type="primary"):
#     path = export_csv(df)
#     with open(path, "rb") as f:
#         st.download_button("⬇️ Download CSV", f, file_name=path.name)
#     st.success(f"Saved to: {path}")


# import pandas as pd
# import streamlit as st
# from pathlib import Path
# from datetime import datetime

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="🧹 Literature Dataset Curator",
#     layout="wide"
# )

# st.title("🧹 Literature Dataset Curator")
# st.caption("Filter, exclude, and curate merged literature datasets")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# OUTPUT_DIR = BASE_DIR / "outputs"

# OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# # =========================================================
# # UTILITIES
# # =========================================================

# @st.cache_data
# def discover_merged_files():
#     return sorted(OUTPUT_DIR.glob("merged_literature_*.csv"))


# @st.cache_data
# def load_csv(path: Path) -> pd.DataFrame:
#     return pd.read_csv(path)


# def export_csv(df: pd.DataFrame) -> Path:
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = OUTPUT_DIR / f"curated_literature_{ts}.csv"
#     df.to_csv(path, index=False)
#     return path


# # =========================================================
# # SIDEBAR – DATA SOURCE
# # =========================================================

# st.sidebar.header("📂 Dataset")

# files = discover_merged_files()

# if not files:
#     st.warning("No merged dataset found in outputs/. Please run the merger first.")
#     st.stop()

# selected_file = st.sidebar.selectbox("Select merged dataset", files)

# raw_df = load_csv(selected_file)

# st.sidebar.metric("Total rows", len(raw_df))

# # =========================================================
# # FILTER CONTROLS
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🧪 Dataset Filters")

# remove_missing_abstract = st.sidebar.checkbox(
#     "Remove '(missing abstract)'",
#     value=True
# )

# remove_empty_doi = st.sidebar.checkbox(
#     "Remove empty DOI",
#     value=True
# )

# remove_empty_title = st.sidebar.checkbox(
#     "Remove empty Title",
#     value=True
# )

# # Year filter
# year_min = int(pd.to_numeric(raw_df["Year"], errors="coerce").min() or 1900)
# year_max = int(pd.to_numeric(raw_df["Year"], errors="coerce").max() or 2100)

# year_range = st.sidebar.slider(
#     "Year range",
#     min_value=year_min,
#     max_value=year_max,
#     value=(year_min, year_max)
# )

# # Keyword exclusion
# exclude_keywords = st.sidebar.text_area(
#     "Exclude if Abstract contains keywords (comma separated)",
#     placeholder="survey, review, protocol"
# )

# # =========================================================
# # APPLY FILTERS
# # =========================================================

# df = raw_df.copy()

# # --- Missing abstract
# if remove_missing_abstract:
#     df = df[
#         df["Abstract"].astype(str).str.lower().str.strip()
#         != "(missing abstract)"
#     ]

# # --- Empty DOI
# if remove_empty_doi:
#     df = df[df["DOI"].notna() & (df["DOI"].astype(str).str.strip() != "")]

# # --- Empty Title
# if remove_empty_title:
#     df = df[df["Title"].notna() & (df["Title"].astype(str).str.strip() != "")]

# # --- Year range
# df["Year_num"] = pd.to_numeric(df["Year"], errors="coerce")
# df = df[
#     (df["Year_num"] >= year_range[0]) &
#     (df["Year_num"] <= year_range[1])
# ]

# # --- Keyword exclusion
# if exclude_keywords.strip():
#     keywords = [k.strip().lower() for k in exclude_keywords.split(",") if k.strip()]

#     mask = df["Abstract"].astype(str).str.lower().apply(
#         lambda txt: any(k in txt for k in keywords)
#     )

#     df = df[~mask]

# df = df.drop(columns=["Year_num"], errors="ignore")

# # =========================================================
# # MANUAL EXCLUSION
# # =========================================================

# st.divider()
# st.subheader("🚫 Manual Paper Exclusion")

# col1, col2 = st.columns(2)

# with col1:
#     excluded_dois = st.text_area(
#         "Exclude DOIs (one per line)",
#         height=150
#     )

# with col2:
#     excluded_titles = st.text_area(
#         "Exclude Titles (one per line)",
#         height=150
#     )

# # Apply manual exclusions
# if excluded_dois.strip():
#     doi_list = [x.strip().lower() for x in excluded_dois.splitlines() if x.strip()]
#     df = df[~df["DOI"].astype(str).str.lower().isin(doi_list)]

# if excluded_titles.strip():
#     title_list = [x.strip().lower() for x in excluded_titles.splitlines() if x.strip()]
#     df = df[~df["Title"].astype(str).str.lower().isin(title_list)]

# # =========================================================
# # INTERACTIVE TABLE FILTER
# # =========================================================

# st.divider()
# st.subheader("🖱️ Interactive Selection (Optional)")

# st.caption("Select rows to exclude manually from the preview table.")

# preview_df = df[["DOI", "Title", "Year", "Journal"]].copy()
# preview_df.insert(0, "Exclude", False)

# edited_df = st.data_editor(
#     preview_df,
#     use_container_width=True,
#     num_rows="dynamic"
# )

# excluded_rows = edited_df[edited_df["Exclude"] == True]

# if not excluded_rows.empty:
#     excluded_doi_set = set(excluded_rows["DOI"].astype(str))
#     df = df[~df["DOI"].astype(str).isin(excluded_doi_set)]

# # =========================================================
# # RESULTS
# # =========================================================

# st.divider()
# st.subheader("✅ Curated Dataset")

# c1, c2, c3 = st.columns(3)
# c1.metric("Remaining Papers", len(df))
# c2.metric("Removed Papers", len(raw_df) - len(df))
# c3.metric("Removal %", round(100 * (1 - len(df) / max(len(raw_df),1)), 2))

# st.dataframe(df.head(300), use_container_width=True)

# # =========================================================
# # EXPORT
# # =========================================================

# st.divider()

# if st.button("💾 Export Curated Dataset", type="primary"):
#     export_path = export_csv(df)

#     with open(export_path, "rb") as f:
#         st.download_button(
#             "⬇️ Download Curated CSV",
#             data=f,
#             file_name=export_path.name,
#             mime="text/csv"
#         )

#     st.success(f"Saved to: {export_path}")
