import streamlit as st
import pandas as pd
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Multi-Prompt Viewer by Paper",
    layout="wide"
)

st.title("📄 Research Prompt Viewer")
st.caption("Visualize all structured prompts grouped by paper https://notebooklm.google.com/notebook/c4b7439e-9dcf-483a-ac57-9a213b52c92f")

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

# Ensure stable ordering
df = df.sort_values(by=["Paper", "#"])

# ============================================================
# SIDEBAR: PAPER SELECTION
# ============================================================
st.sidebar.header("📑 Paper Selection")

paper = st.sidebar.selectbox(
    "Select Paper",
    sorted(df["Paper"].unique())
)

paper_df = df[df["Paper"] == paper]

# ============================================================
# PROMPT GENERATION FUNCTION
# ============================================================
def build_prompt(row):
    return f"""
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
# DISPLAY PROMPTS
# ============================================================
st.subheader(f"🧠 Prompts for Paper {paper}")

all_prompts = []

for _, row in paper_df.iterrows():
    prompt = build_prompt(row)
    all_prompts.append(prompt)

    with st.expander(
        f"#{row['#']} — {row['SECTION']} | {row['SECTION PART']}",
        expanded=True
    ):
        st.text_area(
            label="Prompt",
            value=prompt,
            height=260,
            key=f"prompt_{paper}_{row['#']}"
        )

# ============================================================
# COMBINED COPY VIEW
# ============================================================
st.subheader("📋 All Prompts (Combined)")

st.text_area(
    "Copy all prompts below",
    value="\n\n" + ("\n\n" + "-" * 60 + "\n\n").join(all_prompts),
    height=400
)

# ============================================================
# DEBUG / TRACEABILITY
# ============================================================
with st.expander("📊 Paper Metadata Table"):
    st.dataframe(paper_df.reset_index(drop=True))
