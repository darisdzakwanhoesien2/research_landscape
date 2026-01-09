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
st.title("📚 ACL Research Landscape — Cluster-Aware Dashboard")

BASE_URL = "https://aclanthology.org"
DATA_ROOT = Path("data")

# ======================================================
# FILE SELECTOR
# ======================================================

st.sidebar.header("📁 Dataset Selection")

json_files = sorted(DATA_ROOT.rglob("extracted.json"))

if not json_files:
    st.error(f"No extracted.json files found under {DATA_ROOT}")
    st.stop()

file_map = {str(p.relative_to(DATA_ROOT)): p for p in json_files}

selected_key = st.sidebar.selectbox(
    "Select scraped dataset",
    list(file_map.keys())
)

DATA_PATH = file_map[selected_key]
st.sidebar.caption(f"Loaded: {DATA_PATH}")

# ======================================================
# LOAD JSON
# ======================================================

with open(DATA_PATH, "r", encoding="utf-8") as f:
    obj = json.load(f)

links = obj.get("links", {})
st.success(f"Loaded {len(links)} links")

# ======================================================
# REGEX PATTERNS
# ======================================================

PATTERNS = {
    "paper": re.compile(r"/20\d{2}\.[a-z0-9\-]+\.\d+/"),
    "volume": re.compile(r"^/volumes/"),
    "event": re.compile(r"^/events/"),
    "venue": re.compile(r"^/venues/"),
    "sig": re.compile(r"^/sigs/"),
    "person": re.compile(r"^/people/"),
}

# ======================================================
# CLASSIFY LINKS
# ======================================================

records = []

for name, url in links.items():
    if not isinstance(url, str):
        continue

    path = url.replace(BASE_URL, "")

    cluster = "other"
    for k, pat in PATTERNS.items():
        if pat.search(path):
            cluster = k
            break

    records.append({
        "label": name,
        "path": path,
        "url": BASE_URL + path if path.startswith("/") else url,
        "cluster": cluster
    })

df = pd.DataFrame(records)

# ======================================================
# OVERVIEW
# ======================================================

st.subheader("📊 Link Cluster Overview")

cluster_counts = df["cluster"].value_counts()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Links", len(df))
c2.metric("Volumes", cluster_counts.get("volume", 0))
c3.metric("Papers", cluster_counts.get("paper", 0))
c4.metric("People", cluster_counts.get("person", 0))

fig, ax = plt.subplots()
cluster_counts.plot(kind="bar", ax=ax)
ax.set_ylabel("Count")
ax.set_title("Link Cluster Distribution")
plt.xticks(rotation=45)
st.pyplot(fig)

# ======================================================
# CLUSTER FILTER
# ======================================================

st.subheader("🔍 Browse by Cluster")

cluster_sel = st.selectbox(
    "Select cluster",
    sorted(df["cluster"].unique())
)

cluster_df = df[df["cluster"] == cluster_sel]

st.dataframe(cluster_df, use_container_width=True)

# ======================================================
# PAPER → AUTHOR GRAPH (ONLY IF PAPER PAGE)
# ======================================================

st.subheader("🧠 Paper–Author Network (if applicable)")

paper_df = df[df["cluster"] == "paper"]
person_df = df[df["cluster"] == "person"]

edges = []
current_paper = None

for name, url in links.items():
    if not isinstance(url, str):
        continue

    path = url.replace(BASE_URL, "")

    if PATTERNS["paper"].search(path):
        current_paper = name
        continue

    if PATTERNS["person"].search(path) and current_paper:
        edges.append({
            "paper": current_paper,
            "author": name
        })

edges_df = pd.DataFrame(edges)

if len(edges_df) == 0:
    st.info("No paper–author relations detected in this dataset.")
else:
    st.success(f"Detected {len(edges_df)} authorships")

    # build co-author network
    G = nx.Graph()

    for paper in edges_df["paper"].unique():
        authors = edges_df[edges_df["paper"] == paper]["author"].tolist()
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                if G.has_edge(authors[i], authors[j]):
                    G[authors[i]][authors[j]]["weight"] += 1
                else:
                    G.add_edge(authors[i], authors[j], weight=1)

    MAX_NODES = st.slider("Max authors to visualize", 20, min(300, len(G)), min(80, len(G)))

    top_authors = sorted(G.degree, key=lambda x: x[1], reverse=True)[:MAX_NODES]
    nodes = [n for n, _ in top_authors]
    subG = G.subgraph(nodes)

    fig2, ax2 = plt.subplots(figsize=(10, 8))
    pos = nx.spring_layout(subG, seed=42, k=0.6)

    nx.draw(
        subG, pos,
        ax=ax2,
        node_size=60,
        with_labels=False
    )

    ax2.set_title("Co-Author Collaboration Network")
    st.pyplot(fig2)

# ======================================================
# VOLUME → BIB LINK BUILDER
# ======================================================

st.subheader("📥 Volume → BibTeX Links")

vol_df = df[df["cluster"] == "volume"].copy()

if not vol_df.empty:
    vol_df["bib_url"] = vol_df["path"].apply(
        lambda p: f"https://aclanthology.org{p}.bib"
    )

    st.dataframe(vol_df[["label", "bib_url"]], use_container_width=True)

    bib_list = "\n".join(vol_df["bib_url"].tolist())

    st.text_area("Bulk BibTeX URLs", bib_list, height=200)

    st.download_button(
        "Download BibTeX URL List",
        bib_list.encode("utf-8"),
        file_name="volume_bib_urls.txt"
    )
else:
    st.info("No volume links in this dataset.")

# ======================================================
# EXPORT
# ======================================================

st.subheader("⬇️ Export All Links")

st.download_button(
    "Download All Links CSV",
    df.to_csv(index=False).encode("utf-8"),
    file_name="acl_links_all_clusters.csv",
    mime="text/csv"
)

if len(edges_df) > 0:
    st.download_button(
        "Download Paper–Author Edges",
        edges_df.to_csv(index=False).encode("utf-8"),
        file_name="paper_author_edges.csv",
        mime="text/csv"
    )


# import streamlit as st
# import json
# import pandas as pd
# import matplotlib.pyplot as plt
# import networkx as nx
# from pathlib import Path
# import re

# # ======================================================
# # CONFIG
# # ======================================================

# st.set_page_config(page_title="ACL Research Landscape", layout="wide")
# st.title("📚 ACL / EMNLP Research Landscape Dashboard")

# BASE_URL = "https://aclanthology.org"
# DATA_ROOT = Path("data/scrap_example")

# # ======================================================
# # FILE SELECTOR
# # ======================================================

# st.sidebar.header("📁 Dataset Selection")

# json_files = sorted(DATA_ROOT.rglob("extracted.json"))

# if not json_files:
#     st.error(f"No extracted.json files found under {DATA_ROOT}")
#     st.stop()

# file_map = {str(p.relative_to(DATA_ROOT)): p for p in json_files}

# selected_key = st.sidebar.selectbox(
#     "Select scraped dataset",
#     list(file_map.keys())
# )

# DATA_PATH = file_map[selected_key]

# st.sidebar.caption(f"Loaded from: {DATA_PATH}")

# # ======================================================
# # LOAD
# # ======================================================

# with open(DATA_PATH, "r", encoding="utf-8") as f:
#     obj = json.load(f)

# links = obj.get("links", {})

# st.success(f"Loaded {len(links)} page links")

# # ======================================================
# # REGEX PATTERNS
# # ======================================================

# paper_pattern = re.compile(r"/20\d{2}\.([a-z0-9\-]+)\.(\d+)/")
# proc_pattern = re.compile(r"/20\d{2}\.([a-z0-9\-]+)\.0/")

# # ======================================================
# # PARSE IN PAGE ORDER (PAPER → AUTHORS)
# # ======================================================

# papers = []
# people = []
# paper_author_edges = []

# current_paper = None

# for name, url in links.items():

#     if not isinstance(url, str):
#         continue

#     # normalize to path
#     path = url.replace(BASE_URL, "")

#     # ---------------- PROCEEDINGS ----------------
#     if proc_pattern.search(path):
#         continue

#     # ---------------- PAPER ----------------
#     m_paper = paper_pattern.search(path)
#     if m_paper:
#         track = m_paper.group(1)
#         paper_no = int(m_paper.group(2))
#         paper_id = f"{track}.{paper_no}"

#         current_paper = {
#             "paper_id": paper_id,
#             "title": name,
#             "url": BASE_URL + path,
#             "track": track,
#             "paper_no": paper_no,
#         }
#         papers.append(current_paper)
#         continue

#     # ---------------- PERSON ----------------
#     if path.startswith("/people/") and current_paper is not None:
#         person_url = BASE_URL + path
#         people.append({"name": name, "url": person_url})

#         paper_author_edges.append({
#             "paper_id": current_paper["paper_id"],
#             "title": current_paper["title"],
#             "author": name,
#             "author_url": person_url
#         })
#         continue

# # ======================================================
# # DATAFRAMES
# # ======================================================

# papers_df = pd.DataFrame(papers)
# people_df = pd.DataFrame(people).drop_duplicates()
# edges_df = pd.DataFrame(paper_author_edges)

# # ======================================================
# # METRICS
# # ======================================================

# st.subheader("📈 Overview")

# c1, c2, c3 = st.columns(3)
# c1.metric("Papers", len(papers_df))
# c2.metric("Authors", len(people_df))
# c3.metric("Edges (Authorships)", len(edges_df))

# # ======================================================
# # PAPER DISTRIBUTION
# # ======================================================

# st.subheader("📊 Papers by Track")

# if not papers_df.empty:
#     track_counts = papers_df["track"].value_counts()

#     fig, ax = plt.subplots()
#     track_counts.plot(kind="bar", ax=ax)
#     ax.set_xlabel("Track")
#     ax.set_ylabel("Number of Papers")
#     ax.set_title("Paper Distribution by Track")
#     plt.xticks(rotation=45)

#     st.pyplot(fig)

# # ======================================================
# # TABLES
# # ======================================================

# with st.expander("📄 Papers Table"):
#     st.dataframe(papers_df.sort_values(["track", "paper_no"]), use_container_width=True)

# with st.expander("👥 Authors Table"):
#     st.dataframe(people_df, use_container_width=True)

# with st.expander("🔗 Paper–Author Edges"):
#     st.dataframe(edges_df, use_container_width=True)

# # ======================================================
# # CO-AUTHOR NETWORK
# # ======================================================

# st.subheader("🧠 Co-Author Network")

# coauthor = nx.Graph()

# for paper in edges_df["paper_id"].unique():
#     authors = edges_df[edges_df["paper_id"] == paper]["author"].tolist()
#     for i in range(len(authors)):
#         for j in range(i + 1, len(authors)):
#             if coauthor.has_edge(authors[i], authors[j]):
#                 coauthor[authors[i]][authors[j]]["weight"] += 1
#             else:
#                 coauthor.add_edge(authors[i], authors[j], weight=1)

# MAX_NODES = st.slider("Max authors to visualize", 20, 300, 80)

# top_authors = sorted(coauthor.degree, key=lambda x: x[1], reverse=True)[:MAX_NODES]
# nodes = [n for n, _ in top_authors]
# subG = coauthor.subgraph(nodes)

# fig2, ax2 = plt.subplots(figsize=(10, 8))
# pos = nx.spring_layout(subG, seed=42, k=0.4)

# nx.draw(
#     subG, pos,
#     ax=ax2,
#     node_size=80,
#     with_labels=False
# )

# ax2.set_title("Co-Author Collaboration Network")
# st.pyplot(fig2)

# # ======================================================
# # DOWNLOADS
# # ======================================================

# st.subheader("⬇️ Export for Graph / Neo4j")

# st.download_button(
#     "Download Papers CSV",
#     papers_df.to_csv(index=False).encode("utf-8"),
#     file_name="papers.csv",
#     mime="text/csv"
# )

# st.download_button(
#     "Download Authors CSV",
#     people_df.to_csv(index=False).encode("utf-8"),
#     file_name="authors.csv",
#     mime="text/csv"
# )

# st.download_button(
#     "Download Paper–Author Edges CSV",
#     edges_df.to_csv(index=False).encode("utf-8"),
#     file_name="paper_author_edges.csv",
#     mime="text/csv"
# )


# import streamlit as st
# import json
# import pandas as pd
# import matplotlib.pyplot as plt
# import networkx as nx
# from pathlib import Path
# import re

# # ======================================================
# # CONFIG
# # ======================================================

# st.set_page_config(page_title="ACL Research Landscape", layout="wide")
# st.title("📚 ACL / EMNLP Research Landscape Dashboard")

# DATA_PATH = Path("data/scrap_example/extracted.json")

# # ======================================================
# # LOAD
# # ======================================================

# if not DATA_PATH.exists():
#     st.error(f"File not found: {DATA_PATH}")
#     st.stop()

# with open(DATA_PATH, "r", encoding="utf-8") as f:
#     obj = json.load(f)

# links = obj.get("links", {})

# st.success(f"Loaded {len(links)} page links")

# # ======================================================
# # PATTERNS
# # ======================================================

# paper_pattern = re.compile(r"/20\d{2}\.([a-z0-9\-]+)\.(\d+)/")
# proc_pattern = re.compile(r"/20\d{2}\.([a-z0-9\-]+)\.0/")

# # ======================================================
# # PARSE IN PAGE ORDER (IMPORTANT)
# # ======================================================

# papers = []
# people = []
# paper_author_edges = []

# current_paper = None

# for name, url in links.items():

#     if not isinstance(url, str):
#         continue

#     # normalize
#     path = url.replace("https://aclanthology.org", "")

#     # ---------------- PROCEEDINGS ----------------
#     if proc_pattern.search(path):
#         continue

#     # ---------------- PAPER ----------------
#     m_paper = paper_pattern.search(path)
#     if m_paper:
#         track = m_paper.group(1)
#         paper_no = int(m_paper.group(2))
#         paper_id = f"{track}.{paper_no}"

#         current_paper = {
#             "paper_id": paper_id,
#             "title": name,
#             "url": path,
#             "track": track,
#             "paper_no": paper_no,
#         }
#         papers.append(current_paper)
#         continue

#     # ---------------- PERSON ----------------
#     if path.startswith("/people/") and current_paper is not None:
#         people.append({"name": name, "url": path})

#         paper_author_edges.append({
#             "paper_id": current_paper["paper_id"],
#             "title": current_paper["title"],
#             "author": name
#         })
#         continue

# # ======================================================
# # DATAFRAMES
# # ======================================================

# papers_df = pd.DataFrame(papers)
# people_df = pd.DataFrame(people).drop_duplicates()
# edges_df = pd.DataFrame(paper_author_edges)

# # ======================================================
# # METRICS
# # ======================================================

# st.subheader("📈 Overview")

# c1, c2, c3 = st.columns(3)
# c1.metric("Papers", len(papers_df))
# c2.metric("Authors", len(people_df))
# c3.metric("Edges (Authorships)", len(edges_df))

# # ======================================================
# # PAPER DISTRIBUTION
# # ======================================================

# st.subheader("📊 Papers by Track")

# if not papers_df.empty:
#     track_counts = papers_df["track"].value_counts()

#     fig, ax = plt.subplots()
#     track_counts.plot(kind="bar", ax=ax)
#     ax.set_xlabel("Track")
#     ax.set_ylabel("Number of Papers")
#     ax.set_title("Paper Distribution by Track")
#     plt.xticks(rotation=45)

#     st.pyplot(fig)

# # ======================================================
# # TABLES
# # ======================================================

# with st.expander("📄 Papers Table"):
#     st.dataframe(papers_df.sort_values(["track", "paper_no"]), use_container_width=True)

# with st.expander("👥 Authors Table"):
#     st.dataframe(people_df, use_container_width=True)

# with st.expander("🔗 Paper–Author Edges"):
#     st.dataframe(edges_df, use_container_width=True)

# # ======================================================
# # CO-AUTHOR NETWORK
# # ======================================================

# st.subheader("🧠 Co-Author Network")

# G = nx.Graph()

# for _, row in edges_df.iterrows():
#     G.add_node(row["author"], type="author")
#     G.add_node(row["paper_id"], type="paper")
#     G.add_edge(row["author"], row["paper_id"])

# # Project to co-author graph
# coauthor = nx.Graph()

# for paper in edges_df["paper_id"].unique():
#     authors = edges_df[edges_df["paper_id"] == paper]["author"].tolist()
#     for i in range(len(authors)):
#         for j in range(i + 1, len(authors)):
#             if coauthor.has_edge(authors[i], authors[j]):
#                 coauthor[authors[i]][authors[j]]["weight"] += 1
#             else:
#                 coauthor.add_edge(authors[i], authors[j], weight=1)

# # Limit graph size for display
# MAX_NODES = st.slider("Max authors to visualize", 20, 300, 80)

# top_authors = sorted(coauthor.degree, key=lambda x: x[1], reverse=True)[:MAX_NODES]
# nodes = [n for n, _ in top_authors]
# subG = coauthor.subgraph(nodes)

# fig2, ax2 = plt.subplots(figsize=(10, 8))
# pos = nx.spring_layout(subG, seed=42, k=0.4)

# nx.draw(
#     subG, pos,
#     ax=ax2,
#     node_size=80,
#     with_labels=False
# )

# ax2.set_title("Co-Author Collaboration Network")
# st.pyplot(fig2)

# # ======================================================
# # DOWNLOADS
# # ======================================================

# st.subheader("⬇️ Export for Graph / Neo4j")

# st.download_button(
#     "Download Papers CSV",
#     papers_df.to_csv(index=False).encode("utf-8"),
#     file_name="papers.csv",
#     mime="text/csv"
# )

# st.download_button(
#     "Download Authors CSV",
#     people_df.to_csv(index=False).encode("utf-8"),
#     file_name="authors.csv",
#     mime="text/csv"
# )

# st.download_button(
#     "Download Paper–Author Edges CSV",
#     edges_df.to_csv(index=False).encode("utf-8"),
#     file_name="paper_author_edges.csv",
#     mime="text/csv"
# )
