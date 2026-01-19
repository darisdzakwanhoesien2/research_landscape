import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📚 Literature CSV Merger",
    layout="wide"
)

st.title("📚 Literature CSV Merger")
st.caption("Merge all CSV files under data/csv into a unified literature dataset")

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_DIR = BASE_DIR / "data" / "csv"
OUTPUT_DIR = BASE_DIR / "outputs"

CSV_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# TARGET SCHEMA
# =========================================================

TARGET_COLUMNS = [
    "DOI",
    "Title",
    "Authors",
    "Journal",
    "Year",
    "Abstract",
    "LitmapsId",
    "Cited By",
    "References",
    "PubMedId",
    "Tags",
]

# =========================================================
# UTILITIES
# =========================================================

@st.cache_data
def discover_csv_files():
    return sorted(CSV_DIR.glob("*.csv"))


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to match TARGET_COLUMNS as best as possible.
    """
    col_map = {}

    for col in df.columns:
        clean = col.strip().lower()

        mapping = {
            "doi": "DOI",
            "title": "Title",
            "authors": "Authors",
            "author": "Authors",
            "journal": "Journal",
            "year": "Year",
            "abstract": "Abstract",
            "litmapsid": "LitmapsId",
            "litmaps_id": "LitmapsId",
            "cited by": "Cited By",
            "cited_by": "Cited By",
            "references": "References",
            "pubmedid": "PubMedId",
            "pubmed_id": "PubMedId",
            "tags": "Tags",
        }

        if clean in mapping:
            col_map[col] = mapping[clean]

    df = df.rename(columns=col_map)

    # Ensure all target columns exist
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[TARGET_COLUMNS]


def load_and_merge(files):
    merged = []
    issues = []

    for file in files:
        try:
            df = pd.read_csv(file)
            raw_cols = list(df.columns)

            df = normalize_columns(df)
            df["__source_file"] = file.name

            merged.append(df)

            missing = set(TARGET_COLUMNS) - set(raw_cols)
            if missing:
                issues.append((file.name, list(missing)))

        except Exception as e:
            issues.append((file.name, str(e)))

    if merged:
        final_df = pd.concat(merged, ignore_index=True)
    else:
        final_df = pd.DataFrame(columns=TARGET_COLUMNS)

    return final_df, issues


def export_csv(df: pd.DataFrame) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"merged_literature_{ts}.csv"
    df.to_csv(path, index=False)
    return path


# =========================================================
# UI
# =========================================================

files = discover_csv_files()

st.sidebar.header("📂 Data Source")
st.sidebar.write(f"CSV Folder: `{CSV_DIR}`")
st.sidebar.write(f"Detected files: {len(files)}")

if not files:
    st.warning("No CSV files found in data/csv/")
    st.stop()

with st.expander("📄 Detected CSV Files", expanded=True):
    for f in files:
        st.write("•", f.name)

# =========================================================
# MERGE ACTION
# =========================================================

st.divider()

if st.button("🚀 Merge All CSV Files", type="primary"):
    with st.spinner("Merging CSV files..."):
        merged_df, issues = load_and_merge(files)

    st.success(f"✅ Merged {len(merged_df)} rows")

    # ----------------------------------
    # Preview
    # ----------------------------------
    st.subheader("🔍 Preview")
    st.dataframe(merged_df.head(200), use_container_width=True)

    # ----------------------------------
    # Statistics
    # ----------------------------------
    st.subheader("📊 Dataset Summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rows", len(merged_df))
    c2.metric("Unique DOIs", merged_df["DOI"].nunique(dropna=True))
    c3.metric("Unique Journals", merged_df["Journal"].nunique(dropna=True))
    c4.metric("Unique Years", merged_df["Year"].nunique(dropna=True))

    # ----------------------------------
    # Issues
    # ----------------------------------
    if issues:
        st.subheader("⚠️ Detected Issues")
        for item in issues:
            st.write(item)

    # ----------------------------------
    # Export
    # ----------------------------------
    export_path = export_csv(merged_df)

    with open(export_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Merged CSV",
            data=f,
            file_name=export_path.name,
            mime="text/csv"
        )

    st.info(f"Saved to: {export_path}")

# =========================================================
# OPTIONAL: RAW FILE INSPECTOR
# =========================================================

st.divider()
st.subheader("🧪 Inspect Individual File")

selected = st.selectbox("Select a CSV file", files)

if selected:
    try:
        df = pd.read_csv(selected)
        st.write(f"Rows: {len(df)}")
        st.write("Columns:", list(df.columns))
        st.dataframe(df.head(100), use_container_width=True)
    except Exception as e:
        st.error(str(e))
