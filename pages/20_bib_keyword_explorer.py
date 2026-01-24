import streamlit as st
import pandas as pd
import json
import bibtexparser
from pathlib import Path
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer

# ======================================
# CONFIG
# ======================================
BASE_DIR = Path(__file__).parents[1]

BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"
OUTPUT_DIR = BASE_DIR / "outputs" / "bib_keyword_logs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(layout="wide")
st.title("📚 Global BibTeX Keyword Explorer")

# ======================================
# LOAD ALL BIB FILES
# ======================================
@st.cache_data
def load_all_bib_files():
    entries = []
    source_map = {}

    bib_files = sorted(BIB_DIR.glob("*.bib"))
    for bib_path in bib_files:
        try:
            with open(bib_path) as f:
                db = bibtexparser.load(f)
                for e in db.entries:
                    e["_source_file"] = bib_path.name
                    entries.append(e)
                    source_map.setdefault(bib_path.name, 0)
                    source_map[bib_path.name] += 1
        except Exception as e:
            st.warning(f"Failed to load {bib_path.name}: {e}")

    # ----------------------------------
    # De-duplicate by (title + year)
    # ----------------------------------
    unique = {}
    for e in entries:
        key = (e.get("title", "").lower().strip(),
               e.get("year", ""))
        if key not in unique:
            unique[key] = e

    return list(unique.values()), source_map, bib_files


bib_entries, source_stats, bib_files = load_all_bib_files()

st.success(
    f"Loaded {len(bib_entries)} unique entries "
    f"from {len(bib_files)} BibTeX files."
)

# ======================================
# SOURCE FILE STATS
# ======================================
with st.expander("📂 Source File Statistics"):
    df_sources = pd.DataFrame([
        {"file": k, "entries": v}
        for k, v in source_stats.items()
    ]).sort_values("entries", ascending=False)

    st.dataframe(df_sources, use_container_width=True)

# ======================================
# PREVIEW
# ======================================
df = pd.DataFrame([
    {
        "id": e.get("ID"),
        "title": e.get("title"),
        "year": e.get("year"),
        "author": e.get("author"),
        "source": e.get("_source_file"),
        "abstract": (e.get("abstract") or "")[:200]
    }
    for e in bib_entries
])

st.subheader("📄 Combined Corpus Preview")
st.dataframe(df.head(500), use_container_width=True)

# ======================================
# TEXT EXTRACTION
# ======================================
def extract_docs(entries):
    return [
        f"{e.get('title','')} {e.get('abstract','')}"
        for e in entries
    ]

docs = extract_docs(bib_entries)

# ======================================
# KEYWORD EXTRACTION
# ======================================
st.divider()
st.subheader("🔎 Global Keyword Extraction")

top_n = st.slider("Top N Keywords", 20, 200, 50)

@st.cache_data
def extract_keywords(docs, top_n):
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=3000
    )
    X = vectorizer.fit_transform(docs)
    scores = X.sum(axis=0).A1
    terms = vectorizer.get_feature_names_out()

    df = pd.DataFrame({
        "keyword": terms,
        "score": scores
    }).sort_values("score", ascending=False)

    return df.head(top_n)


keywords_df = extract_keywords(docs, top_n)
st.dataframe(keywords_df, use_container_width=True)

csv_path = OUTPUT_DIR / "global_keywords.csv"
keywords_df.to_csv(csv_path, index=False)
st.caption(f"Saved → {csv_path}")

# ======================================
# SEARCH
# ======================================
st.divider()
st.subheader("🎯 Search Across All Papers")

query = st.text_input("Enter keyword(s)", placeholder="graph neural network")

matches = []

if query:
    q = query.lower()
    for e in bib_entries:
        blob = f"{e.get('title','')} {e.get('abstract','')}".lower()
        if q in blob:
            matches.append(e)

    st.success(f"Matched {len(matches)} papers")

    match_df = pd.DataFrame([
        {
            "id": e.get("ID"),
            "title": e.get("title"),
            "year": e.get("year"),
            "source": e.get("_source_file")
        }
        for e in matches
    ])

    st.dataframe(match_df, use_container_width=True)

# ======================================
# SAVE LOGS
# ======================================
st.divider()
st.subheader("💾 Save Search Logs")

def save_log(payload):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"search_log_{ts}.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


def save_bib(entries):
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = entries
    writer = bibtexparser.bwriter.BibTexWriter()

    path = OUTPUT_DIR / "matched_entries.bib"
    with open(path, "w") as f:
        f.write(writer.write(db))
    return path


if st.button("Save Log + Export Matched Bib"):
    payload = {
        "timestamp": datetime.now().isoformat(),
        "bib_folder": str(BIB_DIR),
        "files_loaded": [p.name for p in bib_files],
        "total_entries": len(bib_entries),
        "query": query,
        "matched_count": len(matches),
        "top_keywords": keywords_df.head(30).to_dict(orient="records")
    }

    log_path = save_log(payload)
    bib_path = save_bib(matches) if matches else None

    st.success("Saved successfully ✅")
    st.write("📄 Log:", log_path)
    if bib_path:
        st.write("📚 Matched Bib:", bib_path)



# import streamlit as st
# import pandas as pd
# import json
# import bibtexparser
# from pathlib import Path
# from datetime import datetime
# from sklearn.feature_extraction.text import TfidfVectorizer

# # ======================================
# # CONFIG
# # ======================================
# BASE_DIR = Path(__file__).parents[1]

# BIB_DIR = BASE_DIR / "data" / "acl_anthology_new"
# OUTPUT_DIR = BASE_DIR / "outputs" / "bib_keyword_logs"

# OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# st.set_page_config(layout="wide")
# st.title("📚 BibTeX Keyword Explorer & Logger")

# # ======================================
# # UTILS
# # ======================================
# def load_bib_file(path: Path):
#     with open(path) as bibtex_file:
#         bib_database = bibtexparser.load(bibtex_file)
#     return bib_database.entries


# def extract_text(entries):
#     docs = []
#     for e in entries:
#         title = e.get("title", "")
#         abstract = e.get("abstract", "")
#         docs.append(f"{title} {abstract}")
#     return docs


# def extract_keywords_tfidf(docs, top_n=30):
#     if not docs:
#         return pd.DataFrame()

#     vectorizer = TfidfVectorizer(
#         stop_words="english",
#         max_features=1000,
#         ngram_range=(1, 2)
#     )
#     X = vectorizer.fit_transform(docs)
#     scores = X.sum(axis=0).A1
#     terms = vectorizer.get_feature_names_out()

#     df = pd.DataFrame({
#         "keyword": terms,
#         "score": scores
#     }).sort_values("score", ascending=False)

#     return df.head(top_n)


# def save_log(payload):
#     ts = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = OUTPUT_DIR / f"search_log_{ts}.json"
#     with open(path, "w") as f:
#         json.dump(payload, f, indent=2)
#     return path


# def save_bib(entries, filename="matched_entries.bib"):
#     db = bibtexparser.bibdatabase.BibDatabase()
#     db.entries = entries
#     writer = bibtexparser.bwriter.BibTexWriter()

#     path = OUTPUT_DIR / filename
#     with open(path, "w") as f:
#         f.write(writer.write(db))
#     return path


# # ======================================
# # FILE SELECTION
# # ======================================
# st.sidebar.header("📂 Bib File Source")

# mode = st.sidebar.radio("Select source", ["Browse Folder", "Upload File"])

# bib_entries = []

# if mode == "Browse Folder":
#     bib_files = sorted(BIB_DIR.glob("*.bib"))
#     selected = st.sidebar.selectbox(
#         "Select BibTeX file",
#         bib_files,
#         format_func=lambda p: p.name if p else ""
#     )

#     if selected:
#         bib_entries = load_bib_file(selected)
#         st.success(f"Loaded: {selected.name} ({len(bib_entries)} entries)")

# elif mode == "Upload File":
#     uploaded = st.sidebar.file_uploader("Upload .bib file", type=["bib"])
#     if uploaded:
#         bib_db = bibtexparser.loads(uploaded.read().decode("utf-8"))
#         bib_entries = bib_db.entries
#         st.success(f"Uploaded: {uploaded.name} ({len(bib_entries)} entries)")


# if not bib_entries:
#     st.warning("Please load a BibTeX file.")
#     st.stop()

# # ======================================
# # DATAFRAME PREVIEW
# # ======================================
# df = pd.DataFrame([
#     {
#         "id": e.get("ID"),
#         "title": e.get("title"),
#         "year": e.get("year"),
#         "author": e.get("author"),
#         "abstract": e.get("abstract", "")[:300]
#     }
#     for e in bib_entries
# ])

# st.subheader("📄 Bib Entries Preview")
# st.dataframe(df, use_container_width=True)

# # ======================================
# # KEYWORD EXTRACTION
# # ======================================
# st.divider()
# st.subheader("🔎 Automatic Keyword Extraction")

# docs = extract_text(bib_entries)

# top_n = st.slider("Top N Keywords", 10, 100, 30)

# keywords_df = extract_keywords_tfidf(docs, top_n)

# st.dataframe(keywords_df, use_container_width=True)

# if not keywords_df.empty:
#     csv_path = OUTPUT_DIR / "extracted_keywords.csv"
#     keywords_df.to_csv(csv_path, index=False)
#     st.caption(f"Saved keyword table → {csv_path}")

# # ======================================
# # MANUAL SEARCH
# # ======================================
# st.divider()
# st.subheader("🎯 Keyword Search in Bib Entries")

# query = st.text_input("Enter keyword(s)", placeholder="graph neural network")

# matches = []

# if query:
#     q = query.lower()
#     for e in bib_entries:
#         blob = f"{e.get('title','')} {e.get('abstract','')}".lower()
#         if q in blob:
#             matches.append(e)

#     st.success(f"Found {len(matches)} matching entries")

#     match_df = pd.DataFrame([
#         {
#             "id": e.get("ID"),
#             "title": e.get("title"),
#             "year": e.get("year"),
#         }
#         for e in matches
#     ])
#     st.dataframe(match_df, use_container_width=True)

# # ======================================
# # SAVE LOGS
# # ======================================
# st.divider()
# st.subheader("💾 Save Search Logs")

# if st.button("Save Log + Matched Bib"):
#     payload = {
#         "timestamp": datetime.now().isoformat(),
#         "source_mode": mode,
#         "total_entries": len(bib_entries),
#         "query": query,
#         "matched_count": len(matches),
#         "top_keywords": keywords_df.head(20).to_dict(orient="records")
#     }

#     log_path = save_log(payload)

#     bib_path = None
#     if matches:
#         bib_path = save_bib(matches)

#     st.success("Saved successfully ✅")
#     st.write("📄 Log file:", log_path)
#     if bib_path:
#         st.write("📚 Matched Bib:", bib_path)
