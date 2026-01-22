import streamlit as st
import pandas as pd
import json
from pathlib import Path
import hashlib
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📚 Literature Category Mapper",
    layout="wide"
)

st.title("📚 Literature Category Mapper")
st.caption("Deterministic keyword clustering + manual overrides + audit logging")

# =========================================================
# SESSION STATE INIT
# =========================================================

if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None

if "edited_df" not in st.session_state:
    st.session_state.edited_df = None

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MAPPING_FILE = DATA_DIR / "mapping.json"
OVERRIDE_FILE = DATA_DIR / "overrides.json"
OVERRIDE_LOG_FILE = DATA_DIR / "override_logs.jsonl"

REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
CSV_DIR = BASE_DIR / "data" / "csv"

REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# SAFETY INIT
# =========================================================

if not MAPPING_FILE.exists():
    st.error(f"❌ mapping.json not found at: {MAPPING_FILE}")
    st.stop()

if not OVERRIDE_FILE.exists():
    OVERRIDE_FILE.write_text("{}")

if not OVERRIDE_LOG_FILE.exists():
    OVERRIDE_LOG_FILE.write_text("")

# =========================================================
# UTILITIES
# =========================================================

def normalize(text: str) -> str:
    return str(text).lower().strip()


def record_hash(record: dict) -> str:
    raw = f"{record.get('title','')}||{record.get('abstract','')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def load_mapping() -> dict:
    return json.loads(MAPPING_FILE.read_text())


def save_mapping(mapping: dict):
    MAPPING_FILE.write_text(json.dumps(mapping, indent=2))


def load_overrides() -> dict:
    try:
        return json.loads(OVERRIDE_FILE.read_text())
    except Exception:
        return {}


def save_overrides(overrides: dict):
    OVERRIDE_FILE.write_text(json.dumps(overrides, indent=2))


def append_override_log(entry: dict):
    with OVERRIDE_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# =========================================================
# 🔑 KEYWORD-BASED CLUSTERING (SIMPLIFIED)
# =========================================================

def classify_text(text: str, mapping: dict):
    """
    Each category in mapping.json is treated as a cluster.
    If any keyword appears in text → that category matches.
    """

    text_norm = normalize(text)
    matched_categories = []
    matched_keywords = []

    for category, keywords in mapping.items():
        for kw in keywords:
            kw_norm = normalize(kw)
            if kw_norm and kw_norm in text_norm:
                matched_categories.append(category)
                matched_keywords.append(kw)
                break   # only one keyword needed per category

    if len(matched_categories) == 1:
        return matched_categories[0], ", ".join(matched_keywords)

    elif len(matched_categories) > 1:
        return "MULTI_MATCH", ", ".join(matched_keywords)

    else:
        return "Uncategorized", ""


def batch_classify(records, mapping):
    overrides = load_overrides()
    rows = []

    for r in records:
        rid = record_hash(r)

        # Manual override always wins
        if rid in overrides:
            final_category = overrides[rid]["final_category"]
            matched_keywords = "MANUAL_OVERRIDE"
        else:
            final_category, matched_keywords = classify_text(
                r["text"], mapping
            )

        rows.append({
            "record_id": rid,
            "source_title": r.get("title", ""),
            "source_abstract": r.get("abstract", ""),
            "input_text_preview": r["text"][:200],
            "predicted_category": final_category,
            "matched_keywords": matched_keywords,
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
# LOAD UNIQUE MATCHED REFERENCES
# =========================================================

@st.cache_data(show_spinner=False)
def load_unique_matched(_json_fp: str, _csv_fp: str):

    def normalize_text(x):
        return str(x).strip().lower()

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

st.sidebar.header("🛠 Category Mapping")

selected_category = st.sidebar.selectbox(
    "Select category",
    list(mapping.keys()),
    key="category_selector"
)

keywords_text = st.sidebar.text_area(
    "Keywords (comma separated)",
    value=", ".join(mapping[selected_category]),
    height=160
)

if st.sidebar.button("💾 Save Keywords"):
    mapping[selected_category] = [
        k.strip() for k in keywords_text.split(",") if k.strip()
    ]
    save_mapping(mapping)
    st.sidebar.success("Saved to mapping.json")

st.sidebar.divider()

new_category = st.sidebar.text_input("➕ New Category Name")

if st.sidebar.button("Add Category"):
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
    horizontal=True
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

run_btn = st.button("🚀 Classify")

if run_btn and records:
    st.session_state.last_result_df = batch_classify(records, mapping)
    st.session_state.edited_df = st.session_state.last_result_df.copy()

# =========================================================
# DISPLAY RESULTS
# =========================================================

if st.session_state.edited_df is not None:

    st.success(f"Loaded {len(st.session_state.edited_df)} records")

    st.subheader("✍️ Manual Override")

    st.session_state.edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True
    )

    # ---------------- SAVE OVERRIDES ----------------

    if st.button("💾 Save Overrides"):

        overrides = load_overrides()
        now = datetime.utcnow().isoformat()

        for _, row in st.session_state.edited_df.iterrows():

            rid = row["record_id"]
            new_cat = row["predicted_category"]
            old_cat = overrides.get(rid, {}).get("final_category")

            if old_cat != new_cat:

                overrides[rid] = {
                    "source_title": row["source_title"],
                    "source_abstract": row["source_abstract"],
                    "final_category": new_cat,
                    "updated_at": now
                }

                append_override_log({
                    "timestamp": now,
                    "record_id": rid,
                    "old_category": old_cat,
                    "new_category": new_cat,
                    "reason": "manual_override"
                })

        save_overrides(overrides)
        st.success("✅ Overrides saved and logged.")

    # ---------------- EXPORT ----------------

    st.subheader("📤 Export")

    csv_data = st.session_state.edited_df.to_csv(index=False).encode("utf-8")
    json_data = st.session_state.edited_df.to_json(orient="records", indent=2).encode("utf-8")

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

# =========================================================
# AUDIT LOG VIEWER
# =========================================================

with st.expander("📜 View Override Audit Log"):
    if OVERRIDE_LOG_FILE.exists():
        logs = OVERRIDE_LOG_FILE.read_text().strip().splitlines()
        if logs:
            log_rows = [json.loads(x) for x in logs[-200:]]
            st.dataframe(pd.DataFrame(log_rows), use_container_width=True)
        else:
            st.info("No override logs yet.")
