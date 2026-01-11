import streamlit as st
import json
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="JSON → NotebookLM Prompt", layout="wide")
st.title("🧠 JSON → NotebookLM Prompt Generator")
st.caption("Convert structured literature-review JSON into NotebookLM-ready prompt template")

# =====================================================
# UPLOAD JSON
# =====================================================

uploaded = st.file_uploader(
    "Upload JSON file (RQ → papers structure)",
    type=["json"]
)

if not uploaded:
    st.info("Upload the JSON generated from your literature mapping step.")
    st.stop()

# =====================================================
# LOAD JSON
# =====================================================

try:
    data = json.load(uploaded)
except Exception as e:
    st.error(f"Invalid JSON: {e}")
    st.stop()

if not isinstance(data, list):
    st.error("Expected a list of research-question objects.")
    st.stop()

# =====================================================
# SELECT RQ
# =====================================================

rq_titles = [d["meta"]["research_question"] for d in data]

selected_idx = st.selectbox(
    "Select Research Question to Generate Prompt",
    range(len(rq_titles)),
    format_func=lambda i: rq_titles[i][:120] + ("..." if len(rq_titles[i]) > 120 else "")
)

rq_block = data[selected_idx]
rq_text = rq_block["meta"]["research_question"]

# =====================================================
# TEMPLATE BUILDER
# =====================================================

def build_prompt(rq_text):
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
    "generated_at": "{datetime.utcnow().isoformat()}Z",
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

st.subheader("📝 NotebookLM Prompt Output")

st.code(prompt_text, language="json")

# =====================================================
# DOWNLOAD
# =====================================================

file_safe = f"notebooklm_prompt_rq_{selected_idx+1}.txt"

st.download_button(
    "⬇️ Download Prompt",
    data=prompt_text.encode("utf-8"),
    file_name=file_safe,
    mime="text/plain"
)
