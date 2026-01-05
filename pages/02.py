import streamlit as st
import pandas as pd
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Research Prompt Generator",
    layout="wide"
)

st.title("🧩 Research Prompt Generator")
st.caption("Structured prompt generation from CSV metadata")

# ============================================================
# LOAD CSV
# ============================================================
CSV_PATH = Path("data/research_prompt.csv")

if not CSV_PATH.exists():
    st.error("❌ data/research_prompt.csv not found")
    st.stop()

df = pd.read_csv(CSV_PATH)

required_columns = {
    "Paper", "#", "TOPIC", "SECTION", "SECTION PART",
    "BATCH TYPE", "SCOPE", "TASK"
}

missing = required_columns - set(df.columns)
if missing:
    st.error(f"❌ Missing required columns: {missing}")
    st.stop()

# Clean HTML breaks
df["SCOPE"] = df["SCOPE"].astype(str).str.replace("<br>", "\n", regex=False)

# ============================================================
# SIDEBAR FILTERS (TABLE-DRIVEN)
# ============================================================
st.sidebar.header("🔎 Prompt Selection")

paper = st.sidebar.selectbox(
    "Paper",
    sorted(df["Paper"].unique())
)

topic = st.sidebar.selectbox(
    "Topic",
    sorted(df[df["Paper"] == paper]["TOPIC"].unique())
)

section = st.sidebar.selectbox(
    "Section",
    sorted(
        df[
            (df["Paper"] == paper) &
            (df["TOPIC"] == topic)
        ]["SECTION"].unique()
    )
)

section_part = st.sidebar.selectbox(
    "Section Part",
    sorted(
        df[
            (df["Paper"] == paper) &
            (df["TOPIC"] == topic) &
            (df["SECTION"] == section)
        ]["SECTION PART"].unique()
    )
)

batch_type = st.sidebar.selectbox(
    "Batch Type",
    sorted(
        df[
            (df["Paper"] == paper) &
            (df["TOPIC"] == topic) &
            (df["SECTION"] == section) &
            (df["SECTION PART"] == section_part)
        ]["BATCH TYPE"].unique()
    )
)

# ============================================================
# ROW SELECTION
# ============================================================
row = df[
    (df["Paper"] == paper) &
    (df["TOPIC"] == topic) &
    (df["SECTION"] == section) &
    (df["SECTION PART"] == section_part) &
    (df["BATCH TYPE"] == batch_type)
].iloc[0]

# ============================================================
# PROMPT TEMPLATE
# ============================================================
prompt = f"""
SECTION:
{row['SECTION']}

SECTION PART:
{row['SECTION PART']}

PART INDEX:
Single

SCOPE:
{row['SCOPE']}

BATCH TYPE:
{row['BATCH TYPE']}

TASK:
{row['TASK']}
""".strip()

# ============================================================
# OUTPUT
# ============================================================
st.subheader("🧠 Generated Prompt")

st.text_area(
    "Copy-ready prompt",
    value=prompt,
    height=320
)

# ============================================================
# DEBUG / TRANSPARENCY
# ============================================================
with st.expander("📊 Source Row Metadata"):
    st.dataframe(row.to_frame(name="Value"))
