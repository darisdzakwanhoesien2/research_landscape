import streamlit as st
import json
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="JSON → NotebookLM Prompt", layout="wide")
st.title("🧠 JSON → NotebookLM Prompt Generator")
st.caption("Paste JSON or upload JSON file to generate NotebookLM-ready prompts")

# =====================================================
# INPUT MODE
# =====================================================

mode = st.radio(
    "Select JSON Input Method",
    ["Upload JSON File", "Paste JSON Text"],
    horizontal=True
)

json_data = None

# =====================================================
# FILE UPLOAD MODE
# =====================================================

if mode == "Upload JSON File":
    uploaded = st.file_uploader("Upload JSON file", type=["json"])
    if uploaded:
        try:
            json_data = json.load(uploaded)
        except Exception as e:
            st.error(f"Invalid JSON file: {e}")

# =====================================================
# TEXT PASTE MODE
# =====================================================

else:
    json_text = st.text_area(
        "Paste JSON here",
        height=350,
        placeholder="Paste full JSON array here..."
    )
    if json_text.strip():
        try:
            json_data = json.loads(json_text)
        except Exception as e:
            st.error(f"Invalid JSON text: {e}")

# =====================================================
# VALIDATE
# =====================================================

if json_data is None:
    st.info("Provide JSON input to continue.")
    st.stop()

if not isinstance(json_data, list):
    st.error("Expected top-level JSON array: [ {meta, papers}, ... ]")
    st.stop()

if not json_data or "meta" not in json_data[0]:
    st.error("JSON structure not recognized. Expected list of objects with 'meta' and 'papers'.")
    st.stop()

# =====================================================
# SELECT RQ
# =====================================================

rq_titles = [item["meta"].get("research_question", "Untitled RQ") for item in json_data]

selected_idx = st.selectbox(
    "Select Research Question",
    list(range(len(rq_titles))),
    format_func=lambda i: rq_titles[i][:140] + ("..." if len(rq_titles[i]) > 140 else "")
)

rq_block = json_data[selected_idx]
rq_text = rq_block["meta"].get("research_question", "")

# =====================================================
# TEMPLATE BUILDER
# =====================================================

def build_prompt(rq_text):
    now = datetime.utcnow().isoformat() + "Z"

    return f"""✅ ULTRA-CONCISE NOTEBOOKLM PROMPT (JSON ONLY)
Task:
Support a literature review for this RQ:
RQ:
{rq_text}
You are given Markdown with Title, DOI, Abstract.
For each paper, provide:
verified links (DOI, publisher, Semantic Scholar, open PDF if available)
relevance score to RQ
method: Neural | Symbolic | Neuro-symbolic | Hybrid
interpretability mechanisms (rules, constraints, SHAP, symbolic traces, etc.)
regulatory relevance (EU Taxonomy, ESG, finance regulation, auditability, governance)
up to 5 related key references if clearly relevant
Use DOI/title matching. Prefer stable links. Do not hallucinate links.
🔷 OUTPUT — VALID JSON ONLY
{{
  "meta": {{
    "research_question": "{rq_text}",
    "generated_at": "{now}",
    "notes": ""
  }},
  "papers": [
    {{
      "id": "paper_001",
      "input": {{"title": "", "doi": "", "abstract": ""}},
      "relevance_score": 0.0,
      "method_category": "Neural | Symbolic | Neuro-symbolic | Hybrid",
      "interpretability_mechanisms": [],
      "regulatory_relevance": [],
      "external_links": [
        {{"type": "doi|publisher|semantic_scholar|pdf|arxiv|other", "url": "", "source": ""}}
      ],
      "key_contributions": [],
      "decision_trace_support": "none | partial | strong",
      "suggested_citations": [
        {{"title": "", "reason": "", "link": ""}}
      ]
    }}
  ]
}}
"""

prompt_text = build_prompt(rq_text)

# =====================================================
# OUTPUT
# =====================================================

st.subheader("📝 NotebookLM Prompt")

st.code(prompt_text, language="json")

# =====================================================
# DOWNLOAD
# =====================================================

safe_name = f"notebooklm_prompt_rq_{selected_idx+1}.txt"

st.download_button(
    "⬇️ Download Prompt",
    data=prompt_text.encode("utf-8"),
    file_name=safe_name,
    mime="text/plain"
)

# =====================================================
# DEBUG VIEW (OPTIONAL)
# =====================================================

with st.expander("🔍 View Parsed JSON Block"):
    st.json(rq_block)
