import streamlit as st
import json
import re
from datetime import datetime
from pathlib import Path
import uuid

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(layout="wide")
st.title("🧩 Research Sections → JSON Parser & Store")

# st.markdown("""
# Paste structured research text (Objectives, Research Gap, Problem Statement, etc.).
# The app will parse, normalize, store, and let you browse previous results.
# """)

st.markdown("""
Paste structured research text (Objectives, Research Gap, Problem Statement, etc.).
The app will automatically parse and normalize it into JSON https://notebooklm.google.com/notebook/d3a32650-daba-4530-b769-0091ecba58a8 https://chatgpt.com/c/697726ec-959c-8330-a9ac-9a29c0a0ed57.
""")

# =========================
# STORAGE CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs" / "parsed_json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# CONSTANTS
# =========================

SECTION_MAP = {
    "🎯 Objectives": "objectives",
    "🔍 Research Gap": "research_gap",
    "🧩 Problem Statement": "problem_statement",
    "❓ Research Questions": "research_questions",
    "🧪 Hypotheses": "hypotheses",
    "🏆 Expected Contributions": "expected_contributions",
}

# =========================
# PARSER FUNCTIONS
# =========================

def split_sections(text: str):
    pattern = "(" + "|".join(map(re.escape, SECTION_MAP.keys())) + ")"
    parts = re.split(pattern, text)

    sections = {}
    current_header = None

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part in SECTION_MAP:
            current_header = SECTION_MAP[part]
            sections[current_header] = ""
        elif current_header:
            sections[current_header] += part + "\n"

    return sections


def normalize_lines(block: str):
    lines = []
    for line in block.split("\n"):
        line = line.strip("•-* \t")
        if len(line) > 2:
            lines.append(line)
    return lines


def parse_structured_sections(sections: dict):
    parsed = {}

    # Simple lists
    for key in ["objectives", "research_gap", "problem_statement"]:
        parsed[key] = normalize_lines(sections.get(key, ""))

    # Research Questions
    parsed["research_questions"] = []
    for line in normalize_lines(sections.get("research_questions", "")):
        m = re.match(r"(RQ\d+)\s*:\s*(.*)", line)
        parsed["research_questions"].append({
            "id": m.group(1) if m else None,
            "text": m.group(2).strip() if m else line
        })

    # Hypotheses
    parsed["hypotheses"] = []
    for line in normalize_lines(sections.get("hypotheses", "")):
        m = re.match(r"(H\d+)\s*:\s*(.*)", line)
        parsed["hypotheses"].append({
            "id": m.group(1) if m else None,
            "text": m.group(2).strip() if m else line
        })

    # Expected Contributions
    parsed["expected_contributions"] = []
    for line in normalize_lines(sections.get("expected_contributions", "")):
        m = re.match(r"([A-Za-z ]+)\s*:\s*(.*)", line)
        parsed["expected_contributions"].append({
            "type": m.group(1).strip() if m else None,
            "text": m.group(2).strip() if m else line
        })

    parsed["metadata"] = {
        "parsed_at": datetime.utcnow().isoformat()
    }

    return parsed


def save_json(data: dict):
    run_id = uuid.uuid4().hex[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"research_parse_{timestamp}_{run_id}.json"
    path = OUTPUT_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path


def load_all_saved():
    return sorted(OUTPUT_DIR.glob("*.json"), reverse=True)


# =========================
# UI LAYOUT
# =========================

tab_parse, tab_history = st.tabs(["📝 Parse New", "📂 History"])

# =========================
# TAB 1 — PARSE NEW
# =========================

with tab_parse:
    raw_text = st.text_area(
        "📄 Paste Research Text",
        height=420,
        placeholder="Paste your research text here..."
    )

    if st.button("🚀 Parse & Store", use_container_width=True):

        if not raw_text.strip():
            st.warning("Please paste some text.")
            st.stop()

        sections = split_sections(raw_text)
        parsed_json = parse_structured_sections(sections)
        output_path = save_json(parsed_json)

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("📦 Parsed JSON")
            st.json(parsed_json)

        with c2:
            st.subheader("💾 Storage Info")
            st.success(f"Saved as: {output_path.name}")
            st.caption(f"Path: {output_path}")

            json_bytes = json.dumps(parsed_json, indent=2).encode("utf-8")
            st.download_button(
                "⬇️ Download JSON",
                json_bytes,
                file_name=output_path.name,
                mime="application/json"
            )

# =========================
# TAB 2 — HISTORY VIEWER
# =========================

with tab_history:
    st.subheader("📂 Stored JSON Files")

    saved_files = load_all_saved()

    if not saved_files:
        st.info("No stored files yet.")
        st.stop()

    selected_file = st.selectbox(
        "Select saved JSON",
        saved_files,
        format_func=lambda p: p.name
    )

    with open(selected_file, encoding="utf-8") as f:
        stored_json = json.load(f)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📦 JSON Preview")
        st.json(stored_json)

    with c2:
        st.subheader("📄 Metadata")
        st.write("Filename:", selected_file.name)
        st.write("Size:", f"{selected_file.stat().st_size / 1024:.1f} KB")
        st.write("Modified:", datetime.fromtimestamp(
            selected_file.stat().st_mtime
        ))

        st.download_button(
            "⬇️ Download Selected",
            json.dumps(stored_json, indent=2).encode("utf-8"),
            file_name=selected_file.name,
            mime="application/json"
        )


# import streamlit as st
# import json
# import re
# from datetime import datetime

# # =========================
# # PAGE CONFIG
# # =========================

# st.set_page_config(layout="wide")
# st.title("🧩 Research Section → JSON Parser")

# st.markdown("""
# Paste structured research text (Objectives, Research Gap, Problem Statement, etc.).
# The app will automatically parse and normalize it into JSON https://notebooklm.google.com/notebook/d3a32650-daba-4530-b769-0091ecba58a8 https://chatgpt.com/c/697726ec-959c-8330-a9ac-9a29c0a0ed57.
# """)

# # =========================
# # INPUT
# # =========================

# raw_text = st.text_area(
#     "📄 Paste Research Text",
#     height=400,
#     placeholder="Paste your text here..."
# )

# # =========================
# # PARSER LOGIC
# # =========================

# SECTION_MAP = {
#     "🎯 Objectives": "objectives",
#     "🔍 Research Gap": "research_gap",
#     "🧩 Problem Statement": "problem_statement",
#     "❓ Research Questions": "research_questions",
#     "🧪 Hypotheses": "hypotheses",
#     "🏆 Expected Contributions": "expected_contributions",
# }

# def split_sections(text: str):
#     """
#     Split text into sections using emoji headers.
#     """
#     pattern = "(" + "|".join(map(re.escape, SECTION_MAP.keys())) + ")"
#     parts = re.split(pattern, text)

#     sections = {}
#     current_header = None

#     for part in parts:
#         part = part.strip()
#         if not part:
#             continue

#         if part in SECTION_MAP:
#             current_header = SECTION_MAP[part]
#             sections[current_header] = ""
#         elif current_header:
#             sections[current_header] += part + "\n"

#     return sections


# def normalize_lines(block: str):
#     """
#     Split block into clean bullet lines.
#     """
#     lines = []
#     for line in block.split("\n"):
#         line = line.strip("•-* \t")
#         if len(line) > 2:
#             lines.append(line)
#     return lines


# def parse_structured_sections(sections: dict):
#     parsed = {}

#     # Objectives, Gap, Problem
#     for key in ["objectives", "research_gap", "problem_statement"]:
#         parsed[key] = normalize_lines(sections.get(key, ""))

#     # Research Questions
#     rq_lines = normalize_lines(sections.get("research_questions", ""))
#     parsed["research_questions"] = []
#     for line in rq_lines:
#         m = re.match(r"(RQ\d+)\s*:\s*(.*)", line)
#         if m:
#             parsed["research_questions"].append({
#                 "id": m.group(1),
#                 "text": m.group(2).strip()
#             })
#         else:
#             parsed["research_questions"].append({
#                 "id": None,
#                 "text": line
#             })

#     # Hypotheses
#     hyp_lines = normalize_lines(sections.get("hypotheses", ""))
#     parsed["hypotheses"] = []
#     for line in hyp_lines:
#         m = re.match(r"(H\d+)\s*:\s*(.*)", line)
#         if m:
#             parsed["hypotheses"].append({
#                 "id": m.group(1),
#                 "text": m.group(2).strip()
#             })
#         else:
#             parsed["hypotheses"].append({
#                 "id": None,
#                 "text": line
#             })

#     # Expected Contributions
#     contrib_lines = normalize_lines(sections.get("expected_contributions", ""))
#     parsed["expected_contributions"] = []
#     for line in contrib_lines:
#         m = re.match(r"([A-Za-z ]+)\s*:\s*(.*)", line)
#         if m:
#             parsed["expected_contributions"].append({
#                 "type": m.group(1).strip(),
#                 "text": m.group(2).strip()
#             })
#         else:
#             parsed["expected_contributions"].append({
#                 "type": None,
#                 "text": line
#             })

#     parsed["metadata"] = {
#         "parsed_at": datetime.utcnow().isoformat()
#     }

#     return parsed


# # =========================
# # PARSE BUTTON
# # =========================

# if st.button("🚀 Parse to JSON"):

#     if not raw_text.strip():
#         st.warning("Please paste some text.")
#         st.stop()

#     sections = split_sections(raw_text)
#     parsed_json = parse_structured_sections(sections)

#     # =========================
#     # DISPLAY
#     # =========================

#     c1, c2 = st.columns(2)

#     with c1:
#         st.subheader("📦 Parsed JSON")
#         st.json(parsed_json)

#     with c2:
#         st.subheader("📋 Section Preview")
#         for k, v in parsed_json.items():
#             if k == "metadata":
#                 continue
#             st.markdown(f"### {k}")
#             if isinstance(v, list):
#                 for item in v:
#                     st.write("•", item)
#             else:
#                 st.write(v)

#     # =========================
#     # DOWNLOAD
#     # =========================

#     json_bytes = json.dumps(parsed_json, indent=2).encode("utf-8")

#     st.download_button(
#         label="⬇️ Download JSON",
#         data=json_bytes,
#         file_name="research_sections.json",
#         mime="application/json"
#     )
