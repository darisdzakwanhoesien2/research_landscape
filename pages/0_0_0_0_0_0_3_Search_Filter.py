import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parents[1]
BIB_DIR = BASE_DIR / "data/bib_new"
CSV_DIR = BASE_DIR / "data/csv_new"

st.title("📂 File Browser")

bib_files = list(BIB_DIR.glob("*.bib"))
csv_files = list(CSV_DIR.glob("*.csv"))

c1, c2 = st.columns(2)

with c1:
    st.subheader("📘 Bib Files")
    for f in bib_files:
        st.write("•", f.name)

with c2:
    st.subheader("📗 CSV Files")
    for f in csv_files:
        st.write("•", f.name)

st.success(f"Found {len(bib_files)} bib files and {len(csv_files)} csv files.")


from pathlib import Path

from utils.bib_parser import parse_bib_file
from utils.csv_loader import load_csv_file
from utils.normalizer import normalize_dataframe, deduplicate

BASE_DIR = Path(__file__).parents[1]
BIB_DIR = BASE_DIR / "data/bib"
CSV_DIR = BASE_DIR / "data/csv"

st.title("🔄 Consolidate Data")

@st.cache_data
def load_all_data():
    frames = []

    for f in BIB_DIR.glob("*.bib"):
        df = parse_bib_file(f)
        frames.append(normalize_dataframe(df))

    for f in CSV_DIR.glob("*.csv"):
        df = load_csv_file(f)
        frames.append(normalize_dataframe(df))

    merged = pd.concat(frames, ignore_index=True)
    deduped = deduplicate(merged)
    return merged, deduped

if st.button("🚀 Load & Consolidate"):
    raw, clean = load_all_data()

    st.session_state["raw_df"] = raw
    st.session_state["clean_df"] = clean

    st.success(f"Loaded {len(raw)} rows → {len(clean)} after deduplication")

    st.subheader("Preview")
    st.dataframe(clean.head(50), use_container_width=True)


st.title("🔍 Search & Filter")

if "clean_df" not in st.session_state:
    st.warning("Please consolidate data first.")
    st.stop()

df = st.session_state["clean_df"]

query = st.text_input("Search title / abstract / authors")

if query:
    mask = (
        df["title"].str.contains(query, case=False, na=False) |
        df["abstract"].str.contains(query, case=False, na=False) |
        df["authors"].str.contains(query, case=False, na=False)
    )
    df = df[mask]

year_range = st.slider(
    "Year range",
    min_value=1900,
    max_value=2030,
    value=(2000, 2030)
)

df = df[
    (df["year"].astype(str).str.extract("(\d+)")[0].astype(float) >= year_range[0]) &
    (df["year"].astype(str).str.extract("(\d+)")[0].astype(float) <= year_range[1])
]

st.write(f"Results: {len(df)}")
st.dataframe(df, use_container_width=True)

import streamlit as st
from pathlib import Path
from utils.exporter import export_csv, export_markdown

BASE_DIR = Path(__file__).parents[1]
OUTPUT_DIR = BASE_DIR / "data/output"
OUTPUT_DIR.mkdir(exist_ok=True)

st.title("⬇️ Export")

if "clean_df" not in st.session_state:
    st.warning("Please consolidate data first.")
    st.stop()

df = st.session_state["clean_df"]

csv_path = OUTPUT_DIR / "consolidated.csv"
md_path = OUTPUT_DIR / "consolidated.md"

if st.button("💾 Export CSV"):
    export_csv(df, csv_path)
    st.success(f"Saved: {csv_path}")

if st.button("📝 Export Markdown"):
    export_markdown(df, md_path)
    st.success(f"Saved: {md_path}")
