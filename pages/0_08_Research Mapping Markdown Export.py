# --------------------------------------------------
# ESG Literature Mapping + CSV Enrichment
# + Paper-Centric & RQ-Centric Markdown Export
# --------------------------------------------------

import json
from pathlib import Path
import pandas as pd
import streamlit as st
import re
from difflib import SequenceMatcher

# ================================
# CONFIG
# ================================

BASE_DIR = Path(__file__).parents[1]
REGISTRY_PATH = BASE_DIR / "data" / "registry.json"

st.set_page_config(page_title="ESG Literature Markdown Exports", layout="wide")
st.title("📚 ESG Literature Mapping — Markdown Exports")

# ================================
# HELPERS
# ================================

def norm(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def fuzzy_best_row(query_norm, df_norm_col, df):
    best_score = 0
    best_row = None
    for _, r in df.iterrows():
        score = SequenceMatcher(None, query_norm, r[df_norm_col]).ratio()
        if score > best_score:
            best_score = score
            best_row = r
    return best_row, best_score


# ================================
# LOAD REGISTRY
# ================================

if not REGISTRY_PATH.exists():
    st.error(f"registry.json not found at: {REGISTRY_PATH}")
    st.stop()

with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    registry = json.load(f)

tracks = registry.get("research_tracks", [])

if not tracks:
    st.error("No research_tracks found in registry.json")
    st.stop()

# ================================
# BUILD GLOBAL MAPPING
# ================================

rows = []
paper_lookup = {}

for ti, t in enumerate(tracks):
    rq = t["meta"].get("research_question", f"RQ_{ti}")

    for p in t.get("papers", []):
        pid = p.get("id")
        title = p.get("input", {}).get("title")

        rows.append({
            "rq": rq,
            "paper_id": pid,
            "title": title,
            "title_norm": norm(title),
            "method": p.get("method_category"),
            "trace": p.get("decision_trace_support"),
            "relevance": p.get("relevance_score", 0.0),
            "regulatory": ", ".join(p.get("regulatory_relevance", [])),
        })

        paper_lookup[pid] = p

df = pd.DataFrame(rows)

# ================================
# UNIQUE PAPERS (DEDUP)
# ================================

unique_df = (
    df.groupby("title_norm")
    .agg({
        "title": "first",
        "method": lambda x: ", ".join(sorted(set(x.dropna()))),
        "trace": lambda x: ", ".join(sorted(set(x.dropna()))),
        "relevance": "max",
        "regulatory": lambda x: ", ".join(sorted(set(", ".join(x).split(", ")))),
        "rq": lambda x: list(sorted(set(x))),
        "paper_id": "first",
    })
    .reset_index(drop=True)
)

unique_df["rq_count"] = unique_df["rq"].apply(len)

# ================================
# CSV UPLOAD
# ================================

st.sidebar.header("📥 External Paper Database (CSV)")

csv_file = st.sidebar.file_uploader(
    "Upload CSV with columns: title, doi, abstract",
    type=["csv"]
)

db_df = None

if csv_file:
    try:
        db_df = pd.read_csv(csv_file)

        required = {"title", "doi", "abstract"}
        if not required.issubset(set(db_df.columns)):
            st.sidebar.error("CSV must contain: title, doi, abstract")
            db_df = None
        else:
            db_df["title_norm"] = db_df["title"].apply(norm)
            st.sidebar.success(f"Loaded {len(db_df)} database records")

    except Exception as e:
        st.sidebar.error(f"CSV error: {e}")

# ================================
# FILTERS
# ================================

st.sidebar.header("🔍 Filters")

rq_filter = st.sidebar.multiselect(
    "Research Questions",
    sorted(df["rq"].unique().tolist()),
    default=sorted(df["rq"].unique().tolist()),
)

method_filter = st.sidebar.multiselect(
    "Method Category",
    sorted(df["method"].dropna().unique().tolist()),
    default=sorted(df["method"].dropna().unique().tolist()),
)

trace_filter = st.sidebar.multiselect(
    "Decision Trace Support",
    sorted(df["trace"].dropna().unique().tolist()),
    default=sorted(df["trace"].dropna().unique().tolist()),
)

min_relevance = st.sidebar.slider("Minimum relevance", 0.0, 1.0, 0.7, 0.01)
search = st.sidebar.text_input("Search title")

# ================================
# APPLY FILTERS
# ================================

unique_filt = unique_df[
    (unique_df["method"].str.contains("|".join(method_filter), na=False))
    & (unique_df["trace"].str.contains("|".join(trace_filter), na=False))
    & (unique_df["relevance"] >= min_relevance)
]

if search:
    unique_filt = unique_filt[
        unique_filt["title"].str.contains(search, case=False, na=False)
    ]

# ================================
# TABLE
# ================================

st.subheader("📄 Unique Papers (Deduplicated)")

st.dataframe(
    unique_filt[["title", "rq_count", "method", "trace", "relevance", "regulatory"]]
    .sort_values(["rq_count", "relevance"], ascending=[False, False]),
    use_container_width=True,
)

# ================================
# MARKDOWN BUILDERS
# ================================

def build_paper_centric_md(unique_df, paper_lookup, db_df=None):
    md = ["# ESG Literature — Paper-Centric View\n"]

    for _, row in unique_df.iterrows():
        paper = paper_lookup[row["paper_id"]]

        md.append(f"## {row['title']}\n")

        md.append("### 🧠 Addressed Research Questions")
        for rq in row["rq"]:
            md.append(f"- {rq}")
        md.append("")

        md.append("### Method Category(s)")
        md.append(str(row["method"]) + "\n")

        md.append("### Decision Trace Support")
        md.append(str(row["trace"]) + "\n")

        md.append("### Max Relevance Score")
        md.append(str(row["relevance"]) + "\n")

        md.append("### Regulatory Relevance")
        md.append(str(row["regulatory"]) + "\n")

        md.append("### 📄 Abstract (Registry)")
        md.append(paper.get("input", {}).get("abstract", "") or "N/A")
        md.append("")

        if db_df is not None:
            query = norm(row["title"])
            best_row, best_score = fuzzy_best_row(query, "title_norm", db_df)

            if best_score >= 0.82 and best_row is not None:
                md.append("### 🗄 Abstract (Database CSV)")
                md.append(str(best_row.get("abstract", "")))
                md.append("")

                md.append("### DOI")
                md.append(str(best_row.get("doi", "")))
                md.append("")
            else:
                md.append("### 🗄 Abstract (Database CSV)")
                md.append("_No reliable match found in uploaded database._\n")

        md.append("### 🔗 External Links (Registry)")
        links = paper.get("external_links", [])
        if links:
            for l in links:
                md.append(f"- {l.get('type')}: {l.get('url')}")
        else:
            md.append("N/A")

        md.append("\n---\n")

    return "\n".join(md)


def build_rq_centric_md(unique_df):
    md = ["# ESG Literature — Research-Question-Centric View\n"]

    rq_map = {}

    for _, row in unique_df.iterrows():
        for rq in row["rq"]:
            rq_map.setdefault(rq, []).append(row)

    for rq, papers in rq_map.items():
        md.append(f"## {rq}\n")

        for row in papers:
            md.append(f"### {row['title']}")
            md.append(f"- Method: {row['method']}")
            md.append(f"- Decision Trace: {row['trace']}")
            md.append(f"- Relevance: {row['relevance']}")
            md.append(f"- Regulatory: {row['regulatory']}")
            md.append("")

        md.append("\n---\n")

    return "\n".join(md)

# ================================
# EXPORTS
# ================================

st.subheader("📤 Markdown Exports")

paper_md = build_paper_centric_md(unique_filt, paper_lookup, db_df)
rq_md = build_rq_centric_md(unique_filt)

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        "⬇️ Download Paper-Centric Markdown",
        data=paper_md,
        file_name="esg_literature_paper_centric.md",
        mime="text/markdown",
    )

with col2:
    st.download_button(
        "⬇️ Download RQ-Centric Markdown",
        data=rq_md,
        file_name="esg_literature_rq_centric.md",
        mime="text/markdown",
    )
