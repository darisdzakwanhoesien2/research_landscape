# --------------------------------------------------
# ESG Literature Mapping — Registry + CSV MERGED
# Fast: fuzzy merge once, then table-driven UI
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

st.set_page_config(page_title="Merged ESG Literature Table", layout="wide")
st.title("📚 ESG Literature — Registry + CSV Merged Table")

# ================================
# HELPERS
# ================================

def norm(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


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
# CSV UPLOAD + FUZZY MERGE
# ================================

st.sidebar.header("📥 External Paper Database (CSV)")
csv_file = st.sidebar.file_uploader(
    "Upload CSV with columns: title, doi, abstract",
    type=["csv"]
)

@st.cache_data(show_spinner="Merging CSV database with registry...")
def merge_with_csv(unique_df, csv_bytes):

    db_df = pd.read_csv(csv_bytes)
    db_df["title_norm"] = db_df["title"].apply(norm)

    merged_rows = []

    for _, u in unique_df.iterrows():
        query = norm(u["title"])

        best_score = 0
        best_row = None

        # cheap blocking
        q_words = set(query.split())

        for _, r in db_df.iterrows():
            if not q_words.intersection(r["title_norm"].split()):
                continue

            score = SequenceMatcher(None, query, r["title_norm"]).ratio()
            if score > best_score:
                best_score = score
                best_row = r

        merged = u.to_dict()
        if best_score >= 0.82 and best_row is not None:
            merged["db_doi"] = best_row.get("doi")
            merged["db_abstract"] = best_row.get("abstract")
            merged["match_score"] = round(best_score, 3)
        else:
            merged["db_doi"] = ""
            merged["db_abstract"] = ""
            merged["match_score"] = 0.0

        merged_rows.append(merged)

    return pd.DataFrame(merged_rows)


merged_df = unique_df.copy()
merged_df["db_doi"] = ""
merged_df["db_abstract"] = ""
merged_df["match_score"] = 0.0

if csv_file:
    try:
        merged_df = merge_with_csv(unique_df, csv_file)
        st.sidebar.success("CSV merged into registry table")
    except Exception as e:
        st.sidebar.error(f"Merge failed: {e}")

# ================================
# FILTERS
# ================================

st.sidebar.header("🔍 Filters")

method_filter = st.sidebar.multiselect(
    "Method Category",
    sorted(merged_df["method"].dropna().unique().tolist()),
    default=sorted(merged_df["method"].dropna().unique().tolist()),
)

trace_filter = st.sidebar.multiselect(
    "Decision Trace Support",
    sorted(merged_df["trace"].dropna().unique().tolist()),
    default=sorted(merged_df["trace"].dropna().unique().tolist()),
)

min_relevance = st.sidebar.slider("Minimum relevance", 0.0, 1.0, 0.7, 0.01)
min_match = st.sidebar.slider("Minimum CSV match score", 0.0, 1.0, 0.0, 0.05)

search = st.sidebar.text_input("Search title")

filt = merged_df[
    (merged_df["method"].str.contains("|".join(method_filter), na=False))
    & (merged_df["trace"].str.contains("|".join(trace_filter), na=False))
    & (merged_df["relevance"] >= min_relevance)
    & (merged_df["match_score"] >= min_match)
]

if search:
    filt = filt[filt["title"].str.contains(search, case=False, na=False)]

# ================================
# TABLE
# ================================

st.subheader("📄 Merged Literature Table")

st.dataframe(
    filt[
        ["title", "rq_count", "method", "trace", "relevance", "match_score", "db_doi"]
    ].sort_values(["match_score", "relevance"], ascending=False),
    use_container_width=True,
)

# ================================
# PAPER DETAILS
# ================================

st.subheader("🔍 Paper Details")

titles = filt["title"].dropna().unique().tolist()

if titles:
    sel = st.selectbox("Select paper", titles)
    row = filt[filt["title"] == sel].iloc[0]
    paper = paper_lookup[row["paper_id"]]

    st.markdown(f"## {row['title']}")

    st.markdown("### 🧠 Addressed Research Questions")
    for rq in row["rq"]:
        st.markdown(f"- {rq}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Method**")
        st.write(row["method"])
        st.markdown("**Decision Trace**")
        st.write(row["trace"])
        st.markdown("**Relevance**")
        st.write(row["relevance"])

    with col2:
        st.markdown("**Regulatory**")
        st.write(row["regulatory"])
        st.markdown("**CSV Match Score**")
        st.write(row["match_score"])
        st.markdown("**DOI (CSV)**")
        st.write(row["db_doi"])

    st.markdown("### 📄 Abstract (Registry)")
    st.write(paper.get("input", {}).get("abstract", ""))

    if row["db_abstract"]:
        st.markdown("### 🗄 Abstract (CSV Database)")
        st.write(row["db_abstract"])

else:
    st.info("No papers available after filtering.")
