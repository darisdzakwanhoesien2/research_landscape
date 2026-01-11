# --------------------------------------------------
# Global ESG Research Mapping — RQ ↔ Papers
# With TRUE Unique Papers + RQ Coverage
# --------------------------------------------------

import json
from pathlib import Path
import pandas as pd
import streamlit as st

# ================================
# CONFIG
# ================================

BASE_DIR = Path(__file__).parents[1]   # as requested
DATA_PATH = BASE_DIR / "data" / "registry.json"

st.set_page_config(page_title="Global ESG Literature Map", layout="wide")
st.title("🔗 Global Mapping: Research Questions ↔ Papers")

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
# BUILD GLOBAL MAPPING TABLE
# ================================

rows = []
paper_lookup = {}

for ti, t in enumerate(tracks):
    rq_text = t["meta"].get("research_question", f"RQ_{ti}")

    for p in t.get("papers", []):
        pid = p.get("id")
        title = p.get("input", {}).get("title")

        rows.append({
            "rq": rq_text,
            "paper_id": pid,
            "title": title,
            "method": p.get("method_category"),
            "trace": p.get("decision_trace_support"),
            "relevance": p.get("relevance_score", 0.0),
            "regulatory": ", ".join(p.get("regulatory_relevance", [])),
        })

        paper_lookup[pid] = p

df = pd.DataFrame(rows)

if df.empty:
    st.warning("No paper mappings found.")
    st.stop()

# ================================
# NORMALIZE TITLE FOR DEDUP
# ================================

df["title_norm"] = (
    df["title"]
    .astype(str)
    .str.lower()
    .str.replace(r"[^a-z0-9]+", " ", regex=True)
    .str.strip()
)

# ================================
# TRUE UNIQUE PAPERS (MERGED)
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
# SIDEBAR FILTERS
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

search = st.sidebar.text_input("Search paper title")

# ================================
# APPLY FILTERS (MAPPING)
# ================================

filtered = df[
    (df["rq"].isin(rq_filter))
    & (df["method"].isin(method_filter))
    & (df["trace"].isin(trace_filter))
    & (df["relevance"] >= min_relevance)
]

if search:
    filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

# ================================
# APPLY FILTERS (UNIQUE)
# ================================

unique_filtered = unique_df[
    (unique_df["method"].str.contains("|".join(method_filter), na=False))
    & (unique_df["trace"].str.contains("|".join(trace_filter), na=False))
    & (unique_df["relevance"] >= min_relevance)
]

if search:
    unique_filtered = unique_filtered[
        unique_filtered["title"].str.contains(search, case=False, na=False)
    ]

# ================================
# VIEW MODE
# ================================

st.subheader("📄 Mapping Table")

view_mode = st.radio(
    "View mode",
    ["RQ ↔ Paper Mapping", "Unique Papers"],
    horizontal=True
)

# ================================
# TABLE DISPLAY
# ================================

if view_mode == "RQ ↔ Paper Mapping":

    st.markdown("##### Mapping Table (RQ ↔ Paper)")

    st.dataframe(
        filtered[["rq", "title", "method", "trace", "relevance", "regulatory"]]
        .sort_values(["rq", "relevance"], ascending=[True, False]),
        use_container_width=True,
    )

else:

    st.markdown("##### Unique Papers (Deduplicated)")

    st.dataframe(
        unique_filtered[["title", "rq_count", "method", "trace", "relevance", "regulatory"]]
        .sort_values(["rq_count", "relevance"], ascending=[False, False]),
        use_container_width=True,
    )

# ================================
# PAPER DETAILS (WITH RQ LIST)
# ================================

st.subheader("🔍 Paper Details")

paper_titles = sorted(unique_filtered["title"].dropna().unique().tolist())

if paper_titles:
    selected_title = st.selectbox("Select a paper", paper_titles)

    selected_row = unique_filtered[unique_filtered["title"] == selected_title].iloc[0]
    selected = paper_lookup[selected_row["paper_id"]]

    st.markdown(f"### {selected_row['title']}")

    # ---- RQ COVERAGE --------------------

    st.markdown("### 🧠 Addressed Research Questions")

    for rq in selected_row["rq"]:
        st.markdown(f"- {rq}")

    st.divider()

    # ---- META ---------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Method Category(s)**")
        st.write(selected_row.get("method"))

        st.markdown("**Decision Trace Support**")
        st.write(selected_row.get("trace"))

        st.markdown("**Max Relevance Score**")
        st.write(selected_row.get("relevance"))

    with col2:
        st.markdown("**Regulatory Relevance**")
        st.write(selected_row.get("regulatory"))

    # ---- CONTENT ------------------------

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

else:
    st.info("No papers available after filtering.")

# ================================
# EXPORT
# ================================

st.divider()

st.download_button(
    "⬇️ Download registry.json",
    data=json.dumps(registry, indent=2),
    file_name="registry.json",
    mime="application/json",
)


# # --------------------------------------------------
# # ESG Research Landscape Explorer
# # Global RQ ↔ Paper Mapping + Unique Paper View
# # --------------------------------------------------

# import json
# from pathlib import Path
# import pandas as pd
# import streamlit as st

# # ================================
# # CONFIG
# # ================================

# BASE_DIR = Path(__file__).parents[1]   # as requested
# DATA_PATH = BASE_DIR / "data" / "registry.json"

# st.set_page_config(page_title="ESG Literature Map", layout="wide")
# st.title("📚 ESG Research Landscape — RQ ↔ Paper Mapping")

# # ================================
# # LOAD DATA
# # ================================

# if not DATA_PATH.exists():
#     st.error(f"registry.json not found at: {DATA_PATH}")
#     st.stop()

# with open(DATA_PATH, "r", encoding="utf-8") as f:
#     registry = json.load(f)

# tracks = registry.get("research_tracks", [])

# if not tracks:
#     st.error("No research_tracks found in registry.json")
#     st.stop()

# # ================================
# # BUILD GLOBAL MAPPING TABLE
# # ================================

# rows = []
# paper_lookup = {}

# for ti, t in enumerate(tracks):
#     rq_text = t["meta"].get("research_question", f"RQ_{ti}")

#     for p in t.get("papers", []):
#         pid = p.get("id")
#         title = p.get("input", {}).get("title")

#         rows.append({
#             "rq": rq_text,
#             "paper_id": pid,
#             "title": title,
#             "method": p.get("method_category"),
#             "trace": p.get("decision_trace_support"),
#             "relevance": p.get("relevance_score", 0.0),
#             "regulatory": ", ".join(p.get("regulatory_relevance", [])),
#         })

#         paper_lookup[pid] = p

# df = pd.DataFrame(rows)

# if df.empty:
#     st.warning("No paper mappings found.")
#     st.stop()

# # ================================
# # UNIQUE PAPER TABLE
# # ================================

# unique_df = (
#     df.groupby("paper_id")
#     .agg({
#         "title": "first",
#         "method": "first",
#         "trace": "first",
#         "relevance": "max",
#         "regulatory": "first",
#         "rq": lambda x: list(sorted(set(x)))
#     })
#     .reset_index()
# )

# unique_df["rq_count"] = unique_df["rq"].apply(len)

# # ================================
# # SIDEBAR FILTERS
# # ================================

# st.sidebar.header("🔍 Filters")

# rq_filter = st.sidebar.multiselect(
#     "Research Questions",
#     sorted(df["rq"].unique().tolist()),
#     default=sorted(df["rq"].unique().tolist()),
# )

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

# search = st.sidebar.text_input("Search paper title")

# # ================================
# # APPLY FILTERS (MAPPING VIEW)
# # ================================

# filtered = df[
#     (df["rq"].isin(rq_filter))
#     & (df["method"].isin(method_filter))
#     & (df["trace"].isin(trace_filter))
#     & (df["relevance"] >= min_relevance)
# ]

# if search:
#     filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

# # ================================
# # APPLY FILTERS (UNIQUE VIEW)
# # ================================

# unique_filtered = unique_df[
#     (unique_df["method"].isin(method_filter))
#     & (unique_df["trace"].isin(trace_filter))
#     & (unique_df["relevance"] >= min_relevance)
# ]

# if search:
#     unique_filtered = unique_filtered[
#         unique_filtered["title"].str.contains(search, case=False, na=False)
#     ]

# # ================================
# # VIEW MODE
# # ================================

# st.subheader("📄 Mapping Table")

# view_mode = st.radio(
#     "View mode",
#     ["RQ ↔ Paper Mapping", "Unique Papers"],
#     horizontal=True
# )

# # ================================
# # TABLE VIEW
# # ================================

# if view_mode == "RQ ↔ Paper Mapping":

#     st.markdown("##### Mapping Table (RQ ↔ Paper)")

#     st.dataframe(
#         filtered[["rq", "title", "method", "trace", "relevance", "regulatory"]]
#         .sort_values(["rq", "relevance"], ascending=[True, False]),
#         use_container_width=True,
#     )

# else:

#     st.markdown("##### Unique Papers")

#     st.dataframe(
#         unique_filtered[["title", "method", "trace", "relevance", "rq_count", "regulatory"]]
#         .sort_values(["rq_count", "relevance"], ascending=[False, False]),
#         use_container_width=True,
#     )

# # ================================
# # PAPER DETAILS (UNIQUE)
# # ================================

# st.subheader("🔍 Paper Details")

# paper_titles = sorted(unique_filtered["title"].dropna().unique().tolist())

# if paper_titles:
#     selected_title = st.selectbox("Select a paper", paper_titles)

#     selected_row = unique_filtered[unique_filtered["title"] == selected_title].iloc[0]
#     selected = paper_lookup[selected_row["paper_id"]]

#     st.markdown(f"### {selected['input']['title']}")

#     # ---- RQ COVERAGE --------------------

#     st.markdown("### 🧠 Addressed Research Questions")

#     for rq in selected_row["rq"]:
#         st.markdown(f"- {rq}")

#     st.divider()

#     # ---- META ---------------------------

#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("**Method Category**")
#         st.write(selected.get("method_category"))

#         st.markdown("**Decision Trace Support**")
#         st.write(selected.get("decision_trace_support"))

#         st.markdown("**Relevance Score**")
#         st.write(selected.get("relevance_score"))

#     with col2:
#         st.markdown("**Regulatory Relevance**")
#         for r in selected.get("regulatory_relevance", []):
#             st.write(f"- {r}")

#     # ---- CONTENT ------------------------

#     st.markdown("**Abstract**")
#     st.write(selected.get("input", {}).get("abstract", ""))

#     st.markdown("**Interpretability Mechanisms**")
#     for m in selected.get("interpretability_mechanisms", []):
#         st.write(f"- {m}")

#     st.markdown("**Key Contributions**")
#     for k in selected.get("key_contributions", []):
#         st.write(f"- {k}")

#     st.markdown("**External Links**")
#     for l in selected.get("external_links", []):
#         st.markdown(f"- [{l['type']}]({l['url']}) — {l.get('source','')}")

# else:
#     st.info("No papers available after filtering.")

# # ================================
# # EXPORT
# # ================================

# st.divider()

# st.download_button(
#     "⬇️ Download registry.json",
#     data=json.dumps(registry, indent=2),
#     file_name="registry.json",
#     mime="application/json",
# )
