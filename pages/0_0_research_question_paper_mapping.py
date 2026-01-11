# --------------------------------------------------
# ESG Neurosymbolic Literature Explorer
# Global RQ ↔ Paper Mapping Graph
# --------------------------------------------------

import json
from pathlib import Path
import pandas as pd
import streamlit as st

from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile

# ================================
# CONFIG
# ================================

BASE_DIR = Path(__file__).parents[1]   # 👈 as you requested
DATA_PATH = BASE_DIR / "data" / "registry.json"

st.set_page_config(page_title="ESG Literature Map", layout="wide")
st.title("📚 ESG Research Landscape — RQ ↔ Paper Mapping")

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
# BUILD GLOBAL TABLE
# ================================

rows = []
paper_lookup = {}

for ti, t in enumerate(tracks):
    rq_id = f"RQ_{ti}"
    rq_text = t["meta"]["research_question"]

    for p in t.get("papers", []):
        pid = p.get("id")
        title = p.get("input", {}).get("title")

        rows.append({
            "rq_id": rq_id,
            "rq": rq_text,
            "paper_id": pid,
            "title": title,
            "method": p.get("method_category"),
            "trace": p.get("decision_trace_support"),
            "relevance": p.get("relevance_score"),
            "regulatory": ", ".join(p.get("regulatory_relevance", [])),
        })

        paper_lookup[pid] = p

df = pd.DataFrame(rows)

if df.empty:
    st.warning("No paper mappings found.")
    st.stop()

# ================================
# SIDEBAR FILTERS
# ================================

st.sidebar.header("🔍 Global Filters")

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

filtered = df[
    (df["rq"].isin(rq_filter))
    & (df["method"].isin(method_filter))
    & (df["trace"].isin(trace_filter))
    & (df["relevance"] >= min_relevance)
]

if search:
    filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

# ================================
# GLOBAL RELATIONAL GRAPH
# ================================

st.subheader("🔗 Global Mapping: Research Questions ↔ Papers")

show_graph = st.checkbox("Show relational graph", value=True)

if show_graph:

    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="black")

    # ---- add RQ nodes (left column)
    rq_positions = {}
    for i, rq in enumerate(sorted(filtered["rq"].unique())):
        node_id = f"RQ::{i}"
        rq_positions[rq] = node_id

        net.add_node(
            node_id,
            label=f"RQ {i+1}",
            title=rq,
            shape="box",
            color="#4F81BD",
            x=-400,
            y=i * 150,
            fixed=True,
            size=30,
        )

    # ---- add Paper nodes (right column)
    paper_positions = {}
    for j, pid in enumerate(sorted(filtered["paper_id"].unique())):
        node_id = f"P::{pid}"
        paper_positions[pid] = node_id

        title = paper_lookup[pid]["input"]["title"]

        net.add_node(
            node_id,
            label=title[:40] + "..." if len(title) > 40 else title,
            title=title,
            shape="ellipse",
            color="#9BBB59",
            x=400,
            y=j * 120,
            fixed=True,
            size=20,
        )

    # ---- edges
    for _, r in filtered.iterrows():
        net.add_edge(rq_positions[r["rq"]], paper_positions[r["paper_id"]])

    # ---- render
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        components.html(open(tmp.name, "r", encoding="utf-8").read(), height=750, scrolling=True)

# ================================
# TABLE VIEW
# ================================

st.subheader("📄 Mapping Table (RQ ↔ Paper)")

st.dataframe(
    filtered[["rq", "title", "method", "trace", "relevance", "regulatory"]]
    .sort_values(["rq", "relevance"], ascending=[True, False]),
    use_container_width=True,
)

# ================================
# PAPER DETAIL (WITH RQ COVERAGE)
# ================================

st.subheader("🔍 Paper Details")

titles = sorted(filtered["title"].dropna().unique().tolist())

if titles:
    selected_title = st.selectbox("Select a paper", titles)

    selected_rows = df[df["title"] == selected_title]

    selected_row = selected_rows.iloc[0]
    selected = paper_lookup[selected_row["paper_id"]]

    st.markdown(f"### {selected['input']['title']}")

    # ---- RQ COVERAGE ---------------------------------

    st.markdown("### 🧠 Addressed Research Questions")

    rq_list = selected_rows["rq"].unique().tolist()

    st.caption(f"This paper is mapped to {len(rq_list)} research question(s):")

    for rq in rq_list:
        st.markdown(f"- {rq}")

    st.divider()

    # ---- PAPER META ----------------------------------

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

    # ---- CONTENT -------------------------------------

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


# # ================================
# # PAPER DETAIL
# # ================================

# st.subheader("🔍 Paper Details")

# titles = sorted(filtered["title"].dropna().unique().tolist())

# if titles:
#     selected_title = st.selectbox("Select a paper", titles)
#     selected_row = filtered[filtered["title"] == selected_title].iloc[0]
#     selected = paper_lookup[selected_row["paper_id"]]

#     st.markdown(f"### {selected['input']['title']}")

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

#     st.markdown("**Abstract**")
#     st.write(selected.get("input", {}).get("abstract", ""))

#     st.markdown("**Interpretability Mechanisms**")
#     for m in selected.get("interpretability_mechanisms", []):
#         st.write(f"- {m}")

#     st.markdown("**External Links**")
#     for l in selected.get("external_links", []):
#         st.markdown(f"- [{l['type']}]({l['url']}) — {l.get('source','')}")

# else:
#     st.info("No papers available after filtering.")

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
# # ESG Neurosymbolic Literature Explorer + Graph View
# # --------------------------------------------------

# import json
# from pathlib import Path
# import pandas as pd
# import streamlit as st

# from pyvis.network import Network
# import streamlit.components.v1 as components
# import tempfile

# # ================================
# # CONFIG
# # ================================

# BASE_DIR = Path(__file__).parents[1]
# DATA_PATH = BASE_DIR / "data" / "registry.json"

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

# tracks = registry.get("research_tracks", [])

# if not tracks:
#     st.error("No research_tracks found in registry.json")
#     st.stop()

# # ================================
# # SIDEBAR — RQ SELECT
# # ================================

# st.sidebar.header("🧠 Research Questions")

# rq_labels = [t["meta"]["research_question"] for t in tracks]

# selected_rq = st.sidebar.selectbox("Select Research Question", rq_labels)

# track = next(t for t in tracks if t["meta"]["research_question"] == selected_rq)
# meta = track.get("meta", {})
# papers = track.get("papers", [])

# # ================================
# # META DISPLAY
# # ================================

# st.caption("Research Question")
# st.info(meta.get("research_question", ""))

# st.caption(f"Generated at: {meta.get('generated_at', 'unknown')}")
# if meta.get("notes"):
#     st.caption(meta.get("notes"))

# # ================================
# # FLATTEN FOR TABLE
# # ================================

# rows = []
# paper_map = {}

# for p in papers:
#     links = p.get("external_links", [])

#     doi = next((l["url"] for l in links if l.get("type") == "doi"), "")
#     pdf = next((l["url"] for l in links if l.get("type") == "pdf"), "")

#     row = {
#         "id": p.get("id"),
#         "title": p.get("input", {}).get("title"),
#         "method": p.get("method_category"),
#         "trace": p.get("decision_trace_support"),
#         "relevance": p.get("relevance_score"),
#         "regulatory": ", ".join(p.get("regulatory_relevance", [])),
#         "doi": doi,
#         "pdf": pdf,
#     }

#     rows.append(row)
#     paper_map[row["id"]] = p

# df = pd.DataFrame(rows)

# if df.empty:
#     st.warning("No papers found for this research question.")
#     st.stop()

# # ================================
# # SIDEBAR FILTERS
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
# # RELATIONAL GRAPH
# # ================================

# st.subheader("🔗 Research Question ↔ Paper Relationship Graph")

# show_graph = st.checkbox("Show relational graph", value=True)

# if show_graph:

#     net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")

#     # RQ node
#     rq_node_id = "RQ"
#     net.add_node(
#         rq_node_id,
#         label="Research Question",
#         title=meta.get("research_question", ""),
#         shape="box",
#         color="#4F81BD",
#         size=35,
#     )

#     for _, row in filtered.iterrows():

#         pid = row["id"]
#         title = row["title"]

#         tooltip = f"""
#         <b>{title}</b><br>
#         Method: {row['method']}<br>
#         Trace: {row['trace']}<br>
#         Relevance: {row['relevance']}
#         """

#         net.add_node(
#             pid,
#             label=title[:45] + "..." if len(title) > 45 else title,
#             title=tooltip,
#             shape="ellipse",
#             color="#9BBB59",
#             size=18 + int(row["relevance"] * 20),
#         )

#         net.add_edge(rq_node_id, pid)

#     net.toggle_physics(True)

#     with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
#         net.save_graph(tmp.name)
#         components.html(open(tmp.name, "r", encoding="utf-8").read(), height=650, scrolling=True)

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

# title_map = {p.get("input", {}).get("title"): p for p in papers if p.get("input", {}).get("title")}

# titles = list(title_map.keys())

# if titles:
#     selected_title = st.selectbox("Select a paper", titles)
#     selected = title_map[selected_title]

#     st.markdown(f"### {selected['input']['title']}")

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

#     st.markdown("**Suggested Citations**")
#     for c in selected.get("suggested_citations", []):
#         st.markdown(f"- [{c['title']}]({c['link']}) — {c['reason']}")

# else:
#     st.info("No paper titles available for detail view.")

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
