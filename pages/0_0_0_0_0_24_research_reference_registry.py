import json
import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📚 Research Reference Registry",
    layout="wide"
)

st.title("📚 Research Reference Registry")
st.caption("Store, validate, visualize and audit structured research reference mappings")

# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_DIR = BASE_DIR / "data" / "research_registry"
LOG_FILE = REGISTRY_DIR / "registry_log.csv"

REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

st.sidebar.caption(f"📁 Registry Folder: `{REGISTRY_DIR}`")

# =========================================================
# UTILITIES
# =========================================================

def discover_registry_files():
    return sorted(REGISTRY_DIR.glob("*.json"))


def safe_load_json(path: Path):
    """
    Safely load JSON file. Never crash.
    """
    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return {}, "⚠️ File is empty"
        return json.loads(text), None
    except Exception as e:
        return {}, f"❌ Invalid JSON: {e}"


def save_json(data: dict, filename: str):
    path = REGISTRY_DIR / filename
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return path


def append_log(action, filename, note=""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "filename": filename,
        "note": note,
    }

    df = pd.DataFrame([entry])

    if LOG_FILE.exists():
        old = pd.read_csv(LOG_FILE)
        df = pd.concat([old, df], ignore_index=True)

    df.to_csv(LOG_FILE, index=False)


def validate_json(text):
    try:
        obj = json.loads(text)
        return obj, None
    except Exception as e:
        return None, str(e)


def flatten_reference_json(data: dict) -> pd.DataFrame:
    """
    Convert research_plan_references into tabular structure.
    """
    rows = []

    root = data.get("research_plan_references", {})
    if not isinstance(root, dict):
        return pd.DataFrame()

    for layer_key, layer in root.items():
        focus = layer.get("focus", "")
        elements = layer.get("plan_elements", {})
        contributions = ", ".join(elements.get("contributions", []))
        rqs = ", ".join(elements.get("research_questions", []))

        for ref in layer.get("literature_references", []):
            rows.append({
                "objective_layer": layer_key,
                "focus": focus,
                "contributions": contributions,
                "research_questions": rqs,
                "title": ref.get("title"),
                "authors": ref.get("authors"),
                "source_index": ref.get("source_index"),
                "relevance": ref.get("relevance"),
            })

    return pd.DataFrame(rows)


# =========================================================
# SIDEBAR – REGISTRY NAVIGATION
# =========================================================

st.sidebar.header("📂 Registry")

files = discover_registry_files()

selected_file = st.sidebar.selectbox(
    "Select registry file",
    ["(New Document)"] + [f.name for f in files]
)

# =========================================================
# LOAD EXISTING OR INIT
# =========================================================

current_data = {}
current_filename = None
load_warning = None

if selected_file != "(New Document)":
    path = REGISTRY_DIR / selected_file
    current_filename = selected_file
    current_data, load_warning = safe_load_json(path)

# =========================================================
# MAIN UI
# =========================================================

tab_edit, tab_view, tab_table, tab_log = st.tabs(
    ["✏️ Editor", "🔍 JSON Viewer", "📊 Table View", "📜 History"]
)

# =========================================================
# ✏️ EDITOR TAB
# =========================================================

with tab_edit:

    st.subheader("📝 JSON Editor")

    if load_warning:
        st.warning(load_warning)

    default_text = (
        json.dumps(current_data, indent=2, ensure_ascii=False)
        if current_data else
        "{\n  \n}"
    )

    json_text = st.text_area(
        "Edit JSON",
        value=default_text,
        height=480
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        filename_input = st.text_input(
            "Filename",
            value=current_filename or f"research_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

    with col2:
        note = st.text_input("Change note")

    with col3:
        overwrite = st.checkbox("Overwrite existing", value=False)

    if st.button("💾 Save JSON", type="primary"):
        parsed, error = validate_json(json_text)

        if error:
            st.error(f"Invalid JSON: {error}")
            st.stop()

        if not filename_input.endswith(".json"):
            st.warning("Filename must end with .json")
            st.stop()

        target_path = REGISTRY_DIR / filename_input

        if target_path.exists() and not overwrite:
            st.error("File already exists. Enable overwrite to replace.")
            st.stop()

        existed_before = target_path.exists()
        save_json(parsed, filename_input)

        action = "overwrite" if existed_before else "create"
        append_log(action, filename_input, note)

        st.success(f"Saved: {filename_input}")
        st.rerun()

# =========================================================
# 🔍 JSON VIEWER TAB
# =========================================================

with tab_view:

    st.subheader("📖 Raw JSON Viewer")

    if not current_data:
        st.info("No JSON loaded.")
    else:
        st.json(current_data, expanded=True)

# =========================================================
# 📊 TABLE VIEW TAB (NEW)
# =========================================================

with tab_table:

    st.subheader("📊 Literature Reference Table")

    if not current_data:
        st.info("No JSON loaded.")
        st.stop()

    table_df = flatten_reference_json(current_data)

    if table_df.empty:
        st.warning("JSON structure does not contain recognizable literature references.")
        st.stop()

    # Search
    search = st.text_input("🔎 Search (title / relevance / authors)")

    if search.strip():
        mask = (
            table_df["title"].astype(str).str.contains(search, case=False) |
            table_df["authors"].astype(str).str.contains(search, case=False) |
            table_df["relevance"].astype(str).str.contains(search, case=False)
        )
        table_df = table_df[mask]

    st.dataframe(
        table_df,
        use_container_width=True,
        height=520
    )

    st.caption(f"Rows: {len(table_df)}")

    # Optional export
    csv_bytes = table_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Table CSV",
        data=csv_bytes,
        file_name="reference_table.csv",
        mime="text/csv"
    )

# =========================================================
# 📜 HISTORY TAB
# =========================================================

with tab_log:

    st.subheader("📜 Registry History")

    if not LOG_FILE.exists():
        st.info("No history yet.")
    else:
        log_df = pd.read_csv(LOG_FILE)

        st.dataframe(
            log_df.sort_values("timestamp", ascending=False),
            use_container_width=True,
            height=450
        )

        csv_bytes = log_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Log CSV",
            csv_bytes,
            file_name="registry_log.csv",
            mime="text/csv"
        )
