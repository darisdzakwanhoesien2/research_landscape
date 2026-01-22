import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📄 Literature Markdown Exporter",
    layout="wide"
)

st.title("📄 Literature Markdown Exporter")
st.caption("Filter by predicted category → concatenate title + abstract → export Markdown")

# =========================================================
# PATH CONFIG  ✅ CORRECT FOR pages/29.py
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]   # project_root
CSV_DIR = BASE_DIR / "data" / "csv_data"
EXPORT_DIR = BASE_DIR / "outputs"

CSV_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
st.sidebar.caption(f"📦 Export Folder: `{EXPORT_DIR}`")

# =========================================================
# UTILITIES
# =========================================================

@st.cache_data
def discover_csv_files():
    return sorted(CSV_DIR.glob("*.csv"))


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    """
    Load CSV safely and normalize types for Arrow compatibility.
    """
    df = pd.read_csv(path)

    # --- Fix Arrow serialization warning ---
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # Ensure expected columns exist
    expected_cols = [
        "record_id",
        "Title",
        "Abstract",
        "predicted_category",
        "matched_keywords"
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    return df


def build_markdown(df: pd.DataFrame) -> str:
    """
    Convert dataframe rows into Markdown sections.
    """
    blocks = []
    df = df.copy()   # ✅ avoid SettingWithCopyWarning

    for _, row in df.iterrows():
        title = str(row["Title"]).strip()
        abstract = str(row["Abstract"]).strip()

        if not title and not abstract:
            continue

        block = f"""## {title}

### Abstract
{abstract}
"""
        blocks.append(block)

    header = f"# 📚 Literature Export\n\nGenerated at: {datetime.now().isoformat()}\n\n"
    return header + "\n\n---\n\n".join(blocks)

# **Record ID:** {row['record_id']}  
# **Predicted Category:** {row['predicted_category']}  
# **Matched Keywords:** {row['matched_keywords']}

# =========================================================
# ACTION BAR
# =========================================================

col_refresh, _ = st.columns([1, 8])

with col_refresh:
    if st.button("🔄 Refresh CSV Folder"):
        st.cache_data.clear()
        st.rerun()

# =========================================================
# SIDEBAR — CSV SELECTION
# =========================================================

csv_files = discover_csv_files()

if not csv_files:
    st.warning(f"⚠️ No CSV files found in {CSV_DIR}")
    st.stop()

selected_csv = st.sidebar.selectbox(
    "📂 Select CSV File",
    csv_files,
    format_func=lambda p: p.name
)

df = load_csv(selected_csv)

# =========================================================
# FILTER UI
# =========================================================

st.subheader("🎯 Filter")

all_categories = sorted(
    df["predicted_category"]
    .dropna()
    .astype(str)
    .unique()
)

selected_categories = st.multiselect(
    "Select predicted categories",
    options=all_categories,
    default=all_categories
)

filtered_df = df[
    df["predicted_category"].astype(str).isin(selected_categories)
].copy()

st.caption(f"Showing **{len(filtered_df)} / {len(df)}** records")

# =========================================================
# PREVIEW TABLE
# =========================================================

st.subheader("👀 Preview")

preview_cols = [
    "record_id",
    "Title",
    "predicted_category",
    "matched_keywords"
]

st.dataframe(
    filtered_df[preview_cols],
    use_container_width=True,
    height=360
)

# =========================================================
# MARKDOWN GENERATION
# =========================================================

st.subheader("📝 Markdown Preview")

markdown_text = build_markdown(filtered_df)

with st.expander("🔍 View Markdown"):
    st.markdown(markdown_text)

# =========================================================
# EXPORT
# =========================================================

st.subheader("⬇️ Export")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
export_name = f"literature_export_{timestamp}.md"
export_path = EXPORT_DIR / export_name

col_export, col_download = st.columns([1, 3])

with col_export:
    if st.button("💾 Export Markdown"):
        export_path.write_text(markdown_text, encoding="utf-8")
        st.success(f"✅ Exported: {export_path.name}")

with col_download:
    st.download_button(
        label="📥 Download Markdown",
        data=markdown_text,
        file_name=export_name,
        mime="text/markdown"
    )
