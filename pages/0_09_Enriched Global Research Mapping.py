# --------------------------------------------------
# Global ESG Research Mapping + CSV Enrichment
# SAFE fuzzy matching (row-based, no KeyError)
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

st.set_page_config(page_title="ESG Literature Map (Enriched)", layout="wide")
st.title("🔗 ESG Research Mapping — Enriched with CSV Database")

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
# PAPER DETAILS (ENRICHED)
# ================================

st.subheader("🔍 Paper Details")

titles = sorted(unique_filt["title"].dropna().unique().tolist())

if titles:
    selected_title = st.selectbox("Select a paper", titles)

    row = unique_filt[unique_filt["title"] == selected_title].iloc[0]
    paper = paper_lookup[row["paper_id"]]

    st.markdown(f"## {row['title']}")

    # ---- RQ LIST -----------------------

    st.markdown("### 🧠 Addressed Research Questions")
    for rq in row["rq"]:
        st.markdown(f"- {rq}")

    st.divider()

    # ---- META --------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Method Category(s)**")
        st.write(row["method"])

        st.markdown("**Decision Trace Support**")
        st.write(row["trace"])

        st.markdown("**Max Relevance Score**")
        st.write(row["relevance"])

    with col2:
        st.markdown("**Regulatory Relevance**")
        st.write(row["regulatory"])

    # ---- ABSTRACTS ---------------------

    st.markdown("### 📄 Abstract (Registry)")
    st.write(paper.get("input", {}).get("abstract", ""))

    if db_df is not None:

        query = norm(row["title"])

        best_score = 0
        best_row = None

        for _, r in db_df.iterrows():
            score = SequenceMatcher(None, query, r["title_norm"]).ratio()
            if score > best_score:
                best_score = score
                best_row = r

        if best_score >= 0.82 and best_row is not None:
            st.markdown("### 🗄 Abstract (Database CSV)")
            st.write(best_row.get("abstract", ""))

            st.markdown("**DOI (from database)**")
            st.write(best_row.get("doi"))

            st.caption(f"Matched with similarity score: {round(best_score, 3)}")

        else:
            st.warning("No close title match found in uploaded CSV database.")

            # Optional debug
            top = (
                db_df.assign(sim=db_df["title_norm"].apply(
                    lambda t: SequenceMatcher(None, query, t).ratio()))
                .sort_values("sim", ascending=False)
                .head(5)
            )

            st.markdown("#### 🔍 Closest title candidates")
            st.dataframe(top[["title", "sim"]], use_container_width=True)

    # ---- LINKS -------------------------

    st.markdown("### 🔗 External Links (Registry)")
    for l in paper.get("external_links", []):
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
# # Global ESG Research Mapping + CSV Enrichment
# # With FUZZY Title Matching
# # --------------------------------------------------

# import json
# from pathlib import Path
# import pandas as pd
# import streamlit as st
# import re
# from difflib import SequenceMatcher

# # ================================
# # CONFIG
# # ================================

# BASE_DIR = Path(__file__).parents[1]
# REGISTRY_PATH = BASE_DIR / "data" / "registry.json"

# st.set_page_config(page_title="ESG Literature Map (Enriched)", layout="wide")
# st.title("🔗 ESG Research Mapping — Enriched with CSV Database")

# # ================================
# # HELPERS
# # ================================

# def norm(text):
#     if not isinstance(text, str):
#         return ""
#     return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


# def fuzzy_match_title(query, candidates, threshold=0.82):
#     best = None
#     best_score = 0

#     for c in candidates:
#         score = SequenceMatcher(None, query, c).ratio()
#         if score > best_score:
#             best_score = score
#             best = c

#     if best_score >= threshold:
#         return best, best_score
#     return None, best_score


# # ================================
# # LOAD REGISTRY
# # ================================

# if not REGISTRY_PATH.exists():
#     st.error(f"registry.json not found at: {REGISTRY_PATH}")
#     st.stop()

# with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
#     registry = json.load(f)

# tracks = registry.get("research_tracks", [])

# # ================================
# # BUILD GLOBAL MAPPING
# # ================================

# rows = []
# paper_lookup = {}

# for ti, t in enumerate(tracks):
#     rq = t["meta"].get("research_question", f"RQ_{ti}")

#     for p in t.get("papers", []):
#         pid = p.get("id")
#         title = p.get("input", {}).get("title")

#         rows.append({
#             "rq": rq,
#             "paper_id": pid,
#             "title": title,
#             "title_norm": norm(title),
#             "method": p.get("method_category"),
#             "trace": p.get("decision_trace_support"),
#             "relevance": p.get("relevance_score", 0.0),
#             "regulatory": ", ".join(p.get("regulatory_relevance", [])),
#         })

#         paper_lookup[pid] = p

# df = pd.DataFrame(rows)

# # ================================
# # UNIQUE PAPERS (DEDUP)
# # ================================

# unique_df = (
#     df.groupby("title_norm")
#     .agg({
#         "title": "first",
#         "method": lambda x: ", ".join(sorted(set(x.dropna()))),
#         "trace": lambda x: ", ".join(sorted(set(x.dropna()))),
#         "relevance": "max",
#         "regulatory": lambda x: ", ".join(sorted(set(", ".join(x).split(", ")))),
#         "rq": lambda x: list(sorted(set(x))),
#         "paper_id": "first",
#     })
#     .reset_index(drop=True)
# )

# unique_df["rq_count"] = unique_df["rq"].apply(len)

# # ================================
# # CSV UPLOAD
# # ================================

# st.sidebar.header("📥 External Paper Database (CSV)")

# csv_file = st.sidebar.file_uploader(
#     "Upload CSV with title, doi, abstract",
#     type=["csv"]
# )

# db_df = None
# db_titles = []
# db_lookup = {}

# if csv_file:
#     try:
#         db_df = pd.read_csv(csv_file)

#         required = {"title", "doi", "abstract"}
#         if not required.issubset(set(db_df.columns)):
#             st.sidebar.error("CSV must contain: title, doi, abstract")
#             db_df = None
#         else:
#             db_df["title_norm"] = db_df["title"].apply(norm)
#             db_titles = db_df["title_norm"].tolist()
#             db_lookup = db_df.set_index("title_norm").to_dict("index")

#             st.sidebar.success(f"Loaded {len(db_df)} database records")

#     except Exception as e:
#         st.sidebar.error(f"CSV error: {e}")

# # ================================
# # FILTERS
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
# search = st.sidebar.text_input("Search title")

# # ================================
# # APPLY FILTERS
# # ================================

# unique_filt = unique_df[
#     (unique_df["method"].str.contains("|".join(method_filter), na=False))
#     & (unique_df["trace"].str.contains("|".join(trace_filter), na=False))
#     & (unique_df["relevance"] >= min_relevance)
# ]

# if search:
#     unique_filt = unique_filt[
#         unique_filt["title"].str.contains(search, case=False, na=False)
#     ]

# # ================================
# # TABLE
# # ================================

# st.subheader("📄 Unique Papers (Deduplicated)")

# st.dataframe(
#     unique_filt[["title", "rq_count", "method", "trace", "relevance", "regulatory"]]
#     .sort_values(["rq_count", "relevance"], ascending=[False, False]),
#     use_container_width=True,
# )

# # ================================
# # PAPER DETAILS (ENRICHED)
# # ================================

# st.subheader("🔍 Paper Details")

# titles = sorted(unique_filt["title"].dropna().unique().tolist())

# if titles:
#     selected_title = st.selectbox("Select a paper", titles)

#     row = unique_filt[unique_filt["title"] == selected_title].iloc[0]
#     paper = paper_lookup[row["paper_id"]]

#     st.markdown(f"## {row['title']}")

#     # ---- RQ LIST -----------------------

#     st.markdown("### 🧠 Addressed Research Questions")
#     for rq in row["rq"]:
#         st.markdown(f"- {rq}")

#     st.divider()

#     # ---- META --------------------------

#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("**Method Category(s)**")
#         st.write(row["method"])

#         st.markdown("**Decision Trace Support**")
#         st.write(row["trace"])

#         st.markdown("**Max Relevance Score**")
#         st.write(row["relevance"])

#     with col2:
#         st.markdown("**Regulatory Relevance**")
#         st.write(row["regulatory"])

#     # ---- ABSTRACTS ---------------------

#     st.markdown("### 📄 Abstract (Registry)")
#     st.write(paper.get("input", {}).get("abstract", ""))

#     if db_df is not None:
#         query = norm(row["title"])
#         match_key, score = fuzzy_match_title(query, db_titles, threshold=0.82)

#         if match_key:
#             db_hit = db_lookup[match_key]

#             st.markdown("### 🗄 Abstract (Database CSV)")
#             st.write(db_hit.get("abstract", ""))

#             st.markdown("**DOI (from database)**")
#             st.write(db_hit.get("doi"))

#             st.caption(f"Matched with similarity score: {round(score, 3)}")

#         else:
#             st.warning("No close title match found in uploaded CSV database.")

#     # ---- LINKS -------------------------

#     st.markdown("### 🔗 External Links (Registry)")
#     for l in paper.get("external_links", []):
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


# # --------------------------------------------------
# # Global ESG Research Mapping + CSV Enrichment
# # --------------------------------------------------

# import json
# from pathlib import Path
# import pandas as pd
# import streamlit as st
# import re

# # ================================
# # CONFIG
# # ================================

# BASE_DIR = Path(__file__).parents[1]
# REGISTRY_PATH = BASE_DIR / "data" / "registry.json"

# st.set_page_config(page_title="ESG Literature Map (Enriched)", layout="wide")
# st.title("🔗 ESG Research Mapping — Enriched with CSV Database")

# # ================================
# # HELPERS
# # ================================

# def norm(text):
#     if not isinstance(text, str):
#         return ""
#     return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

# # ================================
# # LOAD REGISTRY
# # ================================

# if not REGISTRY_PATH.exists():
#     st.error(f"registry.json not found at: {REGISTRY_PATH}")
#     st.stop()

# with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
#     registry = json.load(f)

# tracks = registry.get("research_tracks", [])

# # ================================
# # BUILD GLOBAL MAPPING
# # ================================

# rows = []
# paper_lookup = {}

# for ti, t in enumerate(tracks):
#     rq = t["meta"].get("research_question", f"RQ_{ti}")

#     for p in t.get("papers", []):
#         pid = p.get("id")
#         title = p.get("input", {}).get("title")

#         rows.append({
#             "rq": rq,
#             "paper_id": pid,
#             "title": title,
#             "title_norm": norm(title),
#             "method": p.get("method_category"),
#             "trace": p.get("decision_trace_support"),
#             "relevance": p.get("relevance_score", 0.0),
#             "regulatory": ", ".join(p.get("regulatory_relevance", [])),
#         })

#         paper_lookup[pid] = p

# df = pd.DataFrame(rows)

# # ================================
# # UNIQUE PAPERS (MERGED)
# # ================================

# unique_df = (
#     df.groupby("title_norm")
#     .agg({
#         "title": "first",
#         "method": lambda x: ", ".join(sorted(set(x.dropna()))),
#         "trace": lambda x: ", ".join(sorted(set(x.dropna()))),
#         "relevance": "max",
#         "regulatory": lambda x: ", ".join(sorted(set(", ".join(x).split(", ")))),
#         "rq": lambda x: list(sorted(set(x))),
#         "paper_id": "first",
#     })
#     .reset_index()
# )

# unique_df["rq_count"] = unique_df["rq"].apply(len)

# # ================================
# # CSV UPLOAD (DATABASE)
# # ================================

# st.sidebar.header("📥 External Paper Database (CSV)")

# csv_file = st.sidebar.file_uploader(
#     "Upload CSV with title, doi, abstract",
#     type=["csv"]
# )

# db_df = None
# db_lookup = {}

# if csv_file:
#     try:
#         db_df = pd.read_csv(csv_file)

#         required = {"title", "doi", "abstract"}
#         if not required.issubset(set(db_df.columns)):
#             st.sidebar.error("CSV must contain: title, doi, abstract")
#             db_df = None
#         else:
#             db_df["title_norm"] = db_df["title"].apply(norm)
#             db_lookup = db_df.set_index("title_norm").to_dict("index")

#             st.sidebar.success(f"Loaded {len(db_df)} database records")

#     except Exception as e:
#         st.sidebar.error(f"CSV error: {e}")

# # ================================
# # FILTERS
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
# search = st.sidebar.text_input("Search title")

# # ================================
# # APPLY FILTERS
# # ================================

# filt_df = df[
#     (df["rq"].isin(rq_filter))
#     & (df["method"].isin(method_filter))
#     & (df["trace"].isin(trace_filter))
#     & (df["relevance"] >= min_relevance)
# ]

# if search:
#     filt_df = filt_df[filt_df["title"].str.contains(search, case=False, na=False)]

# unique_filt = unique_df[
#     (unique_df["method"].str.contains("|".join(method_filter), na=False))
#     & (unique_df["trace"].str.contains("|".join(trace_filter), na=False))
#     & (unique_df["relevance"] >= min_relevance)
# ]

# if search:
#     unique_filt = unique_filt[
#         unique_filt["title"].str.contains(search, case=False, na=False)
#     ]

# # ================================
# # TABLE
# # ================================

# st.subheader("📄 Unique Papers (Deduplicated)")

# st.dataframe(
#     unique_filt[["title", "rq_count", "method", "trace", "relevance", "regulatory"]]
#     .sort_values(["rq_count", "relevance"], ascending=[False, False]),
#     use_container_width=True,
# )

# # ================================
# # PAPER DETAILS (ENRICHED)
# # ================================

# st.subheader("🔍 Paper Details")

# titles = sorted(unique_filt["title"].dropna().unique().tolist())

# if titles:
#     selected_title = st.selectbox("Select a paper", titles)

#     row = unique_filt[unique_filt["title"] == selected_title].iloc[0]
#     paper = paper_lookup[row["paper_id"]]

#     st.markdown(f"## {row['title']}")

#     # ---- RQ LIST -----------------------

#     st.markdown("### 🧠 Addressed Research Questions")
#     for rq in row["rq"]:
#         st.markdown(f"- {rq}")

#     st.divider()

#     # ---- META --------------------------

#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("**Method Category(s)**")
#         st.write(row["method"])

#         st.markdown("**Decision Trace Support**")
#         st.write(row["trace"])

#         st.markdown("**Max Relevance Score**")
#         st.write(row["relevance"])

#     with col2:
#         st.markdown("**Regulatory Relevance**")
#         st.write(row["regulatory"])

#     # ---- ABSTRACTS ---------------------

#     st.markdown("### 📄 Abstract (Registry)")
#     st.write(paper.get("input", {}).get("abstract", ""))

#     if db_df is not None:
#         key = norm(row["title"])
#         db_hit = db_lookup.get(key)

#         if db_hit:
#             st.markdown("### 🗄 Abstract (Database CSV)")
#             st.write(db_hit.get("abstract", ""))

#             st.markdown("**DOI (from database)**")
#             st.write(db_hit.get("doi"))
#         else:
#             st.warning("No title match found in uploaded CSV database.")

#     # ---- LINKS -------------------------

#     st.markdown("### 🔗 External Links (Registry)")
#     for l in paper.get("external_links", []):
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
