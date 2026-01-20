import streamlit as st
import pandas as pd
import json
from pathlib import Path
from rapidfuzz import fuzz
import hashlib

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📚 Literature Category Mapper",
    layout="wide"
)

st.title("📚 Literature Category Mapper")
st.caption("Map paper titles / abstracts into categories using JSON mapping")

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MAPPING_FILE = DATA_DIR / "mapping.json"

REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
CSV_DIR = BASE_DIR / "data" / "csv"

REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# SAFETY CHECK — mapping.json must exist
# =========================================================

if not MAPPING_FILE.exists():
    st.error(
        f"❌ mapping.json not found at:\n{MAPPING_FILE}\n\n"
        "Please create it first."
    )
    st.stop()

# =========================================================
# UTILITIES
# =========================================================

def normalize(text: str) -> str:
    return str(text).lower().strip()


def load_mapping() -> dict:
    try:
        return json.loads(MAPPING_FILE.read_text())
    except Exception as e:
        st.error(f"Failed to load mapping.json: {e}")
        st.stop()


def save_mapping(mapping: dict):
    MAPPING_FILE.write_text(json.dumps(mapping, indent=2))


def classify_text(text: str, mapping: dict, threshold=60):
    text_norm = normalize(text)

    best_score = 0
    best_category = "Uncategorized"
    matched_keywords = []

    for category, keywords in mapping.items():
        for kw in keywords:
            score = fuzz.partial_ratio(text_norm, kw.lower())
            if score > best_score and score >= threshold:
                best_score = score
                best_category = category
                matched_keywords = [kw]

    return best_category, ", ".join(matched_keywords), best_score


def batch_classify(records, mapping):
    rows = []
    for r in records:
        cat, kws, score = classify_text(r["text"], mapping)
        rows.append({
            "source_title": r.get("title", ""),
            "source_abstract": r.get("abstract", ""),
            "input_text_preview": r["text"][:200],
            "predicted_category": cat,
            "matched_keywords": kws,
            "confidence": score
        })
    return pd.DataFrame(rows)


def directory_fingerprint(path: Path) -> str:
    parts = []
    for p in sorted(path.glob("*")):
        if p.is_file():
            stat = p.stat()
            parts.append(f"{p.name}:{stat.st_mtime_ns}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


# =========================================================
# LOAD UNIQUE MATCHED REFERENCES (TITLE + ABSTRACT)
# =========================================================

@st.cache_data(show_spinner=False)
def load_unique_matched(_json_fp: str, _csv_fp: str):

    def normalize_text(x):
        return str(x).strip().lower()

    # ---------------- JSON ----------------
    rows = []
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        root = data.get("research_plan_references", {})
        if not isinstance(root, dict):
            continue

        for layer in root.values():
            for ref in layer.get("literature_references", []):
                rows.append({
                    "json_title": ref.get("title", ""),
                    "json_abstract": ref.get("abstract", "")
                })

    json_df = pd.DataFrame(rows)
    if json_df.empty:
        return pd.DataFrame()

    json_df["title_norm"] = json_df["json_title"].map(normalize_text)

    # ---------------- CSV ----------------
    frames = []
    for path in sorted(CSV_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(path)
            frames.append(df)
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    csv_df = pd.concat(frames, ignore_index=True)
    csv_df.columns = csv_df.columns.str.strip()

    if "Title" not in csv_df.columns:
        return pd.DataFrame()

    csv_df["title_norm"] = csv_df["Title"].map(normalize_text)

    abstract_col = next(
        (c for c in ["Abstract", "abstract", "Summary", "summary"] if c in csv_df.columns),
        None
    )

    # ---------------- MATCH ----------------
    merged = json_df.merge(
        csv_df,
        on="title_norm",
        how="left"
    )

    matched = merged[merged["Title"].notna()]

    unique = matched.drop_duplicates(subset="title_norm")

    if abstract_col:
        unique["csv_abstract"] = unique[abstract_col]
    else:
        unique["csv_abstract"] = ""

    return unique


json_fp = directory_fingerprint(REGISTRY_DIR)
csv_fp = directory_fingerprint(CSV_DIR)

unique_matched = load_unique_matched(json_fp, csv_fp)

# =========================================================
# LOAD MAPPING
# =========================================================

mapping = load_mapping()

# =========================================================
# SIDEBAR — EDIT MAPPING.JSON
# =========================================================

st.sidebar.header("🛠 Category Mapping (mapping.json)")

selected_category = st.sidebar.selectbox(
    "Select category",
    list(mapping.keys()),
    key="category_selector"
)

keywords_text = st.sidebar.text_area(
    "Keywords (comma separated)",
    value=", ".join(mapping[selected_category]),
    height=160,
    key="keyword_editor"
)

if st.sidebar.button("💾 Save Keywords", key="save_keywords_btn"):
    mapping[selected_category] = [
        k.strip() for k in keywords_text.split(",") if k.strip()
    ]
    save_mapping(mapping)
    st.sidebar.success("Saved to mapping.json")

st.sidebar.divider()

new_category = st.sidebar.text_input("➕ New Category Name", key="new_category_input")

if st.sidebar.button("Add Category", key="add_category_btn"):
    if new_category and new_category not in mapping:
        mapping[new_category] = []
        save_mapping(mapping)
        st.sidebar.success(f"Added {new_category}")
        st.rerun()
    else:
        st.sidebar.warning("Invalid or existing category")

# =========================================================
# INPUT SOURCE
# =========================================================

st.header("📥 Input Source")

input_mode = st.radio(
    "Select Input Mode",
    [
        "✍️ Paste Text",
        "📂 Upload CSV",
        "🔗 Use Unique Matched References"
    ],
    horizontal=True,
    key="input_mode_selector"
)

records = []

# ---------------- Paste ----------------
if input_mode == "✍️ Paste Text":
    input_text = st.text_area(
        "Paste text (one record per line)",
        height=220
    )

    if input_text.strip():
        records = [
            {"title": "", "abstract": "", "text": line.strip()}
            for line in input_text.split("\n")
            if line.strip()
        ]

# ---------------- CSV ----------------
elif input_mode == "📂 Upload CSV":
    uploaded_file = st.file_uploader(
        "Upload CSV (title / abstract supported)",
        type=["csv"]
    )

    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)

        title_col = next((c for c in ["title", "Title"] if c in df_upload.columns), None)
        abstract_col = next((c for c in ["abstract", "Abstract", "summary"] if c in df_upload.columns), None)

        if not title_col and not abstract_col:
            st.error("CSV must contain at least one column: title or abstract")
        else:
            for _, row in df_upload.iterrows():
                text = " ".join([
                    str(row.get(title_col, "")),
                    str(row.get(abstract_col, ""))
                ]).strip()

                records.append({
                    "title": row.get(title_col, ""),
                    "abstract": row.get(abstract_col, ""),
                    "text": text
                })

# ---------------- Unique Matched ----------------
elif input_mode == "🔗 Use Unique Matched References":

    if unique_matched.empty:
        st.warning("No unique matched references available.")
    else:
        st.success(f"Loaded {len(unique_matched)} unique references")

        preview_cols = [c for c in [
            "json_title", "json_abstract", "Title", "csv_abstract", "Journal", "Year"
        ] if c in unique_matched.columns]

        st.dataframe(
            unique_matched[preview_cols].head(25),
            use_container_width=True,
            height=260
        )

        content_mode = st.radio(
            "Select content for classification",
            [
                "🏷 Title Only",
                "📄 Abstract Only",
                "🔗 Title + Abstract"
            ],
            horizontal=True
        )

        for _, row in unique_matched.iterrows():

            title = row.get("json_title") or row.get("Title") or ""
            abstract = row.get("json_abstract") or row.get("csv_abstract") or ""

            if content_mode == "🏷 Title Only":
                text = title
            elif content_mode == "📄 Abstract Only":
                text = abstract
            else:
                text = f"{title}. {abstract}"

            if text.strip():
                records.append({
                    "title": title,
                    "abstract": abstract,
                    "text": text
                })

# =========================================================
# CLASSIFICATION
# =========================================================

run_btn = st.button("🚀 Classify", key="classify_btn")

if run_btn and records:

    result_df = batch_classify(records, mapping)

    st.success(f"Classified {len(result_df)} records")
    st.dataframe(result_df, use_container_width=True)

    st.subheader("✍️ Manual Override")

    edited_df = st.data_editor(
        result_df,
        num_rows="dynamic",
        use_container_width=True
    )

    st.subheader("📤 Export")

    csv_data = edited_df.to_csv(index=False).encode("utf-8")
    json_data = edited_df.to_json(orient="records", indent=2).encode("utf-8")

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "⬇️ Download CSV",
            csv_data,
            file_name="literature_mapping.csv",
            mime="text/csv"
        )

    with c2:
        st.download_button(
            "⬇️ Download JSON",
            json_data,
            file_name="literature_mapping.json",
            mime="application/json"
        )

elif run_btn:
    st.warning("Please provide at least one record to classify.")


# import streamlit as st
# import pandas as pd
# import json
# from pathlib import Path
# from rapidfuzz import fuzz
# import hashlib

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📚 Literature Category Mapper",
#     layout="wide"
# )

# st.title("📚 Literature Category Mapper")
# st.caption("Map paper titles / abstracts into categories (RAG, Aspect, ESG, etc.)")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# DATA_DIR = BASE_DIR / "data"
# DATA_DIR.mkdir(exist_ok=True)

# MAPPING_FILE = DATA_DIR / "category_mapping.json"

# REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
# CSV_DIR = BASE_DIR / "data" / "csv"

# REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
# CSV_DIR.mkdir(parents=True, exist_ok=True)

# # =========================================================
# # DEFAULT CATEGORY BOOTSTRAP (WRITTEN TO JSON ONCE)
# # =========================================================

# DEFAULT_MAPPING = {
#     "RAG": [
#         "retrieval",
#         "rag",
#         "retrieval-augmented",
#         "knowledge graph",
#         "reranking",
#         "question answering",
#         "pdf",
#         "document"
#     ],
#     "Aspect": [
#         "aspect",
#         "sentiment",
#         "absa",
#         "opinion",
#         "emotion",
#         "quadruple",
#         "triplet"
#     ],
#     "ESG": [
#         "esg",
#         "sustainability",
#         "environmental",
#         "governance",
#         "finance",
#         "investment",
#         "carbon",
#         "climate"
#     ],
#     "Evaluation": [
#         "benchmark",
#         "evaluation",
#         "leaderboard",
#         "dataset",
#         "metric"
#     ],
#     "Reasoning": [
#         "reasoning",
#         "chain-of-thought",
#         "planning",
#         "symbolic",
#         "logic",
#         "multi-agent",
#         "agent"
#     ],
#     "Multilingual": [
#         "multilingual",
#         "cross-lingual",
#         "translation",
#         "indonesian",
#         "language",
#         "low-resource"
#     ],
#     "Safety": [
#         "hallucination",
#         "alignment",
#         "safety",
#         "bias",
#         "truthfulness",
#         "robustness",
#         "privacy"
#     ]
# }

# # Bootstrap once
# if not MAPPING_FILE.exists():
#     MAPPING_FILE.write_text(json.dumps(DEFAULT_MAPPING, indent=2))


# # =========================================================
# # UTILITIES
# # =========================================================

# def normalize(text: str) -> str:
#     return str(text).lower().strip()


# def load_mapping():
#     return json.loads(MAPPING_FILE.read_text())


# def save_mapping(mapping):
#     MAPPING_FILE.write_text(json.dumps(mapping, indent=2))


# def classify_text(text: str, mapping: dict, threshold=60):
#     text_norm = normalize(text)

#     best_score = 0
#     best_category = "Uncategorized"
#     matched_keywords = []

#     for category, keywords in mapping.items():
#         for kw in keywords:
#             score = fuzz.partial_ratio(text_norm, kw.lower())
#             if score > best_score and score >= threshold:
#                 best_score = score
#                 best_category = category
#                 matched_keywords = [kw]

#     return best_category, ", ".join(matched_keywords), best_score


# def batch_classify(records, mapping):
#     rows = []
#     for r in records:
#         cat, kws, score = classify_text(r["text"], mapping)
#         rows.append({
#             "source_title": r.get("title", ""),
#             "source_abstract": r.get("abstract", ""),
#             "input_text_preview": r["text"][:180],
#             "predicted_category": cat,
#             "matched_keywords": kws,
#             "confidence": score
#         })
#     return pd.DataFrame(rows)


# def directory_fingerprint(path: Path) -> str:
#     parts = []
#     for p in sorted(path.glob("*")):
#         if p.is_file():
#             stat = p.stat()
#             parts.append(f"{p.name}:{stat.st_mtime_ns}")
#     raw = "|".join(parts).encode("utf-8")
#     return hashlib.md5(raw).hexdigest()


# # =========================================================
# # LOAD UNIQUE MATCHED REFERENCES (TITLE + ABSTRACT SUPPORT)
# # =========================================================

# @st.cache_data(show_spinner=False)
# def load_unique_matched(_json_fp: str, _csv_fp: str):

#     def normalize_text(x):
#         return str(x).strip().lower()

#     # ---------------- JSON ----------------
#     rows = []
#     for path in sorted(REGISTRY_DIR.glob("*.json")):
#         try:
#             data = json.loads(path.read_text(encoding="utf-8"))
#         except Exception:
#             continue

#         root = data.get("research_plan_references", {})
#         if not isinstance(root, dict):
#             continue

#         for layer in root.values():
#             for ref in layer.get("literature_references", []):
#                 rows.append({
#                     "json_title": ref.get("title", ""),
#                     "json_abstract": ref.get("abstract", "")
#                 })

#     json_df = pd.DataFrame(rows)

#     if json_df.empty:
#         return pd.DataFrame()

#     json_df["title_norm"] = json_df["json_title"].map(normalize_text)

#     # ---------------- CSV ----------------
#     frames = []
#     for path in sorted(CSV_DIR.glob("*.csv")):
#         try:
#             df = pd.read_csv(path)
#             frames.append(df)
#         except Exception:
#             pass

#     if not frames:
#         return pd.DataFrame()

#     csv_df = pd.concat(frames, ignore_index=True)
#     csv_df.columns = csv_df.columns.str.strip()

#     if "Title" not in csv_df.columns:
#         return pd.DataFrame()

#     csv_df["title_norm"] = csv_df["Title"].map(normalize_text)

#     # Detect abstract column if exists
#     abstract_col = next(
#         (c for c in ["Abstract", "abstract", "Summary", "summary"] if c in csv_df.columns),
#         None
#     )

#     # ---------------- MATCH ----------------
#     merged = json_df.merge(
#         csv_df,
#         on="title_norm",
#         how="left"
#     )

#     matched = merged[merged["Title"].notna()]

#     # Deduplicate safely
#     unique = matched.drop_duplicates(subset="title_norm")

#     # Normalize abstract source
#     if abstract_col:
#         unique["csv_abstract"] = unique[abstract_col]
#     else:
#         unique["csv_abstract"] = ""

#     return unique


# json_fp = directory_fingerprint(REGISTRY_DIR)
# csv_fp = directory_fingerprint(CSV_DIR)

# unique_matched = load_unique_matched(json_fp, csv_fp)

# # =========================================================
# # SIDEBAR — CATEGORY EDITOR
# # =========================================================

# mapping = load_mapping()

# st.sidebar.header("🛠 Category Mapping")

# selected_category = st.sidebar.selectbox(
#     "Select category",
#     list(mapping.keys()),
#     key="category_selector"
# )

# keywords_text = st.sidebar.text_area(
#     "Keywords (comma separated)",
#     value=", ".join(mapping[selected_category]),
#     height=140,
#     key="keyword_editor"
# )

# if st.sidebar.button("💾 Save Keywords", key="save_keywords_btn"):
#     mapping[selected_category] = [
#         k.strip() for k in keywords_text.split(",") if k.strip()
#     ]
#     save_mapping(mapping)
#     st.sidebar.success("Saved!")

# st.sidebar.divider()

# new_category = st.sidebar.text_input("➕ New Category Name", key="new_category_input")

# if st.sidebar.button("Add Category", key="add_category_btn"):
#     if new_category and new_category not in mapping:
#         mapping[new_category] = []
#         save_mapping(mapping)
#         st.sidebar.success(f"Added {new_category}")
#     else:
#         st.sidebar.warning("Invalid or existing category")

# # =========================================================
# # INPUT SELECTION
# # =========================================================

# st.header("📥 Input Source")

# input_mode = st.radio(
#     "Select Input Mode",
#     [
#         "✍️ Paste Text",
#         "📂 Upload CSV",
#         "🔗 Use Unique Matched References"
#     ],
#     horizontal=True,
#     key="input_mode_selector"
# )

# records = []

# # ---------------- Paste ----------------
# if input_mode == "✍️ Paste Text":
#     input_text = st.text_area(
#         "Paste text (one record per line)",
#         height=220,
#         key="paste_text_area"
#     )

#     if input_text.strip():
#         records = [
#             {"title": "", "abstract": "", "text": line.strip()}
#             for line in input_text.split("\n")
#             if line.strip()
#         ]

# # ---------------- CSV ----------------
# elif input_mode == "📂 Upload CSV":
#     uploaded_file = st.file_uploader(
#         "Upload CSV (title / abstract supported)",
#         type=["csv"],
#         key="csv_uploader"
#     )

#     if uploaded_file:
#         df_upload = pd.read_csv(uploaded_file)

#         title_col = next((c for c in ["title", "Title"] if c in df_upload.columns), None)
#         abstract_col = next((c for c in ["abstract", "Abstract", "summary"] if c in df_upload.columns), None)

#         if not title_col and not abstract_col:
#             st.error("CSV must contain at least one column: title or abstract")
#         else:
#             for _, row in df_upload.iterrows():
#                 text = " ".join([
#                     str(row.get(title_col, "")),
#                     str(row.get(abstract_col, ""))
#                 ]).strip()

#                 records.append({
#                     "title": row.get(title_col, ""),
#                     "abstract": row.get(abstract_col, ""),
#                     "text": text
#                 })

# # ---------------- Unique Matched ----------------
# elif input_mode == "🔗 Use Unique Matched References":

#     if unique_matched.empty:
#         st.warning("No unique matched references available.")
#     else:
#         st.success(f"Loaded {len(unique_matched)} unique references")

#         preview_cols = [c for c in [
#             "json_title", "json_abstract", "Title", "csv_abstract", "Journal", "Year"
#         ] if c in unique_matched.columns]

#         st.dataframe(
#             unique_matched[preview_cols].head(30),
#             use_container_width=True,
#             height=260
#         )

#         content_mode = st.radio(
#             "Select content for classification",
#             [
#                 "🏷 Title Only",
#                 "📄 Abstract Only",
#                 "🔗 Title + Abstract"
#             ],
#             horizontal=True,
#             key="content_mode_selector"
#         )

#         for _, row in unique_matched.iterrows():

#             title = row.get("json_title") or row.get("Title") or ""
#             abstract = row.get("json_abstract") or row.get("csv_abstract") or ""

#             if content_mode == "🏷 Title Only":
#                 text = title
#             elif content_mode == "📄 Abstract Only":
#                 text = abstract
#             else:
#                 text = f"{title}. {abstract}"

#             if text.strip():
#                 records.append({
#                     "title": title,
#                     "abstract": abstract,
#                     "text": text
#                 })

# # =========================================================
# # CLASSIFICATION
# # =========================================================

# run_btn = st.button("🚀 Classify", key="classify_btn")

# if run_btn and records:

#     result_df = batch_classify(records, mapping)

#     st.success(f"Classified {len(result_df)} records")
#     st.dataframe(result_df, use_container_width=True)

#     # Manual override
#     st.subheader("✍️ Manual Override")

#     edited_df = st.data_editor(
#         result_df,
#         num_rows="dynamic",
#         use_container_width=True,
#         key="editor"
#     )

#     # Export
#     st.subheader("📤 Export")

#     csv_data = edited_df.to_csv(index=False).encode("utf-8")
#     json_data = edited_df.to_json(orient="records", indent=2).encode("utf-8")

#     c1, c2 = st.columns(2)

#     with c1:
#         st.download_button(
#             "⬇️ Download CSV",
#             csv_data,
#             file_name="literature_mapping.csv",
#             mime="text/csv",
#             key="download_csv_btn"
#         )

#     with c2:
#         st.download_button(
#             "⬇️ Download JSON",
#             json_data,
#             file_name="literature_mapping.json",
#             mime="application/json",
#             key="download_json_btn"
#         )

# elif run_btn:
#     st.warning("Please provide at least one record to classify.")


# import streamlit as st
# import pandas as pd
# import json
# from pathlib import Path
# from rapidfuzz import fuzz
# import hashlib

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📚 Literature Category Mapper",
#     layout="wide"
# )

# st.title("📚 Literature Category Mapper")
# st.caption("Map paper titles into categories (RAG, Aspect, ESG, etc.)")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# DATA_DIR = BASE_DIR / "data"
# DATA_DIR.mkdir(exist_ok=True)

# MAPPING_FILE = DATA_DIR / "category_mapping.json"

# REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
# CSV_DIR = BASE_DIR / "data" / "csv"

# REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
# CSV_DIR.mkdir(parents=True, exist_ok=True)

# # =========================================================
# # DEFAULT CATEGORY MAPPING
# # =========================================================

# DEFAULT_MAPPING = {
#     "RAG": [
#         "retrieval",
#         "rag",
#         "retrieval-augmented",
#         "knowledge graph",
#         "reranking",
#         "question answering"
#     ],
#     "Aspect": [
#         "aspect",
#         "sentiment",
#         "absa",
#         "opinion",
#         "emotion",
#         "quadruple",
#         "triplet"
#     ],
#     "ESG": [
#         "esg",
#         "sustainability",
#         "environmental",
#         "governance",
#         "finance",
#         "investment"
#     ],
#     "Evaluation": [
#         "benchmark",
#         "evaluation",
#         "leaderboard",
#         "dataset",
#         "metric"
#     ],
#     "Reasoning": [
#         "reasoning",
#         "chain-of-thought",
#         "planning",
#         "symbolic",
#         "logic",
#         "multi-agent"
#     ],
#     "Multilingual": [
#         "multilingual",
#         "cross-lingual",
#         "translation",
#         "indonesian",
#         "language"
#     ],
#     "Safety": [
#         "hallucination",
#         "alignment",
#         "safety",
#         "bias",
#         "truthfulness"
#     ]
# }

# # Initialize mapping file
# if not MAPPING_FILE.exists():
#     MAPPING_FILE.write_text(json.dumps(DEFAULT_MAPPING, indent=2))

# # =========================================================
# # UTILITIES
# # =========================================================

# def normalize(text: str) -> str:
#     return str(text).lower().strip()


# def load_mapping():
#     return json.loads(MAPPING_FILE.read_text())


# def save_mapping(mapping):
#     MAPPING_FILE.write_text(json.dumps(mapping, indent=2))


# def classify_title(title: str, mapping: dict, threshold=60):
#     title_norm = normalize(title)

#     best_score = 0
#     best_category = "Uncategorized"
#     matched_keywords = []

#     for category, keywords in mapping.items():
#         for kw in keywords:
#             score = fuzz.partial_ratio(title_norm, kw.lower())
#             if score > best_score and score >= threshold:
#                 best_score = score
#                 best_category = category
#                 matched_keywords = [kw]

#     return best_category, ", ".join(matched_keywords), best_score


# def batch_classify(titles, mapping):
#     rows = []
#     for t in titles:
#         cat, kws, score = classify_title(t, mapping)
#         rows.append({
#             "title": t,
#             "predicted_category": cat,
#             "matched_keywords": kws,
#             "confidence": score
#         })
#     return pd.DataFrame(rows)


# def directory_fingerprint(path: Path) -> str:
#     parts = []
#     for p in sorted(path.glob("*")):
#         if p.is_file():
#             stat = p.stat()
#             parts.append(f"{p.name}:{stat.st_mtime_ns}")
#     raw = "|".join(parts).encode("utf-8")
#     return hashlib.md5(raw).hexdigest()


# # =========================================================
# # LOAD UNIQUE MATCHED REFERENCES (FROM YOUR ANALYZER LOGIC)
# # =========================================================

# @st.cache_data(show_spinner=False)
# def load_unique_matched(_json_fp: str, _csv_fp: str):

#     def normalize_text(x):
#         return str(x).strip().lower()

#     # ---------------- JSON ----------------
#     rows = []
#     for path in sorted(REGISTRY_DIR.glob("*.json")):
#         try:
#             data = json.loads(path.read_text(encoding="utf-8"))
#         except Exception:
#             continue

#         root = data.get("research_plan_references", {})
#         if not isinstance(root, dict):
#             continue

#         for layer_key, layer in root.items():
#             for ref in layer.get("literature_references", []):
#                 rows.append({
#                     "json_title": ref.get("title", "")
#                 })

#     json_df = pd.DataFrame(rows)
#     if json_df.empty:
#         return pd.DataFrame()

#     json_df["title_norm"] = json_df["json_title"].map(normalize_text)

#     # ---------------- CSV ----------------
#     frames = []
#     for path in sorted(CSV_DIR.glob("*.csv")):
#         try:
#             df = pd.read_csv(path)
#             frames.append(df)
#         except Exception:
#             pass

#     if not frames:
#         return pd.DataFrame()

#     csv_df = pd.concat(frames, ignore_index=True)
#     csv_df.columns = csv_df.columns.str.strip()

#     if "Title" not in csv_df.columns:
#         return pd.DataFrame()

#     csv_df["title_norm"] = csv_df["Title"].map(normalize_text)

#     # ---------------- MATCH ----------------
#     merged = json_df.merge(
#         csv_df,
#         on="title_norm",
#         how="left"
#     )

#     matched = merged[merged["Title"].notna()]

#     # Deduplicate safely
#     unique_matched = matched.drop_duplicates(subset="title_norm")

#     return unique_matched


# json_fp = directory_fingerprint(REGISTRY_DIR)
# csv_fp = directory_fingerprint(CSV_DIR)

# unique_matched = load_unique_matched(json_fp, csv_fp)

# # =========================================================
# # SIDEBAR — CATEGORY EDITOR
# # =========================================================

# mapping = load_mapping()

# st.sidebar.header("🛠 Category Mapping")

# selected_category = st.sidebar.selectbox(
#     "Select category",
#     list(mapping.keys()),
#     key="category_selector"
# )

# keywords_text = st.sidebar.text_area(
#     "Keywords (comma separated)",
#     value=", ".join(mapping[selected_category]),
#     height=120,
#     key="keyword_editor"
# )

# if st.sidebar.button("💾 Save Keywords", key="save_keywords_btn"):
#     mapping[selected_category] = [
#         k.strip() for k in keywords_text.split(",") if k.strip()
#     ]
#     save_mapping(mapping)
#     st.sidebar.success("Saved!")

# st.sidebar.divider()

# new_category = st.sidebar.text_input("➕ New Category Name", key="new_category_input")

# if st.sidebar.button("Add Category", key="add_category_btn"):
#     if new_category and new_category not in mapping:
#         mapping[new_category] = []
#         save_mapping(mapping)
#         st.sidebar.success(f"Added {new_category}")
#     else:
#         st.sidebar.warning("Invalid or existing category")

# # =========================================================
# # INPUT SELECTION
# # =========================================================

# st.header("📥 Input Titles")

# input_mode = st.radio(
#     "Select Input Source",
#     [
#         "✍️ Paste Text",
#         "📂 Upload CSV",
#         "🔗 Use Unique Matched References"
#     ],
#     horizontal=True,
#     key="input_mode_selector"
# )

# titles = []

# # ---------------- Paste ----------------
# if input_mode == "✍️ Paste Text":
#     input_text = st.text_area(
#         "Paste paper titles (one per line)",
#         height=220,
#         key="paste_text_area"
#     )

#     if input_text.strip():
#         titles = [t.strip() for t in input_text.split("\n") if t.strip()]

# # ---------------- CSV ----------------
# elif input_mode == "📂 Upload CSV":
#     uploaded_file = st.file_uploader(
#         "Upload CSV (must contain column: title or Title)",
#         type=["csv"],
#         key="csv_uploader"
#     )

#     if uploaded_file:
#         df_upload = pd.read_csv(uploaded_file)

#         possible_cols = ["title", "Title"]
#         title_col = next((c for c in possible_cols if c in df_upload.columns), None)

#         if not title_col:
#             st.error("CSV must contain a column named 'title' or 'Title'")
#         else:
#             titles = (
#                 df_upload[title_col]
#                 .dropna()
#                 .astype(str)
#                 .tolist()
#             )

# # ---------------- Unique Matched ----------------
# elif input_mode == "🔗 Use Unique Matched References":

#     if unique_matched.empty:
#         st.warning("No unique matched references available.")
#     else:
#         st.success(f"Loaded {len(unique_matched)} unique references")

#         preview_cols = [c for c in ["json_title", "Title", "Journal", "Year"] if c in unique_matched.columns]

#         st.dataframe(
#             unique_matched[preview_cols].head(50),
#             use_container_width=True,
#             height=280
#         )

#         title_source = st.selectbox(
#             "Select title column",
#             options=[c for c in ["json_title", "Title"] if c in unique_matched.columns],
#             key="title_source_selector"
#         )

#         titles = (
#             unique_matched[title_source]
#             .dropna()
#             .astype(str)
#             .tolist()
#         )

# # =========================================================
# # CLASSIFICATION
# # =========================================================

# run_btn = st.button("🚀 Classify", key="classify_btn")

# if run_btn and titles:

#     result_df = batch_classify(titles, mapping)

#     st.success(f"Classified {len(result_df)} titles")
#     st.dataframe(result_df, use_container_width=True)

#     # Manual override
#     st.subheader("✍️ Manual Override")

#     edited_df = st.data_editor(
#         result_df,
#         num_rows="dynamic",
#         use_container_width=True,
#         key="editor"
#     )

#     # Export
#     st.subheader("📤 Export")

#     csv_data = edited_df.to_csv(index=False).encode("utf-8")
#     json_data = edited_df.to_json(orient="records", indent=2).encode("utf-8")

#     c1, c2 = st.columns(2)

#     with c1:
#         st.download_button(
#             "⬇️ Download CSV",
#             csv_data,
#             file_name="literature_mapping.csv",
#             mime="text/csv",
#             key="download_csv_btn"
#         )

#     with c2:
#         st.download_button(
#             "⬇️ Download JSON",
#             json_data,
#             file_name="literature_mapping.json",
#             mime="application/json",
#             key="download_json_btn"
#         )

# elif run_btn:
#     st.warning("Please provide at least one title.")


# import streamlit as st
# import pandas as pd
# import json
# from pathlib import Path
# from rapidfuzz import fuzz

# # ============================
# # CONFIG
# # ============================

# st.set_page_config(
#     page_title="📚 Literature Keyword Mapper",
#     layout="wide"
# )

# BASE_DIR = Path(__file__).parent
# DATA_DIR = BASE_DIR / "data"
# DATA_DIR.mkdir(exist_ok=True)

# MAPPING_FILE = DATA_DIR / "mappings.json"

# DEFAULT_MAPPING = {
#     "RAG": [
#         "retrieval",
#         "rag",
#         "retrieval-augmented",
#         "knowledge graph",
#         "reranking",
#         "document retrieval",
#         "question answering"
#     ],
#     "Aspect": [
#         "aspect",
#         "sentiment",
#         "absa",
#         "opinion",
#         "emotion",
#         "quadruple",
#         "triplet"
#     ],
#     "ESG": [
#         "esg",
#         "sustainability",
#         "environmental",
#         "governance",
#         "finance",
#         "investment",
#         "carbon"
#     ],
#     "Evaluation": [
#         "benchmark",
#         "evaluation",
#         "leaderboard",
#         "dataset",
#         "metric"
#     ],
#     "Reasoning": [
#         "reasoning",
#         "chain-of-thought",
#         "planning",
#         "symbolic",
#         "logic",
#         "multi-agent"
#     ],
#     "Multilingual": [
#         "multilingual",
#         "cross-lingual",
#         "translation",
#         "indonesian",
#         "language"
#     ],
#     "Safety": [
#         "hallucination",
#         "alignment",
#         "safety",
#         "bias",
#         "toxicity",
#         "truthfulness"
#     ]
# }

# # Initialize mapping file
# if not MAPPING_FILE.exists():
#     MAPPING_FILE.write_text(json.dumps(DEFAULT_MAPPING, indent=2))


# # ============================
# # UTILITIES
# # ============================

# def load_mapping():
#     return json.loads(MAPPING_FILE.read_text())


# def save_mapping(mapping):
#     MAPPING_FILE.write_text(json.dumps(mapping, indent=2))


# def normalize(text: str) -> str:
#     return text.lower().strip()


# def classify_title(title: str, mapping: dict, threshold=60):
#     """
#     Returns:
#         best_category, matched_keywords, score
#     """
#     title_norm = normalize(title)
#     best_score = 0
#     best_category = "Uncategorized"
#     matched_keywords = []

#     for category, keywords in mapping.items():
#         for kw in keywords:
#             score = fuzz.partial_ratio(title_norm, kw.lower())
#             if score > best_score and score >= threshold:
#                 best_score = score
#                 best_category = category
#                 matched_keywords = [kw]

#     return best_category, matched_keywords, best_score


# def batch_classify(titles, mapping):
#     rows = []
#     for t in titles:
#         cat, kws, score = classify_title(t, mapping)
#         rows.append({
#             "title": t,
#             "predicted_category": cat,
#             "matched_keywords": ", ".join(kws),
#             "confidence": score
#         })
#     return pd.DataFrame(rows)


# # ============================
# # UI
# # ============================

# st.title("📚 Literature Keyword Mapper")
# st.caption("Automatically categorize paper titles using keyword rules")

# mapping = load_mapping()

# # ----------------------------
# # Sidebar: Category Editor
# # ----------------------------

# st.sidebar.header("🛠 Category Mapping")

# selected_category = st.sidebar.selectbox(
#     "Select category",
#     list(mapping.keys())
# )

# keywords_text = st.sidebar.text_area(
#     "Keywords (comma separated)",
#     value=", ".join(mapping[selected_category]),
#     height=120
# )

# if st.sidebar.button("💾 Save Keywords"):
#     mapping[selected_category] = [
#         k.strip() for k in keywords_text.split(",") if k.strip()
#     ]
#     save_mapping(mapping)
#     st.sidebar.success("Saved!")

# st.sidebar.divider()

# # Add new category
# new_category = st.sidebar.text_input("➕ New Category Name")
# if st.sidebar.button("Add Category"):
#     if new_category and new_category not in mapping:
#         mapping[new_category] = []
#         save_mapping(mapping)
#         st.sidebar.success(f"Added {new_category}")
#     else:
#         st.sidebar.warning("Invalid or existing category")


# # ----------------------------
# # Input
# # ----------------------------

# st.header("📥 Input Titles")

# input_text = st.text_area(
#     "Paste paper titles (one per line)",
#     height=250
# )

# uploaded_file = st.file_uploader(
#     "Or upload CSV (column: title)",
#     type=["csv"]
# )

# titles = []

# if input_text.strip():
#     titles.extend([x.strip() for x in input_text.split("\n") if x.strip()])

# if uploaded_file:
#     df_upload = pd.read_csv(uploaded_file)
#     if "title" not in df_upload.columns:
#         st.error("CSV must contain a column named 'title'")
#     else:
#         titles.extend(df_upload["title"].dropna().tolist())


# # ----------------------------
# # Classification
# # ----------------------------

# if st.button("🚀 Classify") and titles:
#     result_df = batch_classify(titles, mapping)

#     st.success(f"Classified {len(result_df)} titles")
#     st.dataframe(result_df, use_container_width=True)

#     # ------------------------
#     # Manual override
#     # ------------------------

#     st.subheader("✍️ Manual Override")

#     edited_df = st.data_editor(
#         result_df,
#         num_rows="dynamic",
#         use_container_width=True
#     )

#     # ------------------------
#     # Export
#     # ------------------------

#     st.subheader("📤 Export")

#     csv_data = edited_df.to_csv(index=False).encode("utf-8")
#     json_data = edited_df.to_json(orient="records", indent=2).encode("utf-8")

#     col1, col2 = st.columns(2)

#     with col1:
#         st.download_button(
#             "⬇️ Download CSV",
#             csv_data,
#             file_name="literature_mapping.csv",
#             mime="text/csv"
#         )

#     with col2:
#         st.download_button(
#             "⬇️ Download JSON",
#             json_data,
#             file_name="literature_mapping.json",
#             mime="application/json"
#         )

# elif st.button("🚀 Classify"):
#     st.warning("Please provide at least one title.")
