import streamlit as st
import pandas as pd
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Modular LaTeX Prompt Viewer",
    layout="wide"
)

st.title("🧩 Modular Thesis Prompt Viewer")
st.caption("Generate NotebookLM-ready modular LaTeX prompts from structured research plan CSV")

# ============================================================
# LOAD CSV
# ============================================================
CSV_PATH = Path("data/master_thesis_research_prompt.csv")

if not CSV_PATH.exists():
    st.error("❌ data/master_thesis_research_prompt.csv not found")
    st.stop()

df = pd.read_csv(CSV_PATH)

required_columns = {
    "section_name",
    "section_part",
    "part_title",
    "research_question",
    "batch_id",
    "notes"
}

missing = required_columns - set(df.columns)
if missing:
    st.error(f"❌ Missing required columns: {missing}")
    st.stop()

# Ensure ordering
df["section_part"] = df["section_part"].astype(int)
df = df.sort_values(by=["section_name", "section_part"])

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.header("🔎 Filters")

section = st.sidebar.selectbox(
    "Select Section",
    sorted(df["section_name"].unique())
)

batch = st.sidebar.selectbox(
    "Select Batch ID",
    ["All"] + sorted(df["batch_id"].unique())
)

filtered = df[df["section_name"] == section]

if batch != "All":
    filtered = filtered[filtered["batch_id"] == batch]

# ============================================================
# PROMPT BUILDER
# ============================================================
def build_prompt(section_name, rows):
    rq = rows["research_question"].iloc[0]

    parts = []
    for _, r in rows.iterrows():
        parts.append(f"- Part {r['section_part']}: {r['part_title']}")

    parts_text = "\n".join(parts)

    return f"""
ROLE:
You are an academic writing assistant for a modular LaTeX paper.

SECTION NAME:
{section_name}

RESEARCH QUESTION:
{rq}

REQUIRED OUTPUT MODULES:
{parts_text}

TASK:
For this section, generate EACH part as an independent LaTeX-ready subsection.
Each part must:
- Synthesize evidence from the provided papers
- Be coherent as a standalone module
- Use \\\\citep{{BibKey}} for all references

OUTPUT FORMAT:

SECTION: {section_name}

{section_name}.<PartNumber> — <Part Title>
[LaTeX-ready academic prose]

REFERENCES:
Provide BibTeX entries for all cited papers.
Key format: FirstAuthorYearKeyword

CONSTRAINTS:
- Use ONLY the provided papers
- Do NOT invent citations
- If metadata is missing, mark as "unknown"
""".strip()

# ============================================================
# DISPLAY PER-PART PROMPTS
# ============================================================
st.subheader(f"📘 Section: {section}")

st.markdown(f"**Research Question:** {filtered['research_question'].iloc[0]}")

all_part_prompts = []

for _, row in filtered.iterrows():

    part_prompt = f"""
SECTION: {row['section_name']}

PART:
{row['section_name']}.{row['section_part']} — {row['part_title']}

RESEARCH QUESTION:
{row['research_question']}

TASK:
Write this subsection as a standalone LaTeX-ready module.
- Use academic tone
- Cite using \\\\citep{{BibKey}}
- Do not invent studies

NOTES:
{row['notes']}
""".strip()

    all_part_prompts.append(part_prompt)

    with st.expander(
        f"{row['section_name']}.{row['section_part']} — {row['part_title']}",
        expanded=True
    ):
        st.text_area(
            "NotebookLM Subsection Prompt",
            value=part_prompt,
            height=260,
            key=f"part_{row['section_name']}_{row['section_part']}"
        )

# ============================================================
# SECTION-LEVEL COMBINED PROMPT
# ============================================================
st.subheader("🧠 Section-Level Combined Prompt (Recommended for NotebookLM)")

section_prompt = build_prompt(section, filtered)

st.text_area(
    "Copy this into NotebookLM (then paste the paper batch below it)",
    value=section_prompt,
    height=420
)

# ============================================================
# ALL SUB-PART PROMPTS COMBINED
# ============================================================
st.subheader("📋 All Subsection Prompts (Combined)")

st.text_area(
    "Copy all individual subsection prompts",
    value="\n\n" + ("\n\n" + "-" * 60 + "\n\n").join(all_part_prompts),
    height=400
)

# ============================================================
# TRACEABILITY TABLE
# ============================================================
with st.expander("📊 Prompt Planning Table"):
    st.dataframe(filtered.reset_index(drop=True))
