import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="🔗 Merge Final RQ CSVs", layout="wide")
st.title("🔗 Merge Final RQ CSV Files")

# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
LOG_DIR = BASE_DIR / "data" / "registry"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

MERGED_PATH = OUTPUT_DIR / "merged_all.csv"
LOG_PATH = LOG_DIR / "merge_log.json"

# =====================================================
# UTILITIES
# =====================================================

def load_logs():
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text())
    return []


def save_log(entry):
    logs = load_logs()
    logs.append(entry)
    LOG_PATH.write_text(json.dumps(logs, indent=2))


def clean_abstract(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
    )


def filter_missing_abstracts(df: pd.DataFrame):
    if "Abstract" not in df.columns:
        return df, 0

    before = len(df)

    abstract = clean_abstract(df["Abstract"])

    INVALID = {
        "",
        "nan",
        "none",
        "(missing abstract)",
        "missing abstract"
    }

    mask = ~abstract.isin(INVALID)
    df = df[mask].copy()

    return df, before - len(df)


def smart_deduplicate(df: pd.DataFrame):
    if "DOI" not in df.columns or "Title" not in df.columns:
        return df, 0

    before = len(df)

    has_doi = df["DOI"].notna() & (df["DOI"].astype(str).str.strip() != "")
    with_doi = df[has_doi].drop_duplicates(subset=["DOI"])
    without_doi = df[~has_doi].drop_duplicates(subset=["Title"])

    df = pd.concat([with_doi, without_doi], ignore_index=True)

    return df, before - len(df)

# =====================================================
# DISCOVERY
# =====================================================

csv_files = sorted(RAW_DIR.glob("rq*/**/*_final.csv"))

if not csv_files:
    st.warning("No *_final.csv files found under data/raw/")
    st.stop()

with st.expander("📂 Discovered Files", expanded=False):
    for f in csv_files:
        st.code(str(f))

# =====================================================
# LOAD + MERGE
# =====================================================

dfs = []

for path in csv_files:
    rq = path.parent.name
    df = pd.read_csv(path)
    df["RQ"] = rq
    df["SourceFile"] = path.name
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

st.metric("📊 Total Raw Records", len(combined_df))

# =====================================================
# FILTER CONTROLS
# =====================================================

st.subheader("🧹 Cleaning Controls")

col1, col2 = st.columns(2)

with col1:
    enable_filter = st.checkbox(
        "Remove missing / placeholder abstracts",
        value=True
    )

with col2:
    min_length = st.number_input(
        "Minimum abstract length (characters)",
        min_value=0,
        value=50,
        step=10
    )

working_df = combined_df.copy()

removed_abstracts = 0
removed_length = 0

if enable_filter:
    working_df, removed_abstracts = filter_missing_abstracts(working_df)

if min_length > 0 and "Abstract" in working_df.columns:
    before = len(working_df)
    working_df = working_df[
        working_df["Abstract"].astype(str).str.len() >= min_length
    ]
    removed_length = before - len(working_df)

# =====================================================
# DEDUP CONTROLS
# =====================================================

st.subheader("🧬 Deduplication")

dedup_mode = st.selectbox(
    "Deduplication Strategy",
    [
        "None",
        "Smart (DOI → Title fallback)",
        "Manual column selection"
    ]
)

removed_duplicates = 0

if dedup_mode == "Smart (DOI → Title fallback)":
    working_df, removed_duplicates = smart_deduplicate(working_df)

elif dedup_mode == "Manual column selection":
    dedup_col = st.selectbox(
        "Select column",
        list(working_df.columns)
    )
    before = len(working_df)
    working_df = working_df.drop_duplicates(subset=[dedup_col])
    removed_duplicates = before - len(working_df)

# =====================================================
# METRICS
# =====================================================

st.subheader("📈 Processing Metrics")

m1, m2, m3, m4 = st.columns(4)

m1.metric("Raw Records", len(combined_df))
m2.metric("Removed (Missing Abstracts)", removed_abstracts)
m3.metric("Removed (Min Length)", removed_length)
m4.metric("Removed (Duplicates)", removed_duplicates)

st.metric("✅ Final Records", len(working_df))

# =====================================================
# PREVIEW
# =====================================================

st.subheader("📊 Preview (Top 500 Rows)")
st.dataframe(working_df.head(500), use_container_width=True)

# =====================================================
# EXPORT
# =====================================================

st.subheader("⬇️ Export")

if st.button("💾 Save merged CSV"):
    working_df.to_csv(MERGED_PATH, index=False)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "inputs": [str(p) for p in csv_files],
        "raw_records": len(combined_df),
        "final_records": len(working_df),
        "removed_missing_abstracts": removed_abstracts,
        "removed_min_length": removed_length,
        "removed_duplicates": removed_duplicates,
        "output": str(MERGED_PATH)
    }

    save_log(log_entry)

    st.success(f"✅ Saved to {MERGED_PATH}")

# =====================================================
# LOG VIEWER
# =====================================================

st.subheader("🧾 Merge Logs")

if st.button("📜 Show Logs"):
    logs = load_logs()

    if not logs:
        st.info("No logs available yet.")
    else:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)


# import streamlit as st
# import pandas as pd
# from pathlib import Path

# # =====================================================
# # PATHS
# # =====================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# RAW_DIR = BASE_DIR / "data" / "raw"
# OUTPUT_DIR = BASE_DIR / "data" / "processed"
# OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# st.title("🔗 Merge Final RQ CSV Files")

# # =====================================================
# # DISCOVERY
# # =====================================================

# csv_files = sorted(RAW_DIR.glob("rq*/**/*_final.csv"))

# if not csv_files:
#     st.warning("No *_final.csv files found under data/raw/")
#     st.stop()

# st.write("📂 Discovered files:")
# for f in csv_files:
#     st.code(str(f))

# # =====================================================
# # LOAD + MERGE
# # =====================================================

# dfs = []

# for path in csv_files:
#     rq = path.parent.name
#     df = pd.read_csv(path)
#     df["RQ"] = rq
#     df["SourceFile"] = path.name
#     dfs.append(df)

# combined_df = pd.concat(dfs, ignore_index=True)

# st.metric("Total Raw Records", len(combined_df))

# # =====================================================
# # OPTIONAL DEDUP
# # =====================================================

# dedup_col = st.selectbox(
#     "Deduplicate by column (optional)",
#     ["None"] + list(combined_df.columns)
# )

# if dedup_col != "None":
#     before = len(combined_df)
#     combined_df = combined_df.drop_duplicates(subset=[dedup_col])
#     after = len(combined_df)
#     st.success(f"Deduplicated: {before} → {after}")

# # =====================================================
# # PREVIEW
# # =====================================================

# st.subheader("📊 Preview")
# st.dataframe(combined_df.head(500), use_container_width=True)

# # =====================================================
# # SAVE
# # =====================================================

# if st.button("💾 Save merged CSV"):
#     output_path = OUTPUT_DIR / "merged_all.csv"
#     combined_df.to_csv(output_path, index=False)
#     st.success(f"Saved to {output_path}")
