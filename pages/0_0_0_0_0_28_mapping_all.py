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
    page_title="📚 Literature Category Mapper (Aggregated)",
    layout="wide"
)

st.title("📚 Literature Category Mapper")
st.caption("Aggregated CSV → filters → keyword clustering → manual overrides → audit logs")

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
CSV_DIR = DATA_DIR / "csv"
REGISTRY_DIR = DATA_DIR / "research_registry"

MAPPING_FILE = DATA_DIR / "mapping.json"
OVERRIDE_FILE = DATA_DIR / "overrides.json"
OVERRIDE_LOG_FILE = DATA_DIR / "override_logs.jsonl"

for d in [DATA_DIR, CSV_DIR, REGISTRY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

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
    return str(text).strip().lower()


def record_hash(record: dict) -> str:
    raw = f"{record.get('title','')}||{record.get('abstract','')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def directory_fingerprint(path: Path) -> str:
    parts = []
    for p in sorted(path.glob("*")):
        if p.is_file():
            stat = p.stat()
            parts.append(f"{p.name}:{stat.st_mtime_ns}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def normalize_text(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


# =========================================================
# LOADERS (FROM BATCH CURATOR)
# =========================================================

@st.cache_data
def discover_csv_files():
    return sorted(CSV_DIR.glob("*.csv"))


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def load_multiple(files):
    frames = []
    for f in files:
        df = load_csv(f)
        df["__source_file"] = f.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# =========================================================
# SIDEBAR — DATASET SELECTION
# =========================================================

st.sidebar.header("📂 Dataset Selection")

files = discover_csv_files()

if not files:
    st.warning("⚠️ No CSV files found in data/csv/")
    st.stop()

selected_files = st.sidebar.multiselect(
    "Select CSV files to merge",
    files,
    default=files[:1],
    format_func=lambda p: p.name
)

if not selected_files:
    st.info("Please select at least one CSV file.")
    st.stop()

raw_df = load_multiple(selected_files)
st.sidebar.metric("Loaded rows", len(raw_df))

# =========================================================
# SIDEBAR — FILTERS (SIMPLIFIED)
# =========================================================

st.sidebar.divider()
st.sidebar.header("🧪 Filters")

remove_missing_abstract = st.sidebar.checkbox("Remove '(missing abstract)'", True)
remove_empty_title = st.sidebar.checkbox("Remove empty Title", True)
deduplicate = st.sidebar.checkbox("Deduplicate (Title)", True)

min_abstract_len = st.sidebar.slider(
    "Minimum abstract length",
    0, 500, 40
)

# =========================================================
# APPLY FILTERS
# =========================================================

df = raw_df.copy()

if "Abstract" in df.columns and remove_missing_abstract:
    df = df[
        normalize_text(df["Abstract"]) != "(missing abstract)"
    ]

if "Title" in df.columns and remove_empty_title:
    df = df[
        normalize_text(df["Title"]) != ""
    ]

if "Abstract" in df.columns and min_abstract_len > 0:
    df = df[
        df["Abstract"].astype(str).str.len() >= min_abstract_len
    ]

if deduplicate and "Title" in df.columns:
    df["_title_norm"] = normalize_text(df["Title"])
    df = df.drop_duplicates(subset="_title_norm")
    df = df.drop(columns="_title_norm")

st.success(f"Filtered dataset: {len(df)} rows")

st.subheader("🔍 Filtered Preview")
st.dataframe(df.head(200), use_container_width=True)

# =========================================================
# LOAD MAPPING + OVERRIDES
# =========================================================

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


mapping = load_mapping()

# =========================================================
# SIDEBAR — EDIT MAPPING.JSON
# =========================================================

st.sidebar.divider()
st.sidebar.header("🛠 Category Mapping")

selected_category = st.sidebar.selectbox(
    "Select category",
    list(mapping.keys()),
)

keywords_text = st.sidebar.text_area(
    "Keywords (comma separated)",
    value=", ".join(mapping[selected_category]),
    height=140
)

if st.sidebar.button("💾 Save Keywords"):
    mapping[selected_category] = [
        k.strip() for k in keywords_text.split(",") if k.strip()
    ]
    save_mapping(mapping)
    st.sidebar.success("Saved to mapping.json")

# =========================================================
# CLASSIFICATION ENGINE
# =========================================================

def classify_text(text: str, mapping: dict):
    text_norm = normalize(text)
    matched_categories = []
    matched_keywords = []

    for category, keywords in mapping.items():
        for kw in keywords:
            kw_norm = normalize(kw)
            if kw_norm and kw_norm in text_norm:
                matched_categories.append(category)
                matched_keywords.append(kw)
                break

    if len(matched_categories) == 1:
        return matched_categories[0], ", ".join(matched_keywords)
    elif len(matched_categories) > 1:
        return "MULTI_MATCH", ", ".join(matched_keywords)
    else:
        return "Uncategorized", ""


def batch_classify_from_df(df: pd.DataFrame, content_mode: str):

    overrides = load_overrides()
    rows = []

    for _, row in df.iterrows():

        title = str(row.get("Title", ""))
        abstract = str(row.get("Abstract", ""))

        if content_mode == "Title":
            text = title
        elif content_mode == "Abstract":
            text = abstract
        else:
            text = f"{title}. {abstract}"

        record = {
            "title": title,
            "abstract": abstract,
            "text": text
        }

        rid = record_hash(record)

        if rid in overrides:
            final_category = overrides[rid]["final_category"]
            matched_keywords = "MANUAL_OVERRIDE"
        else:
            final_category, matched_keywords = classify_text(text, mapping)

        rows.append({
            "record_id": rid,
            "Title": title,
            "Abstract": abstract,
            "predicted_category": final_category,
            "matched_keywords": matched_keywords,
        })

    return pd.DataFrame(rows)

# =========================================================
# CLASSIFICATION CONTROLS
# =========================================================

st.divider()
st.subheader("🎯 Classification Settings")

content_mode = st.radio(
    "Text used for classification",
    ["Title", "Abstract", "Title + Abstract"],
    horizontal=True
)

run_btn = st.button("🚀 Run Classification", type="primary")

if run_btn and not df.empty:
    st.session_state.last_result_df = batch_classify_from_df(df, content_mode)
    st.session_state.edited_df = st.session_state.last_result_df.copy()

# =========================================================
# RESULTS + MANUAL OVERRIDE
# =========================================================

if st.session_state.edited_df is not None:

    st.success(f"Classified {len(st.session_state.edited_df)} records")

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
