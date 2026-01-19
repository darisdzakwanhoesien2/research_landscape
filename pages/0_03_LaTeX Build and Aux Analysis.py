import streamlit as st
from pathlib import Path
import re
import pandas as pd

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(page_title="LaTeX ↔ Literature DB Matcher", layout="wide")

st.title("📚 LaTeX Citation ↔ Literature Database Matcher")
st.caption("Match AUX citations against TXT abstract database")

DATA_LATEX = Path("data/latex")
DATA_DB = Path("data/database")

# =====================================
# SIDEBAR — INPUT
# =====================================
st.sidebar.header("📥 Input Source")

mode = st.sidebar.radio("Input method", ["Load from folders", "Upload files"])

aux_text = None
db_text = None

if mode == "Upload files":
    aux_file = st.sidebar.file_uploader("Upload .aux file", type=["aux", "txt"])
    db_file = st.sidebar.file_uploader("Upload database TXT", type=["txt"])

    if aux_file:
        aux_text = aux_file.read().decode("utf-8", errors="ignore")

    if db_file:
        db_text = db_file.read().decode("utf-8", errors="ignore")

else:
    aux_files = list(DATA_LATEX.glob("*.aux")) if DATA_LATEX.exists() else []
    db_files = list(DATA_DB.glob("*.txt")) if DATA_DB.exists() else []

    aux_path = st.sidebar.selectbox("Select AUX file", aux_files, format_func=lambda p: p.name if p else "")
    db_path = st.sidebar.selectbox("Select DB file", db_files, format_func=lambda p: p.name if p else "")

    if aux_path:
        aux_text = aux_path.read_text(errors="ignore")
    if db_path:
        db_text = db_path.read_text(errors="ignore")

# =====================================
# PARSING FUNCTIONS
# =====================================
def extract_dois_from_aux(aux_text):
    citations = re.findall(r"\\citation\{([^}]*)\}", aux_text)
    dois = set()

    for block in citations:
        parts = [p.strip() for p in block.split(",")]
        for p in parts:
            if p.startswith("10."):
                dois.add(p)

    return sorted(dois)


def parse_txt_database(text):
    records = []
    blocks = text.split("\n---")

    for b in blocks:
        lines = [l.strip() for l in b.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue

        title = lines[0]
        doi = lines[1] if lines[1].startswith("10.") else None
        abstract = " ".join(lines[2:])

        records.append({
            "title": title,
            "doi": doi,
            "abstract": abstract
        })

    return pd.DataFrame(records)

# =====================================
# MAIN LOGIC
# =====================================
if aux_text and db_text:

    aux_dois = extract_dois_from_aux(aux_text)
    db_df = parse_txt_database(db_text)

    db_doi_set = set(db_df["doi"].dropna().tolist())

    matched = [d for d in aux_dois if d in db_doi_set]
    missing = [d for d in aux_dois if d not in db_doi_set]
    extra = [d for d in db_doi_set if d not in aux_dois]

    # =====================================
    # METRICS
    # =====================================
    c1, c2, c3 = st.columns(3)
    c1.metric("Citations in AUX", len(aux_dois))
    c2.metric("Matched in DB", len(matched))
    c3.metric("Missing from DB", len(missing))

    # =====================================
    # TABS
    # =====================================
    tabs = st.tabs(["✅ Matched", "❌ Missing", "📚 Extra in DB", "🗃 Full Database"])

    with tabs[0]:
        st.subheader("Matched Citations")
        df = db_df[db_df["doi"].isin(matched)]
        st.dataframe(df, use_container_width=True)

        # ============================
        # DOI COPY BLOCK
        # ============================
        st.markdown("### 📋 Comma-separated DOI list")

        doi_list = df["doi"].dropna().tolist()
        doi_csv = ", ".join(doi_list)

        st.text_area(
            "Copy all matched DOIs:",
            value=doi_csv,
            height=120
        )



    with tabs[1]:
        st.subheader("Missing Citations (not in database)")
        if missing:
            st.code("\n".join(missing))
        else:
            st.success("All citations found in database.")

    with tabs[2]:
        st.subheader("Database Entries Not Cited in LaTeX")
        df = db_df[db_df["doi"].isin(extra)]
        st.dataframe(df[["title", "doi"]], use_container_width=True)

    with tabs[3]:
        st.subheader("Full Database")
        st.dataframe(db_df, use_container_width=True)

else:
    st.info("Please load both AUX file and TXT database.")

# =====================================
# FOOTER
# =====================================
st.caption("Designed for LaTeX literature tracking & thesis workflows.")
