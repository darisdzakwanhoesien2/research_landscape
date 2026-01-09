import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
import re

# ======================================================
# CONFIG
# ======================================================

st.set_page_config(page_title="ACL Research Landscape", layout="wide")
st.title("📚 ACL / EMNLP Research Landscape Dashboard")

DATA_PATH = Path("data/scrap_example/extracted.json")

# ======================================================
# LOAD
# ======================================================

if not DATA_PATH.exists():
    st.error(f"File not found: {DATA_PATH}")
    st.stop()

with open(DATA_PATH, "r", encoding="utf-8") as f:
    obj = json.load(f)

links = obj.get("links", {})

st.success(f"Loaded {len(links)} page links")

# ======================================================
# PATTERNS
# ======================================================

paper_pattern = re.compile(r"/20\d{2}\.([a-z0-9\-]+)\.(\d+)/")
proc_pattern = re.compile(r"/20\d{2}\.([a-z0-9\-]+)\.0/")

# ======================================================
# PARSE IN PAGE ORDER (IMPORTANT)
# ======================================================

papers = []
people = []
paper_author_edges = []

current_paper = None

for name, url in links.items():

    if not isinstance(url, str):
        continue

    # normalize
    path = url.replace("https://aclanthology.org", "")

    # ---------------- PROCEEDINGS ----------------
    if proc_pattern.search(path):
        continue

    # ---------------- PAPER ----------------
    m_paper = paper_pattern.search(path)
    if m_paper:
        track = m_paper.group(1)
        paper_no = int(m_paper.group(2))
        paper_id = f"{track}.{paper_no}"

        current_paper = {
            "paper_id": paper_id,
            "title": name,
            "url": path,
            "track": track,
            "paper_no": paper_no,
        }
        papers.append(current_paper)
        continue

    # ---------------- PERSON ----------------
    if path.startswith("/people/") and current_paper is not None:
        people.append({"name": name, "url": path})

        paper_author_edges.append({
            "paper_id": current_paper["paper_id"],
            "title": current_paper["title"],
            "author": name
        })
        continue

# ======================================================
# DATAFRAMES
# ======================================================

papers_df = pd.DataFrame(papers)
people_df = pd.DataFrame(people).drop_duplicates()
edges_df = pd.DataFrame(paper_author_edges)

# ======================================================
# METRICS
# ======================================================

st.subheader("📈 Overview")

c1, c2, c3 = st.columns(3)
c1.metric("Papers", len(papers_df))
c2.metric("Authors", len(people_df))
c3.metric("Edges (Authorships)", len(edges_df))

# ======================================================
# PAPER DISTRIBUTION
# ======================================================

st.subheader("📊 Papers by Track")

if not papers_df.empty:
    track_counts = papers_df["track"].value_counts()

    fig, ax = plt.subplots()
    track_counts.plot(kind="bar", ax=ax)
    ax.set_xlabel("Track")
    ax.set_ylabel("Number of Papers")
    ax.set_title("Paper Distribution by Track")
    plt.xticks(rotation=45)

    st.pyplot(fig)

# ======================================================
# TABLES
# ======================================================

with st.expander("📄 Papers Table"):
    st.dataframe(papers_df.sort_values(["track", "paper_no"]), use_container_width=True)

with st.expander("👥 Authors Table"):
    st.dataframe(people_df, use_container_width=True)

with st.expander("🔗 Paper–Author Edges"):
    st.dataframe(edges_df, use_container_width=True)

# ======================================================
# CO-AUTHOR NETWORK
# ======================================================

st.subheader("🧠 Co-Author Network")

G = nx.Graph()

for _, row in edges_df.iterrows():
    G.add_node(row["author"], type="author")
    G.add_node(row["paper_id"], type="paper")
    G.add_edge(row["author"], row["paper_id"])

# Project to co-author graph
coauthor = nx.Graph()

for paper in edges_df["paper_id"].unique():
    authors = edges_df[edges_df["paper_id"] == paper]["author"].tolist()
    for i in range(len(authors)):
        for j in range(i + 1, len(authors)):
            if coauthor.has_edge(authors[i], authors[j]):
                coauthor[authors[i]][authors[j]]["weight"] += 1
            else:
                coauthor.add_edge(authors[i], authors[j], weight=1)

# Limit graph size for display
MAX_NODES = st.slider("Max authors to visualize", 20, 300, 80)

top_authors = sorted(coauthor.degree, key=lambda x: x[1], reverse=True)[:MAX_NODES]
nodes = [n for n, _ in top_authors]
subG = coauthor.subgraph(nodes)

fig2, ax2 = plt.subplots(figsize=(10, 8))
pos = nx.spring_layout(subG, seed=42, k=0.4)

nx.draw(
    subG, pos,
    ax=ax2,
    node_size=80,
    with_labels=False
)

ax2.set_title("Co-Author Collaboration Network")
st.pyplot(fig2)

# ======================================================
# DOWNLOADS
# ======================================================

st.subheader("⬇️ Export for Graph / Neo4j")

st.download_button(
    "Download Papers CSV",
    papers_df.to_csv(index=False).encode("utf-8"),
    file_name="papers.csv",
    mime="text/csv"
)

st.download_button(
    "Download Authors CSV",
    people_df.to_csv(index=False).encode("utf-8"),
    file_name="authors.csv",
    mime="text/csv"
)

st.download_button(
    "Download Paper–Author Edges CSV",
    edges_df.to_csv(index=False).encode("utf-8"),
    file_name="paper_author_edges.csv",
    mime="text/csv"
)
