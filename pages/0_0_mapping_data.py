# streamlit_app.py
# --------------------------------------------------
# ESG Neurosymbolic Literature Explorer
# --------------------------------------------------
# Features:
# - Loads registry.json (your enriched literature database)
# - Table + filters (method, trace support, regulatory relevance)
# - Clickable external links
# - Paper detail view
# - Supports iterative updates (just replace/append JSON)
# --------------------------------------------------

# --------------------------------------------------
# ESG Neurosymbolic Literature Explorer (Multi-RQ)
# --------------------------------------------------

import json
from pathlib import Path
import pandas as pd
import streamlit as st

# ================================
# CONFIG
# ================================

BASE_DIR = Path(__file__).parents[1]
DATA_PATH = BASE_DIR / "data" / "registry.json"

st.set_page_config(page_title="ESG Neuro-Symbolic Literature", layout="wide")
st.title("📚 ESG Neuro-Symbolic Literature Explorer")

# ================================
# LOAD DATA
# ================================

if not DATA_PATH.exists():
    st.error(f"registry.json not found at: {DATA_PATH}")
    st.stop()

with open(DATA_PATH, "r", encoding="utf-8") as f:
    registry = json.load(f)

tracks = registry.get("research_tracks", [])

if not tracks:
    st.error("No research_tracks found in registry.json")
    st.stop()

# ================================
# SELECT RESEARCH QUESTION
# ================================

st.sidebar.header("🧠 Research Questions")

rq_labels = [t["meta"]["research_question"] for t in tracks]

selected_rq = st.sidebar.selectbox("Select Research Question", rq_labels)

track = next(t for t in tracks if t["meta"]["research_question"] == selected_rq)
meta = track.get("meta", {})
papers = track.get("papers", [])

# ================================
# META DISPLAY
# ================================

st.caption("Research Question:")
st.info(meta.get("research_question", ""))

st.caption(f"Generated at: {meta.get('generated_at', 'unknown')}")
if meta.get("notes"):
    st.caption(meta.get("notes"))

# ================================
# FLATTEN FOR TABLE
# ================================

rows = []
for p in papers:
    links = p.get("external_links", [])

    doi = next((l["url"] for l in links if l.get("type") == "doi"), "")
    pdf = next((l["url"] for l in links if l.get("type") == "pdf"), "")

    rows.append({
        "id": p.get("id"),
        "title": p.get("input", {}).get("title"),
        "method": p.get("method_category"),
        "trace": p.get("decision_trace_support"),
        "relevance": p.get("relevance_score"),
        "regulatory": ", ".join(p.get("regulatory_relevance", [])),
        "doi": doi,
        "pdf": pdf,
    })

df = pd.DataFrame(rows)

if df.empty:
    st.warning("No papers found for this research question.")
    st.stop()

# ================================
# FILTERS
# ================================

st.sidebar.header("🔍 Filters")

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

filtered = df[
    (df["method"].isin(method_filter))
    & (df["trace"].isin(trace_filter))
    & (df["relevance"] >= min_relevance)
]

if search:
    filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

# ================================
# TABLE VIEW
# ================================

st.subheader("📄 Paper Overview")

st.dataframe(
    filtered.sort_values("relevance", ascending=False),
    use_container_width=True,
)

# ================================
# DETAIL VIEW
# ================================

st.subheader("🔍 Paper Details")

title_map = {p.get("input", {}).get("title"): p for p in papers}
titles = list(title_map.keys())

selected_title = st.selectbox("Select a paper", titles)

selected = title_map[selected_title]

st.markdown(f"### {selected['input']['title']}")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Method Category**")
    st.write(selected.get("method_category"))

    st.markdown("**Decision Trace Support**")
    st.write(selected.get("decision_trace_support"))

    st.markdown("**Relevance Score**")
    st.write(selected.get("relevance_score"))

with col2:
    st.markdown("**Regulatory Relevance**")
    for r in selected.get("regulatory_relevance", []):
        st.write(f"- {r}")

st.markdown("**Abstract**")
st.write(selected.get("input", {}).get("abstract", ""))

st.markdown("**Interpretability Mechanisms**")
for m in selected.get("interpretability_mechanisms", []):
    st.write(f"- {m}")

st.markdown("**Key Contributions**")
for k in selected.get("key_contributions", []):
    st.write(f"- {k}")

st.markdown("**External Links**")
for l in selected.get("external_links", []):
    st.markdown(f"- [{l['type']}]({l['url']}) — {l.get('source','')}")

st.markdown("**Suggested Citations**")
for c in selected.get("suggested_citations", []):
    st.markdown(f"- [{c['title']}]({c['link']}) — {c['reason']}")

# ================================
# EXPORT
# ================================

st.download_button(
    "⬇️ Download registry.json",
    data=json.dumps(registry, indent=2),
    file_name="registry.json",
    mime="application/json",
)


# import json
# from pathlib import Path
# import pandas as pd
# import streamlit as st

# # ================================
# # CONFIG
# # ================================

# BASE_DIR = Path(__file__).parents[1]
# DATA_PATH = BASE_DIR / "data" / "registry.json"   # <-- put your JSON here

# st.set_page_config(page_title="ESG Neuro-Symbolic Literature", layout="wide")
# st.title("📚 ESG Neuro-Symbolic Literature Explorer")

# # ================================
# # LOAD DATA
# # ================================

# if not DATA_PATH.exists():
#     st.error(f"registry.json not found at: {DATA_PATH}")
#     st.stop()

# with open(DATA_PATH, "r", encoding="utf-8") as f:
#     registry = json.load(f)

# papers = registry.get("papers", [])
# meta = registry.get("meta", {})

# st.caption("Research Question:")
# st.info(meta.get("research_question", ""))

# st.caption(f"Last generated: {meta.get('generated_at', 'unknown')}")

# # ================================
# # FLATTEN FOR TABLE
# # ================================

# rows = []
# for p in papers:
#     links = p.get("external_links", [])
#     doi = next((l["url"] for l in links if l["type"] == "doi"), "")
#     pdf = next((l["url"] for l in links if l["type"] == "pdf"), "")
#     rows.append({
#         "id": p.get("id"),
#         "title": p.get("input", {}).get("title"),
#         "method": p.get("method_category"),
#         "trace": p.get("decision_trace_support"),
#         "relevance": p.get("relevance_score"),
#         "doi": doi,
#         "pdf": pdf,
#         "regulatory": ", ".join(p.get("regulatory_relevance", [])),
#     })

# df = pd.DataFrame(rows)

# # ================================
# # FILTERS
# # ================================

# st.sidebar.header("🔍 Filters")

# method_filter = st.sidebar.multiselect(
#     "Method Category",
#     sorted(df["method"].dropna().unique().tolist()),
#     default=sorted(df["method"].dropna().unique().tolist()),
# )

# trace_filter = st.sidebar.multiselect(
#     "Decision Trace Support",
#     sorted(df["trace"].dropna().unique().tolist()),
#     default=sorted(df["trace"].dropna().unique().tolist()),
# )

# min_relevance = st.sidebar.slider("Minimum relevance", 0.0, 1.0, 0.7, 0.01)

# search = st.sidebar.text_input("Search title")

# filtered = df[
#     (df["method"].isin(method_filter))
#     & (df["trace"].isin(trace_filter))
#     & (df["relevance"] >= min_relevance)
# ]

# if search:
#     filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

# # ================================
# # TABLE VIEW
# # ================================

# st.subheader("📄 Paper Overview")

# st.dataframe(
#     filtered.sort_values("relevance", ascending=False),
#     use_container_width=True,
# )

# # ================================
# # DETAIL VIEW
# # ================================

# st.subheader("🔍 Paper Details")

# paper_titles = [p.get("input", {}).get("title") for p in papers]
# selected_title = st.selectbox("Select a paper", paper_titles)

# selected = next(p for p in papers if p.get("input", {}).get("title") == selected_title)

# st.markdown(f"### {selected['input']['title']}")

# col1, col2 = st.columns(2)

# with col1:
#     st.markdown("**Method Category**")
#     st.write(selected.get("method_category"))

#     st.markdown("**Decision Trace Support**")
#     st.write(selected.get("decision_trace_support"))

#     st.markdown("**Relevance Score**")
#     st.write(selected.get("relevance_score"))

# with col2:
#     st.markdown("**Regulatory Relevance**")
#     for r in selected.get("regulatory_relevance", []):
#         st.write(f"- {r}")

# st.markdown("**Abstract**")
# st.write(selected.get("input", {}).get("abstract", ""))

# st.markdown("**Interpretability Mechanisms**")
# for m in selected.get("interpretability_mechanisms", []):
#     st.write(f"- {m}")

# st.markdown("**Key Contributions**")
# for k in selected.get("key_contributions", []):
#     st.write(f"- {k}")

# st.markdown("**External Links**")
# for l in selected.get("external_links", []):
#     st.markdown(f"- [{l['type']}]({l['url']}) — {l.get('source','')}")

# st.markdown("**Suggested Citations**")
# for c in selected.get("suggested_citations", []):
#     st.markdown(f"- [{c['title']}]({c['link']}) — {c['reason']}")

# # ================================
# # EXPORT
# # ================================

# st.download_button(
#     "⬇️ Download registry.json",
#     data=json.dumps(registry, indent=2),
#     file_name="registry.json",
#     mime="application/json",
# )
