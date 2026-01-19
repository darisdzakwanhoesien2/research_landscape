import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📝 Missing Abstract Editor",
    layout="wide"
)

st.title("📝 Missing Abstract Editor")
st.caption("Review, edit and audit papers with missing abstracts")

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_DIR = BASE_DIR / "data" / "csv"
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_FILE = LOG_DIR / "abstract_edit_log.csv"

CSV_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 CSV Folder: `{CSV_DIR}`")
st.sidebar.caption(f"🗂️ Log Folder: `{LOG_DIR}`")

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


def save_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False)


def append_log(entry: dict):
    log_df = pd.DataFrame([entry])

    if LOG_FILE.exists():
        old = pd.read_csv(LOG_FILE)
        log_df = pd.concat([old, log_df], ignore_index=True)

    log_df.to_csv(LOG_FILE, index=False)


def normalize_text(x):
    return str(x).strip().lower()


# =========================================================
# SIDEBAR – FILE SELECTION
# =========================================================

st.sidebar.header("📂 Dataset Selection")

files = discover_csv_files()

if not files:
    st.warning("No CSV files found in data/csv/")
    st.stop()

selected_file = st.sidebar.selectbox(
    "Select CSV file",
    files,
    format_func=lambda p: p.name
)

csv_path = selected_file
df_raw = load_csv(csv_path)

# =========================================================
# FIND MISSING ABSTRACTS
# =========================================================

if "Abstract" not in df_raw.columns:
    st.error("This CSV does not contain an 'Abstract' column.")
    st.stop()

missing_mask = (
    df_raw["Abstract"]
    .astype(str)
    .str.strip()
    .str.lower()
    == "(missing abstract)"
)

missing_df = df_raw[missing_mask].copy()

st.sidebar.metric("Missing abstracts", len(missing_df))

# =========================================================
# MAIN UI
# =========================================================

tab_edit, tab_log = st.tabs(["✍️ Edit Missing Abstracts", "📜 Edit History"])

# =========================================================
# ✍️ EDIT TAB
# =========================================================

with tab_edit:

    if missing_df.empty:
        st.success("🎉 No missing abstracts found!")
        st.stop()

    st.subheader("📄 Papers Missing Abstracts")

    display_cols = [
        c for c in ["DOI", "Title", "Journal", "Year"]
        if c in missing_df.columns
    ]

    st.dataframe(
        missing_df[display_cols].reset_index(),
        use_container_width=True,
        height=300
    )

    # ---------------------------------------------
    # Selection
    # ---------------------------------------------

    st.divider()
    st.subheader("✏️ Edit Selected Paper")

    selected_index = st.selectbox(
        "Select row index",
        missing_df.index.tolist()
    )

    row = df_raw.loc[selected_index]

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("DOI", row.get("DOI", ""), disabled=True)
        st.text_input("Title", row.get("Title", ""), disabled=True)
        st.text_input("Journal", row.get("Journal", ""), disabled=True)
        st.text_input("Year", row.get("Year", ""), disabled=True)

    with col2:
        new_abstract = st.text_area(
            "New Abstract",
            height=240,
            placeholder="Paste or write the abstract here..."
        )

        editor_note = st.text_input(
            "Optional note (source, confidence, etc.)"
        )

    # ---------------------------------------------
    # Save Action
    # ---------------------------------------------

    if st.button("💾 Save Abstract", type="primary"):
        if not new_abstract.strip():
            st.warning("Abstract cannot be empty.")
            st.stop()

        old_abstract = df_raw.loc[selected_index, "Abstract"]

        # Update dataframe
        df_raw.loc[selected_index, "Abstract"] = new_abstract.strip()
        save_csv(csv_path, df_raw)

        # Log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file": csv_path.name,
            "row_index": selected_index,
            "doi": row.get("DOI", ""),
            "title": row.get("Title", ""),
            "old_abstract": old_abstract,
            "new_abstract": new_abstract.strip(),
            "note": editor_note,
        }

        append_log(log_entry)

        st.success("✅ Abstract updated and logged successfully.")
        st.cache_data.clear()
        st.rerun()

# =========================================================
# 📜 LOG TAB
# =========================================================

with tab_log:

    st.subheader("📜 Abstract Edit History")

    if not LOG_FILE.exists():
        st.info("No edit history yet.")
        st.stop()

    log_df = pd.read_csv(LOG_FILE)

    # ---------------------------------------------
    # Filters
    # ---------------------------------------------

    with st.expander("🔎 Filters", expanded=True):
        f1, f2, f3 = st.columns(3)

        with f1:
            file_filter = st.multiselect(
                "Filter by file",
                sorted(log_df["file"].dropna().unique())
            )

        with f2:
            doi_filter = st.text_input("Filter by DOI contains")

        with f3:
            title_filter = st.text_input("Filter by Title contains")

    filtered_log = log_df.copy()

    if file_filter:
        filtered_log = filtered_log[
            filtered_log["file"].isin(file_filter)
        ]

    if doi_filter.strip():
        filtered_log = filtered_log[
            filtered_log["doi"]
            .astype(str)
            .str.lower()
            .str.contains(doi_filter.lower())
        ]

    if title_filter.strip():
        filtered_log = filtered_log[
            filtered_log["title"]
            .astype(str)
            .str.lower()
            .str.contains(title_filter.lower())
        ]

    # ---------------------------------------------
    # Display
    # ---------------------------------------------

    st.dataframe(
        filtered_log.sort_values("timestamp", ascending=False),
        use_container_width=True,
        height=500
    )

    # ---------------------------------------------
    # Export Log
    # ---------------------------------------------

    st.divider()

    csv_bytes = filtered_log.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Log CSV",
        data=csv_bytes,
        file_name="abstract_edit_log.csv",
        mime="text/csv"
    )
