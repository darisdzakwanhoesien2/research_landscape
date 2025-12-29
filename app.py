import streamlit as st
import pandas as pd

from pipeline.loader import load_papers
from pipeline.cleaner import (
    normalize_columns,
    clean_abstracts,
    clean_keywords,
    infer_source_type,
    filter_nonempty_keywords,
)
from pipeline.cooccurrence import build_cooccurrence_graph
from viz.wordclouds import plot_wordcloud
from viz.network import build_interactive_graph
from viz.timeline import plot_keyword_trend

# -----------------------------
# Keyword fallback (TF-IDF)
# -----------------------------
from sklearn.feature_extraction.text import TfidfVectorizer


def generate_fallback_keywords(df, top_k=5):
    texts = (
        df["title"].fillna("") + " " + df["abstract"].fillna("")
    ).tolist()

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=1000,
        ngram_range=(1, 2)
    )

    X = vectorizer.fit_transform(texts)
    terms = vectorizer.get_feature_names_out()

    keywords = []
    for row in X:
        if row.nnz == 0:
            keywords.append([])
        else:
            idx = row.toarray()[0].argsort()[-top_k:]
            keywords.append([terms[i] for i in idx])

    return keywords


# -----------------------------
# Streamlit config
# -----------------------------
st.set_page_config(layout="wide")
st.title("📚 Conference & Journal Knowledge Landscape")

# -----------------------------
# File upload
# -----------------------------
uploaded = st.file_uploader(
    "Upload paper metadata (CSV / JSON)",
    type=["csv", "json"]
)

if not uploaded:
    st.info("Upload a CSV or JSON file to begin.")
    st.stop()

# -----------------------------
# Load & preprocess
# -----------------------------
df = load_papers(uploaded)
df = normalize_columns(df)
df = clean_abstracts(df)
df = clean_keywords(df)
df = infer_source_type(df)

# -----------------------------
# Keyword fallback (critical)
# -----------------------------
if df["keywords"].apply(len).sum() == 0:
    st.info(
        "No author keywords found. "
        "Generating keywords automatically from titles and abstracts."
    )
    df["keywords"] = generate_fallback_keywords(df)

st.success(f"Loaded {len(df)} papers")

# -----------------------------
# Sidebar filters + inspection
# -----------------------------
with st.sidebar:
    st.header("Filters")

    source_types = sorted(df["source_type"].dropna().unique())
    selected_sources = st.multiselect(
        "Source Type",
        source_types,
        default=source_types
    )

    year_min, year_max = int(df.year.min()), int(df.year.max())
    year_range = st.slider(
        "Year Range",
        year_min,
        year_max,
        (year_min, year_max)
    )

    st.divider()
    st.header("Debug / Inspection")
    debug_mode = st.checkbox("Enable inspection mode", value=False)

# -----------------------------
# Apply filters
# -----------------------------
df_f = df[
    (df["source_type"].isin(selected_sources)) &
    (df["year"].between(*year_range))
]

st.caption(f"Filtered papers: {len(df_f)}")

# ======================================================
# 🔍 INSPECTION MODE
# ======================================================
if debug_mode:
    st.subheader("🧪 Filtered Data Preview")
    st.dataframe(df_f.head(20))

    st.subheader("📊 Diagnostics")
    diagnostics = {
        "total_rows": len(df_f),
        "rows_with_keywords": df_f["keywords"].apply(len).gt(0).sum(),
        "unique_keywords": len({k for kws in df_f["keywords"] for k in kws}),
        "non_empty_abstracts": (df_f["abstract"].str.len() > 0).sum(),
        "source_type_counts": df_f["source_type"].value_counts().to_dict(),
    }
    st.json(diagnostics)

# ======================================================
# ☁️ WORD CLOUD
# ======================================================
st.subheader("☁️ Keyword Word Cloud")

df_wc = filter_nonempty_keywords(df_f)
fig_wc = plot_wordcloud(df_wc)

if fig_wc is None:
    st.warning(
        "No keywords available for word cloud under current filters.\n\n"
        "Try expanding the year range or including more source types."
    )
else:
    st.pyplot(fig_wc)

# ======================================================
# 🧠 KNOWLEDGE GRAPH
# ======================================================
st.subheader("🧠 Keyword Co-Occurrence Knowledge Graph")

df_graph = filter_nonempty_keywords(df_f)

if len(df_graph) == 0:
    st.warning("No keyword data available to build a co-occurrence graph.")
else:
    G = build_cooccurrence_graph(df_graph)

    if G.number_of_nodes() == 0:
        st.warning("Keyword graph is empty after frequency filtering.")
    else:
        net = build_interactive_graph(G)
        net.save_graph("kg.html")

        with open("kg.html", "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=750)

# ======================================================
# ⏳ TEMPORAL ANALYSIS
# ======================================================
st.subheader("⏳ Keyword Evolution Over Time")

all_keywords = sorted({
    k
    for kws in df_f["keywords"]
    if isinstance(kws, list)
    for k in kws
})

if not all_keywords:
    st.warning("No keywords available for temporal analysis.")
else:
    keyword = st.selectbox("Select keyword", all_keywords)
    fig_trend = plot_keyword_trend(df_f, keyword)
    st.pyplot(fig_trend)


# import streamlit as st
# from pathlib import Path

# from pipeline.loader import load_papers
# from pipeline.cleaner import clean_keywords, normalize_columns, clean_abstracts, infer_source_type, filter_nonempty_keywords
# from pipeline.cooccurrence import build_cooccurrence_graph
# from viz.wordclouds import plot_wordcloud
# from viz.network import build_interactive_graph
# from viz.timeline import plot_keyword_trend

# st.set_page_config(layout="wide")
# st.title("📚 Conference & Journal Knowledge Landscape")

# uploaded = st.file_uploader("Upload paper metadata (CSV / JSON)", type=["csv", "json"])

# if uploaded:
#     # df = load_papers(Path(uploaded.name))
#     df = load_papers(uploaded)
#     df = normalize_columns(df)
#     df = clean_abstracts(df)
#     df = clean_keywords(df)
#     df = infer_source_type(df)

#     st.success(f"Loaded {len(df)} papers")

#     # ---- Filters ----
#     with st.sidebar:
#         source = st.multiselect(
#             "Source Type",
#             df["source_type"].unique(),
#             default=df["source_type"].unique()
#         )
#         year_range = st.slider(
#             "Year Range",
#             int(df.year.min()),
#             int(df.year.max()),
#             (int(df.year.min()), int(df.year.max()))
#         )

#     df_f = df[
#         (df.source_type.isin(source)) &
#         (df.year.between(*year_range))
#     ]

#     # ---- Word Cloud ----
#     st.subheader("☁️ Keyword Word Cloud")
#     st.pyplot(plot_wordcloud(df_f))

#     # ---- Knowledge Graph ----
#     st.subheader("🧠 Keyword Co-Occurrence Knowledge Graph")
#     G = build_cooccurrence_graph(df_f)
#     net = build_interactive_graph(G)
#     net.save_graph("kg.html")
#     st.components.v1.html(open("kg.html").read(), height=750)

#     # ---- Temporal Analysis ----
#     st.subheader("⏳ Keyword Evolution")
#     keyword = st.selectbox("Select keyword", sorted({k for kws in df_f.keywords for k in kws}))
#     st.pyplot(plot_keyword_trend(df_f, keyword))