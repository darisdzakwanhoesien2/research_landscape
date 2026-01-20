import json
import pandas as pd
import streamlit as st
from pathlib import Path
import hashlib

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📊 Reference Coverage Analyzer",
    layout="wide"
)

st.title("📊 Reference Coverage Analyzer")
st.caption("Merge JSON registry with CSV literature database and analyze journal coverage")

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
CSV_DIR = BASE_DIR / "data" / "csv"

REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 JSON Registry: `{REGISTRY_DIR}`")
st.sidebar.caption(f"📁 CSV Database: `{CSV_DIR}`")

# =========================================================
# UTILITIES
# =========================================================

def normalize_text(x):
    return str(x).strip().lower()


def directory_fingerprint(path: Path) -> str:
    """
    Generate a fingerprint based on filenames + modification timestamps.
    Any change triggers cache invalidation automatically.
    """
    parts = []
    for p in sorted(path.glob("*")):
        if p.is_file():
            stat = p.stat()
            parts.append(f"{p.name}:{stat.st_mtime_ns}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


# =========================================================
# CACHE-AWARE LOADERS
# =========================================================

@st.cache_data(show_spinner=False)
def load_all_json(_fingerprint: str):
    rows = []
    files = sorted(REGISTRY_DIR.glob("*.json"))

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        root = data.get("research_plan_references", {})
        if not isinstance(root, dict):
            continue

        for layer_key, layer in root.items():
            focus = layer.get("focus", "")

            for ref in layer.get("literature_references", []):
                rows.append({
                    "registry_file": path.name,
                    "objective_layer": layer_key,
                    "focus": focus,
                    "json_title": ref.get("title", ""),
                    "json_authors": ref.get("authors", ""),
                    "json_source_index": ref.get("source_index"),
                    "json_relevance": ref.get("relevance", ""),
                })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["title_norm"] = df["json_title"].map(normalize_text)

    return df


@st.cache_data(show_spinner=False)
def load_all_csv(_fingerprint: str):
    frames = []
    files = sorted(CSV_DIR.glob("*.csv"))

    for path in files:
        try:
            df = pd.read_csv(path)
            df["__source_file"] = path.name
            frames.append(df)
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df.columns = df.columns.str.strip()

    if "Title" in df.columns:
        df["title_norm"] = df["Title"].map(normalize_text)

    return df


# =========================================================
# MANUAL RELOAD CONTROL
# =========================================================

st.sidebar.divider()
st.sidebar.header("🔄 Data Control")

if st.sidebar.button("♻️ Reload Data"):
    load_all_json.clear()
    load_all_csv.clear()
    st.rerun()

# =========================================================
# LOAD DATA WITH AUTO INVALIDATION
# =========================================================

json_fingerprint = directory_fingerprint(REGISTRY_DIR)
csv_fingerprint = directory_fingerprint(CSV_DIR)

json_df = load_all_json(json_fingerprint)
csv_df = load_all_csv(csv_fingerprint)

if json_df.empty:
    st.warning("⚠️ No valid JSON registry files found.")
    st.stop()

if csv_df.empty:
    st.warning("⚠️ No CSV files found in data/csv.")
    st.stop()

# =========================================================
# MATCH JSON ↔ CSV
# =========================================================

merged = json_df.merge(
    csv_df,
    on="title_norm",
    how="left"
)

matched = merged[merged["Title"].notna()]
unmatched = merged[merged["Title"].isna()]

# =========================================================
# ✅ UNIQUE MATCHED REFERENCES (DEDUPLICATED + SAFE SORT)
# =========================================================

def build_unique_key(df: pd.DataFrame) -> pd.Series:
    """
    Stable deduplication key:
        DOI → title_norm → json_title
    """
    if "DOI" in df.columns:
        return (
            df["DOI"]
            .fillna(df["title_norm"])
            .fillna(df["json_title"])
            .astype(str)
            .str.strip()
            .str.lower()
        )
    else:
        return (
            df["title_norm"]
            .fillna(df["json_title"])
            .astype(str)
            .str.strip()
            .str.lower()
        )


unique_matched = matched.copy()

if not unique_matched.empty:
    unique_matched["__dedup_key"] = build_unique_key(unique_matched)

    unique_matched = (
        unique_matched
        .drop_duplicates(subset="__dedup_key")
        .drop(columns="__dedup_key")
    )

# Safe numeric year sort (handles mixed int/str safely)
if "Year" in unique_matched.columns and not unique_matched.empty:
    unique_matched["__year_num"] = pd.to_numeric(
        unique_matched["Year"],
        errors="coerce"
    )

    unique_matched = (
        unique_matched
        .sort_values("__year_num", ascending=False)
        .drop(columns="__year_num")
    )

# =========================================================
# JOURNAL COVERAGE ANALYSIS
# =========================================================

missing_journal_df = pd.DataFrame()

if "Journal" in csv_df.columns and not matched.empty:

    all_journals = (
        csv_df["Journal"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    referenced_journals = (
        matched["Journal"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    missing_journals = sorted(
        set(all_journals) - set(referenced_journals)
    )

    if missing_journals:
        missing_journal_df = (
            csv_df[csv_df["Journal"].isin(missing_journals)]
            .groupby("Journal")
            .agg(
                paper_count=("Title", "count"),
                examples=("Title", lambda x: ", ".join(x.head(3)))
            )
            .reset_index()
            .sort_values("paper_count", ascending=False)
        )

# =========================================================
# UI TABS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🔗 Matched References",
    "❌ Unmatched JSON References",
    "📉 Missing Journal Coverage",
    "📌 Unique Matched References"
])

# =========================================================
# TAB 1 — MATCHED
# =========================================================

with tab1:
    st.subheader("🔗 JSON References Matched with CSV Database")
    st.caption(f"Matched references: {len(matched)}")

    show_cols = [
        "registry_file",
        "objective_layer",
        "json_title",
        "Journal",
        "Year",
        "DOI",
        "__source_file",
        "json_relevance",
    ]

    available_cols = [c for c in show_cols if c in matched.columns]

    st.dataframe(
        matched[available_cols],
        use_container_width=True,
        height=520
    )

# =========================================================
# TAB 2 — UNMATCHED
# =========================================================

with tab2:
    st.subheader("❌ JSON References Not Found in CSV Database")
    st.caption(f"Unmatched references: {len(unmatched)}")

    show_cols = [
        "registry_file",
        "objective_layer",
        "json_title",
        "json_authors",
        "json_relevance",
    ]

    available_cols = [c for c in show_cols if c in unmatched.columns]

    st.dataframe(
        unmatched[available_cols],
        use_container_width=True,
        height=520
    )

    st.warning(
        "These references were not found in your CSV database. "
        "Possible causes: title mismatches, missing records, or normalization issues."
    )

# =========================================================
# TAB 3 — MISSING JOURNALS
# =========================================================

with tab3:
    st.subheader("📉 Journals Present in CSV but NOT Referenced in JSON")

    if missing_journal_df.empty:
        st.success("🎉 All journals in CSV are covered by registry references!")
    else:
        st.caption(f"Missing journals: {len(missing_journal_df)}")

        st.dataframe(
            missing_journal_df,
            use_container_width=True,
            height=520
        )

        csv_bytes = missing_journal_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Missing Journal Report",
            data=csv_bytes,
            file_name="missing_journals.csv",
            mime="text/csv"
        )

# =========================================================
# TAB 4 — UNIQUE MATCHED REFERENCES
# =========================================================

with tab4:
    st.subheader("📌 Unique Matched References (Deduplicated)")
    st.caption(
        f"Unique references: {len(unique_matched)} "
        f"(from {len(matched)} matched rows)"
    )

    show_cols = [
        "json_title",
        "Journal",
        "Year",
        "DOI",
        "json_authors",
        "__source_file",
    ]

    available_cols = [c for c in show_cols if c in unique_matched.columns]

    st.dataframe(
        unique_matched[available_cols],
        use_container_width=True,
        height=520
    )

    unique_csv = unique_matched.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Unique References",
        data=unique_csv,
        file_name="unique_matched_references.csv",
        mime="text/csv"
    )



# import json
# import pandas as pd
# import streamlit as st
# from pathlib import Path
# import hashlib

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📊 Reference Coverage Analyzer",
#     layout="wide"
# )

# st.title("📊 Reference Coverage Analyzer")
# st.caption("Merge JSON registry with CSV literature database and analyze journal coverage")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
# CSV_DIR = BASE_DIR / "data" / "csv"

# REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
# CSV_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 JSON Registry: `{REGISTRY_DIR}`")
# st.sidebar.caption(f"📁 CSV Database: `{CSV_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# def normalize_text(x):
#     return str(x).strip().lower()


# def directory_fingerprint(path: Path) -> str:
#     """
#     Generate a fingerprint based on filenames + modification timestamps.
#     Any change triggers cache invalidation automatically.
#     """
#     parts = []
#     for p in sorted(path.glob("*")):
#         if p.is_file():
#             stat = p.stat()
#             parts.append(f"{p.name}:{stat.st_mtime_ns}")
#     raw = "|".join(parts).encode("utf-8")
#     return hashlib.md5(raw).hexdigest()


# # =========================================================
# # CACHE-AWARE LOADERS
# # =========================================================

# @st.cache_data(show_spinner=False)
# def load_all_json(_fingerprint: str):
#     rows = []
#     files = sorted(REGISTRY_DIR.glob("*.json"))

#     for path in files:
#         try:
#             data = json.loads(path.read_text(encoding="utf-8"))
#         except Exception:
#             continue

#         root = data.get("research_plan_references", {})
#         if not isinstance(root, dict):
#             continue

#         for layer_key, layer in root.items():
#             focus = layer.get("focus", "")

#             for ref in layer.get("literature_references", []):
#                 rows.append({
#                     "registry_file": path.name,
#                     "objective_layer": layer_key,
#                     "focus": focus,
#                     "json_title": ref.get("title", ""),
#                     "json_authors": ref.get("authors", ""),
#                     "json_source_index": ref.get("source_index"),
#                     "json_relevance": ref.get("relevance", ""),
#                 })

#     df = pd.DataFrame(rows)

#     if not df.empty:
#         df["title_norm"] = df["json_title"].map(normalize_text)

#     return df


# @st.cache_data(show_spinner=False)
# def load_all_csv(_fingerprint: str):
#     frames = []
#     files = sorted(CSV_DIR.glob("*.csv"))

#     for path in files:
#         try:
#             df = pd.read_csv(path)
#             df["__source_file"] = path.name
#             frames.append(df)
#         except Exception:
#             pass

#     if not frames:
#         return pd.DataFrame()

#     df = pd.concat(frames, ignore_index=True)
#     df.columns = df.columns.str.strip()

#     if "Title" in df.columns:
#         df["title_norm"] = df["Title"].map(normalize_text)

#     return df


# # =========================================================
# # MANUAL RELOAD CONTROL
# # =========================================================

# st.sidebar.divider()
# st.sidebar.header("🔄 Data Control")

# if st.sidebar.button("♻️ Reload Data"):
#     load_all_json.clear()
#     load_all_csv.clear()
#     st.rerun()

# # =========================================================
# # LOAD DATA WITH AUTO INVALIDATION
# # =========================================================

# json_fingerprint = directory_fingerprint(REGISTRY_DIR)
# csv_fingerprint = directory_fingerprint(CSV_DIR)

# json_df = load_all_json(json_fingerprint)
# csv_df = load_all_csv(csv_fingerprint)

# if json_df.empty:
#     st.warning("⚠️ No valid JSON registry files found.")
#     st.stop()

# if csv_df.empty:
#     st.warning("⚠️ No CSV files found in data/csv.")
#     st.stop()

# # =========================================================
# # MATCH JSON ↔ CSV
# # =========================================================

# merged = json_df.merge(
#     csv_df,
#     on="title_norm",
#     how="left"
# )

# matched = merged[merged["Title"].notna()]
# unmatched = merged[merged["Title"].isna()]

# # =========================================================
# # JOURNAL COVERAGE ANALYSIS
# # =========================================================

# missing_journal_df = pd.DataFrame()

# if "Journal" in csv_df.columns and not matched.empty:

#     all_journals = (
#         csv_df["Journal"]
#         .dropna()
#         .astype(str)
#         .str.strip()
#     )

#     referenced_journals = (
#         matched["Journal"]
#         .dropna()
#         .astype(str)
#         .str.strip()
#     )

#     missing_journals = sorted(
#         set(all_journals) - set(referenced_journals)
#     )

#     if missing_journals:
#         missing_journal_df = (
#             csv_df[csv_df["Journal"].isin(missing_journals)]
#             .groupby("Journal")
#             .agg(
#                 paper_count=("Title", "count"),
#                 examples=("Title", lambda x: ", ".join(x.head(3)))
#             )
#             .reset_index()
#             .sort_values("paper_count", ascending=False)
#         )

# # =========================================================
# # UI TABS
# # =========================================================

# tab1, tab2, tab3 = st.tabs([
#     "🔗 Matched References",
#     "❌ Unmatched JSON References",
#     "📉 Missing Journal Coverage"
# ])

# # =========================================================
# # TAB 1 — MATCHED
# # =========================================================

# with tab1:
#     st.subheader("🔗 JSON References Matched with CSV Database")
#     st.caption(f"Matched references: {len(matched)}")

#     show_cols = [
#         "registry_file",
#         "objective_layer",
#         "json_title",
#         "Journal",
#         "Year",
#         "DOI",
#         "__source_file",
#         "json_relevance",
#     ]

#     available_cols = [c for c in show_cols if c in matched.columns]

#     st.dataframe(
#         matched[available_cols],
#         use_container_width=True,
#         height=520
#     )

# # =========================================================
# # TAB 2 — UNMATCHED
# # =========================================================

# with tab2:
#     st.subheader("❌ JSON References Not Found in CSV Database")
#     st.caption(f"Unmatched references: {len(unmatched)}")

#     show_cols = [
#         "registry_file",
#         "objective_layer",
#         "json_title",
#         "json_authors",
#         "json_relevance",
#     ]

#     available_cols = [c for c in show_cols if c in unmatched.columns]

#     st.dataframe(
#         unmatched[available_cols],
#         use_container_width=True,
#         height=520
#     )

#     st.warning(
#         "These references were not found in your CSV database. "
#         "Possible causes: title mismatches, missing records, or normalization issues."
#     )

# # =========================================================
# # TAB 3 — MISSING JOURNALS
# # =========================================================

# with tab3:
#     st.subheader("📉 Journals Present in CSV but NOT Referenced in JSON")

#     if missing_journal_df.empty:
#         st.success("🎉 All journals in CSV are covered by registry references!")
#     else:
#         st.caption(f"Missing journals: {len(missing_journal_df)}")

#         st.dataframe(
#             missing_journal_df,
#             use_container_width=True,
#             height=520
#         )

#         csv_bytes = missing_journal_df.to_csv(index=False).encode("utf-8")

#         st.download_button(
#             "⬇️ Download Missing Journal Report",
#             data=csv_bytes,
#             file_name="missing_journals.csv",
#             mime="text/csv"
#         )


# import json
# import pandas as pd
# import streamlit as st
# from pathlib import Path

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📊 Reference Coverage Analyzer",
#     layout="wide"
# )

# st.title("📊 Reference Coverage Analyzer")
# st.caption("Merge JSON registry with CSV literature database and analyze journal coverage")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
# CSV_DIR = BASE_DIR / "data" / "csv"

# REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
# CSV_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 JSON Registry: `{REGISTRY_DIR}`")
# st.sidebar.caption(f"📁 CSV Database: `{CSV_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# def normalize_text(x):
#     return str(x).strip().lower()


# @st.cache_data
# def load_all_json():
#     rows = []
#     files = sorted(REGISTRY_DIR.glob("*.json"))

#     for path in files:
#         try:
#             data = json.loads(path.read_text(encoding="utf-8"))
#         except Exception:
#             continue

#         root = data.get("research_plan_references", {})
#         if not isinstance(root, dict):
#             continue

#         for layer_key, layer in root.items():
#             focus = layer.get("focus", "")

#             for ref in layer.get("literature_references", []):
#                 rows.append({
#                     "registry_file": path.name,
#                     "objective_layer": layer_key,
#                     "focus": focus,
#                     "json_title": ref.get("title", ""),
#                     "json_authors": ref.get("authors", ""),
#                     "json_source_index": ref.get("source_index"),
#                     "json_relevance": ref.get("relevance", ""),
#                 })

#     df = pd.DataFrame(rows)

#     if not df.empty:
#         df["title_norm"] = df["json_title"].map(normalize_text)

#     return df


# @st.cache_data
# def load_all_csv():
#     frames = []
#     files = sorted(CSV_DIR.glob("*.csv"))

#     for path in files:
#         try:
#             df = pd.read_csv(path)
#             df["__source_file"] = path.name
#             frames.append(df)
#         except Exception:
#             pass

#     if not frames:
#         return pd.DataFrame()

#     df = pd.concat(frames, ignore_index=True)
#     df.columns = df.columns.str.strip()

#     if "Title" in df.columns:
#         df["title_norm"] = df["Title"].map(normalize_text)

#     return df


# # =========================================================
# # LOAD DATA
# # =========================================================

# json_df = load_all_json()
# csv_df = load_all_csv()

# if json_df.empty:
#     st.warning("⚠️ No valid JSON registry files found.")
#     st.stop()

# if csv_df.empty:
#     st.warning("⚠️ No CSV files found in data/csv.")
#     st.stop()

# # =========================================================
# # MATCH JSON ↔ CSV
# # =========================================================

# merged = json_df.merge(
#     csv_df,
#     on="title_norm",
#     how="left"
# )

# matched = merged[merged["Title"].notna()]
# unmatched = merged[merged["Title"].isna()]

# # =========================================================
# # JOURNAL COVERAGE ANALYSIS
# # =========================================================

# missing_journal_df = pd.DataFrame()

# if "Journal" in csv_df.columns and not matched.empty:

#     all_journals = (
#         csv_df["Journal"]
#         .dropna()
#         .astype(str)
#         .str.strip()
#     )

#     referenced_journals = (
#         matched["Journal"]
#         .dropna()
#         .astype(str)
#         .str.strip()
#     )

#     missing_journals = sorted(
#         set(all_journals) - set(referenced_journals)
#     )

#     if missing_journals:
#         missing_journal_df = (
#             csv_df[csv_df["Journal"].isin(missing_journals)]
#             .groupby("Journal")
#             .agg(
#                 paper_count=("Title", "count"),
#                 examples=("Title", lambda x: ", ".join(x.head(3)))
#             )
#             .reset_index()
#             .sort_values("paper_count", ascending=False)
#         )

# # =========================================================
# # UI TABS
# # =========================================================

# tab1, tab2, tab3 = st.tabs([
#     "🔗 Matched References",
#     "❌ Unmatched JSON References",
#     "📉 Missing Journal Coverage"
# ])

# # =========================================================
# # TAB 1 — MATCHED
# # =========================================================

# with tab1:
#     st.subheader("🔗 JSON References Matched with CSV Database")
#     st.caption(f"Matched references: {len(matched)}")

#     show_cols = [
#         "registry_file",
#         "objective_layer",
#         "json_title",
#         "Journal",
#         "Year",
#         "DOI",
#         "__source_file",
#         "json_relevance",
#     ]

#     available_cols = [c for c in show_cols if c in matched.columns]

#     st.dataframe(
#         matched[available_cols],
#         use_container_width=True,
#         height=520
#     )

# # =========================================================
# # TAB 2 — UNMATCHED
# # =========================================================

# with tab2:
#     st.subheader("❌ JSON References Not Found in CSV Database")
#     st.caption(f"Unmatched references: {len(unmatched)}")

#     show_cols = [
#         "registry_file",
#         "objective_layer",
#         "json_title",
#         "json_authors",
#         "json_relevance",
#     ]

#     available_cols = [c for c in show_cols if c in unmatched.columns]

#     st.dataframe(
#         unmatched[available_cols],
#         use_container_width=True,
#         height=520
#     )

#     st.warning(
#         "These references were not found in your CSV database. "
#         "Possible causes: title mismatches, missing records, or normalization issues."
#     )

# # =========================================================
# # TAB 3 — MISSING JOURNALS
# # =========================================================

# with tab3:
#     st.subheader("📉 Journals Present in CSV but NOT Referenced in JSON")

#     if missing_journal_df.empty:
#         st.success("🎉 All journals in CSV are covered by registry references!")
#     else:
#         st.caption(f"Missing journals: {len(missing_journal_df)}")

#         st.dataframe(
#             missing_journal_df,
#             use_container_width=True,
#             height=520
#         )

#         csv_bytes = missing_journal_df.to_csv(index=False).encode("utf-8")

#         st.download_button(
#             "⬇️ Download Missing Journal Report",
#             data=csv_bytes,
#             file_name="missing_journals.csv",
#             mime="text/csv"
#         )


# import json
# import pandas as pd
# import streamlit as st
# from pathlib import Path

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(
#     page_title="📊 Reference Coverage Analyzer",
#     layout="wide"
# )

# st.title("📊 Reference Coverage Analyzer")
# st.caption("Merge JSON registry with CSV literature database and analyze journal coverage")

# # =========================================================
# # PATH CONFIG
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
# CSV_DIR = BASE_DIR / "data" / "csv"

# REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
# CSV_DIR.mkdir(parents=True, exist_ok=True)

# st.sidebar.caption(f"📁 JSON Registry: `{REGISTRY_DIR}`")
# st.sidebar.caption(f"📁 CSV Database: `{CSV_DIR}`")

# # =========================================================
# # UTILITIES
# # =========================================================

# def normalize_text(x):
#     return str(x).strip().lower()


# @st.cache_data
# def load_all_json():
#     rows = []
#     files = sorted(REGISTRY_DIR.glob("*.json"))

#     for path in files:
#         try:
#             data = json.loads(path.read_text(encoding="utf-8"))
#         except Exception:
#             continue

#         root = data.get("research_plan_references", {})
#         if not isinstance(root, dict):
#             continue

#         for layer_key, layer in root.items():
#             focus = layer.get("focus", "")

#             for ref in layer.get("literature_references", []):
#                 rows.append({
#                     "registry_file": path.name,
#                     "objective_layer": layer_key,
#                     "focus": focus,
#                     "title": ref.get("title", ""),
#                     "authors": ref.get("authors", ""),
#                     "source_index": ref.get("source_index"),
#                     "relevance": ref.get("relevance", ""),
#                 })

#     df = pd.DataFrame(rows)
#     if not df.empty:
#         df["title_norm"] = df["title"].map(normalize_text)

#     return df


# @st.cache_data
# def load_all_csv():
#     frames = []
#     files = sorted(CSV_DIR.glob("*.csv"))

#     for path in files:
#         try:
#             df = pd.read_csv(path)
#             df["__source_file"] = path.name
#             frames.append(df)
#         except Exception:
#             pass

#     if not frames:
#         return pd.DataFrame()

#     df = pd.concat(frames, ignore_index=True)
#     df.columns = df.columns.str.strip()

#     if "Title" in df.columns:
#         df["title_norm"] = df["Title"].map(normalize_text)

#     return df


# # =========================================================
# # LOAD DATA
# # =========================================================

# json_df = load_all_json()
# csv_df = load_all_csv()

# if json_df.empty:
#     st.warning("No valid JSON registry files found.")
#     st.stop()

# if csv_df.empty:
#     st.warning("No CSV files found in data/csv.")
#     st.stop()

# # =========================================================
# # MATCH JSON ↔ CSV
# # =========================================================

# merged = json_df.merge(
#     csv_df,
#     on="title_norm",
#     how="left",
#     suffixes=("_json", "_csv")
# )

# matched = merged[merged["Title"].notna()]
# unmatched = merged[merged["Title"].isna()]

# # =========================================================
# # JOURNAL COVERAGE ANALYSIS
# # =========================================================

# if "Journal" in csv_df.columns:
#     all_journals = (
#         csv_df["Journal"]
#         .dropna()
#         .astype(str)
#         .str.strip()
#     )

#     referenced_journals = (
#         matched["Journal"]
#         .dropna()
#         .astype(str)
#         .str.strip()
#     )

#     missing_journals = sorted(
#         set(all_journals) - set(referenced_journals)
#     )

#     missing_journal_df = (
#         csv_df[csv_df["Journal"].isin(missing_journals)]
#         .groupby("Journal")
#         .agg(
#             paper_count=("Title", "count"),
#             examples=("Title", lambda x: ", ".join(x.head(3)))
#         )
#         .reset_index()
#         .sort_values("paper_count", ascending=False)
#     )

# else:
#     missing_journal_df = pd.DataFrame()

# # =========================================================
# # UI TABS
# # =========================================================

# tab1, tab2, tab3 = st.tabs([
#     "🔗 Matched References",
#     "❌ Unmatched JSON References",
#     "📉 Missing Journal Coverage"
# ])

# # =========================================================
# # TAB 1 — MATCHED
# # =========================================================

# with tab1:
#     st.subheader("🔗 JSON References Matched with CSV Database")

#     st.caption(f"Matched references: {len(matched)}")

#     show_cols = [
#         "registry_file",
#         "objective_layer",
#         "title_json",
#         "Journal",
#         "Year",
#         "DOI",
#         "__source_file",
#         "relevance",
#     ]

#     available_cols = [c for c in show_cols if c in matched.columns]

#     st.dataframe(
#         matched[available_cols],
#         use_container_width=True,
#         height=520
#     )

# # =========================================================
# # TAB 2 — UNMATCHED
# # =========================================================

# with tab2:
#     st.subheader("❌ JSON References Not Found in CSV Database")

#     st.caption(f"Unmatched references: {len(unmatched)}")

#     st.dataframe(
#         unmatched[
#             ["registry_file", "objective_layer", "title_json", "authors", "relevance"]
#         ],
#         use_container_width=True,
#         height=520
#     )

#     st.warning(
#         "These titles may have spelling differences, missing records, "
#         "or require manual reconciliation."
#     )

# # =========================================================
# # TAB 3 — MISSING JOURNALS
# # =========================================================

# with tab3:
#     st.subheader("📉 Journals Present in CSV but NOT Referenced in JSON")

#     if missing_journal_df.empty:
#         st.success("🎉 All journals in CSV are covered by registry references!")
#     else:
#         st.caption(f"Missing journals: {len(missing_journal_df)}")

#         st.dataframe(
#             missing_journal_df,
#             use_container_width=True,
#             height=520
#         )

#         csv_bytes = missing_journal_df.to_csv(index=False).encode("utf-8")

#         st.download_button(
#             "⬇️ Download Missing Journal Report",
#             data=csv_bytes,
#             file_name="missing_journals.csv",
#             mime="text/csv"
#         )
