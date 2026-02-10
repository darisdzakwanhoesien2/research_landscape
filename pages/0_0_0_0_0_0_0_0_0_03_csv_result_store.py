import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# =========================================
# CONFIG
# =========================================

BASE_DIR = Path(__file__).resolve().parents[2]
STORE_DIR = BASE_DIR / "data" / "stored_csv_results"
STORE_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(layout="wide")
st.title("🗂️ CSV Result Storage Manager")

st.markdown("""
Upload scraped CSV results (e.g. Google Scholar extraction tables)  
Preview, clean, and permanently store them.
""")

# =========================================
# HELPERS
# =========================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("__+", "_", regex=True)
    )
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove fully empty columns and rows"""
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")
    return df


def list_saved_files():
    return sorted(STORE_DIR.glob("*.csv"))


# =========================================
# UPLOAD SECTION
# =========================================

st.subheader("📤 Upload CSV")

uploaded_file = st.file_uploader(
    "Upload your CSV file",
    type=["csv"]
)

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)

    st.success(f"Loaded {len(df_raw)} rows × {len(df_raw.columns)} columns")

    # Preview
    with st.expander("🔍 Raw Preview"):
        st.dataframe(df_raw, use_container_width=True)

    # Cleaning
    df_clean = clean_dataframe(df_raw)
    df_clean = normalize_columns(df_clean)

    st.info(f"After cleaning: {len(df_clean)} rows × {len(df_clean.columns)} columns")

    with st.expander("🧹 Cleaned Preview"):
        st.dataframe(df_clean, use_container_width=True)

    # =========================================
    # SAVE OPTIONS
    # =========================================

    st.subheader("💾 Save Options")

    default_name = uploaded_file.name.replace(".csv", "")
    dataset_name = st.text_input(
        "Dataset name",
        value=f"{default_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    )

    mode = st.radio(
        "Save mode",
        ["Create new dataset", "Append to existing dataset"]
    )

    existing_files = list_saved_files()
    target_file = None

    if mode == "Append to existing dataset":
        if not existing_files:
            st.warning("No existing datasets found.")
        else:
            target_file = st.selectbox(
                "Select existing dataset",
                existing_files,
                format_func=lambda p: p.name
            )

    if st.button("✅ Save Dataset"):
        if mode == "Create new dataset":
            save_path = STORE_DIR / f"{dataset_name}.csv"
            df_clean.to_csv(save_path, index=False)
            st.success(f"Saved new dataset → {save_path.name}")

        else:
            if target_file is None:
                st.error("Please select a target dataset.")
            else:
                df_existing = pd.read_csv(target_file)
                combined = pd.concat([df_existing, df_clean], ignore_index=True)
                combined.to_csv(target_file, index=False)
                st.success(f"Appended {len(df_clean)} rows → {target_file.name}")

# =========================================
# STORED DATASETS VIEWER
# =========================================

st.divider()
st.subheader("📚 Stored Datasets")

saved_files = list_saved_files()

if not saved_files:
    st.info("No stored datasets yet.")
else:
    selected_file = st.selectbox(
        "Select dataset",
        saved_files,
        format_func=lambda p: p.name
    )

    df_view = pd.read_csv(selected_file)

    st.write(f"Rows: {len(df_view)} | Columns: {len(df_view.columns)}")
    st.dataframe(df_view, use_container_width=True)

    # Download
    csv_bytes = df_view.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download CSV",
        data=csv_bytes,
        file_name=selected_file.name,
        mime="text/csv"
    )
