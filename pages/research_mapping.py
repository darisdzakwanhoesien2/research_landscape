import streamlit as st
import pandas as pd
from io import StringIO
import bibtexparser

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="📚 CSV + BibTeX Concatenator",
    layout="wide"
)

st.title("📚 CSV + BibTeX Dataset Concatenator")
st.caption("Upload multiple CSV and BibTeX files and merge them into a unified dataset")

# =====================================================
# TARGET SCHEMA
# =====================================================

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

# =====================================================
# FILE UPLOAD
# =====================================================

uploaded_files = st.file_uploader(
    "Upload CSV and/or BibTeX files",
    type=["csv", "bib"],
    accept_multiple_files=True
)

# =====================================================
# UTILITIES
# =====================================================

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Force dataframe into target schema.
    Missing columns are created automatically.
    Extra columns are dropped.
    """
    df = df.copy()

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    for col in TARGET_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[TARGET_COLUMNS]


def parse_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    return normalize_dataframe(df)


def parse_bibtex(file) -> pd.DataFrame:
    """
    Convert BibTeX entries into dataframe rows.
    """
    text = file.read().decode("utf-8")
    bib_db = bibtexparser.loads(text)

    rows = []

    for entry in bib_db.entries:
        row = {
            "DOI": entry.get("doi"),
            "Title": entry.get("title"),
            "Authors": entry.get("author"),
            "Journal": entry.get("journal") or entry.get("booktitle"),
            "Year": entry.get("year"),
            "Abstract": entry.get("abstract"),
            "LitmapsId": None,
            "Cited By": None,
            "References": None,
            "PubMedId": entry.get("pmid"),
            "Tags": entry.get("keywords"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    return normalize_dataframe(df)


# =====================================================
# PROCESS FILES
# =====================================================

all_dfs = []

if uploaded_files:
    st.success(f"📂 {len(uploaded_files)} files uploaded")

    for file in uploaded_files:
        st.write(f"▶️ Processing `{file.name}`")

        try:
            if file.name.lower().endswith(".csv"):
                df = parse_csv(file)

            elif file.name.lower().endswith(".bib"):
                df = parse_bibtex(file)

            else:
                st.warning(f"Unsupported file type: {file.name}")
                continue

            st.write(f"✅ Loaded {len(df)} rows")
            all_dfs.append(df)

        except Exception as e:
            st.error(f"❌ Failed to parse {file.name}: {e}")

# =====================================================
# CONCATENATE + DISPLAY
# =====================================================

if all_dfs:
    combined_df = pd.concat(all_dfs, ignore_index=True)

    st.subheader("📊 Combined Dataset Preview")
    st.dataframe(combined_df, use_container_width=True)

    st.metric("Total Records", len(combined_df))

    # =====================================================
    # DOWNLOAD
    # =====================================================

    csv_data = combined_df.to_csv(index=False).encode("utf-8")
    json_data = combined_df.to_json(orient="records", indent=2).encode("utf-8")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "⬇️ Download CSV",
            csv_data,
            file_name="combined_dataset.csv",
            mime="text/csv"
        )

    with col2:
        st.download_button(
            "⬇️ Download JSON",
            json_data,
            file_name="combined_dataset.json",
            mime="application/json"
        )

else:
    st.info("📥 Upload CSV and/or BibTeX files to begin.")
