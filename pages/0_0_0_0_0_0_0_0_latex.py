import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(layout="wide")
st.title("🧭 Transitional Research Dashboard (Phase 1–3)")

# =========================
# STORAGE
# =========================

BASE_DIR = Path(__file__).resolve().parents[1]
PHASE_DIR = BASE_DIR / "outputs" / "phases"
LATEX_DIR = BASE_DIR / "outputs" / "latex"

PHASE_DIR.mkdir(parents=True, exist_ok=True)
LATEX_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# DEFAULT PHASE CONTENT
# =========================

DEFAULT_PHASES = {
    "Phase 1": {
        "title": "Constraint-Aware Extraction of ESG Claims",
        "objectives": [
            "Build XBRL ingestion pipeline with taxonomy normalization.",
            "Fine-tune FinBERT for performative vs actionable ESG claims.",
            "Measure extraction reliability under structured noise."
        ],
        "research_gap": [
            "No validated extraction pipelines exist for hierarchical financial filings."
        ],
        "problem_statement": [
            "NLP systems cannot reliably validate extracted claims against financial structure."
        ],
        "research_questions": [
            "What extraction accuracy is achievable on XBRL-derived text?",
            "How sensitive is extraction to structural normalization errors?"
        ],
        "hypotheses": [
            "Domain adaptation improves macro-F1 by ≥10%.",
            "Structural noise degrades extraction nonlinearly."
        ],
        "expected_contributions": [
            "Verified XBRL extraction pipeline.",
            "Constraint violation detection benchmark."
        ]
    },

    "Phase 2": {
        "title": "Neurosymbolic Regulatory Constraint Enforcement",
        "objectives": [
            "Design regulatory ontology.",
            "Enforce logical consistency over neural predictions.",
            "Quantify violation reduction."
        ],
        "research_gap": [
            "Neural models lack formal constraint validation mechanisms."
        ],
        "problem_statement": [
            "Statistical predictions violate regulatory consistency rules."
        ],
        "research_questions": [
            "How often do unconstrained models violate regulations?",
            "Can constraints reduce violations without accuracy loss?"
        ],
        "hypotheses": [
            "Constraint enforcement reduces violations by ≥30%."
        ],
        "expected_contributions": [
            "Neurosymbolic reasoning prototype.",
            "Formal regulatory constraint ontology."
        ]
    },

    "Phase 3": {
        "title": "Cost-Aware Multilingual Verification Agents",
        "objectives": [
            "Implement confidence-aware retrieval controller.",
            "Evaluate multilingual transfer to Arabic and Finnish.",
            "Optimize retrieval cost vs accuracy."
        ],
        "research_gap": [
            "Verification systems lack cost-aware reasoning strategies."
        ],
        "problem_statement": [
            "Multilingual verification pipelines are expensive and opaque."
        ],
        "research_questions": [
            "How much retrieval cost reduction is achievable?",
            "How stable is reasoning transfer across languages?"
        ],
        "hypotheses": [
            "Adaptive retrieval reduces cost by ≥40% without accuracy loss."
        ],
        "expected_contributions": [
            "Cost-aware verification agent.",
            "Multilingual audit benchmark."
        ]
    }
}

# =========================
# UTILITIES
# =========================

def save_phase(name, data):
    path = PHASE_DIR / f"{name.replace(' ', '_').lower()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_phase(name):
    path = PHASE_DIR / f"{name.replace(' ', '_').lower()}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_PHASES[name]


def latex_escape(text: str):
    replacements = {
        "&": "\\&", "%": "\\%", "$": "\\$", "#": "\\#",
        "_": "\\_", "{": "\\{", "}": "\\}", "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def generate_latex(phases: dict):
    lines = [
        "\\documentclass{article}",
        "\\usepackage[margin=1in]{geometry}",
        "\\usepackage{hyperref}",
        "\\title{Transitional Research Plan}",
        "\\date{}",
        "\\begin{document}",
        "\\maketitle"
    ]

    for phase_name, phase in phases.items():
        lines.append(f"\\section{{{latex_escape(phase_name)}: {latex_escape(phase['title'])}}}")

        for section in [
            "objectives",
            "research_gap",
            "problem_statement",
            "research_questions",
            "hypotheses",
            "expected_contributions"
        ]:
            pretty = section.replace("_", " ").title()
            lines.append(f"\\subsection{{{latex_escape(pretty)}}}")
            lines.append("\\begin{itemize}")
            for item in phase.get(section, []):
                lines.append(f"  \\item {latex_escape(item)}")
            lines.append("\\end{itemize}")

    lines.append("\\end{document}")
    return "\n".join(lines)

# =========================
# UI
# =========================

tabs = st.tabs(["📘 Phase 1", "📙 Phase 2", "📕 Phase 3", "📤 Export"])

edited_phases = {}

for idx, phase_name in enumerate(["Phase 1", "Phase 2", "Phase 3"]):
    with tabs[idx]:
        st.subheader(phase_name)

        phase_data = load_phase(phase_name)

        title = st.text_input("Title", phase_data["title"], key=f"{phase_name}_title")

        def edit_list(label, items, key):
            text = st.text_area(
                label,
                value="\n".join(items),
                height=140,
                key=key
            )
            return [x.strip() for x in text.split("\n") if x.strip()]

        objectives = edit_list("🎯 Objectives", phase_data["objectives"], f"{phase_name}_obj")
        research_gap = edit_list("🔍 Research Gap", phase_data["research_gap"], f"{phase_name}_gap")
        problem_statement = edit_list("🧩 Problem Statement", phase_data["problem_statement"], f"{phase_name}_prob")
        research_questions = edit_list("❓ Research Questions", phase_data["research_questions"], f"{phase_name}_rq")
        hypotheses = edit_list("🧪 Hypotheses", phase_data["hypotheses"], f"{phase_name}_hyp")
        contributions = edit_list("🏆 Expected Contributions", phase_data["expected_contributions"], f"{phase_name}_contrib")

        updated = {
            "title": title,
            "objectives": objectives,
            "research_gap": research_gap,
            "problem_statement": problem_statement,
            "research_questions": research_questions,
            "hypotheses": hypotheses,
            "expected_contributions": contributions,
            "updated_at": datetime.utcnow().isoformat()
        }

        edited_phases[phase_name] = updated

        if st.button(f"💾 Save {phase_name}", use_container_width=True):
            path = save_phase(phase_name, updated)
            st.success(f"Saved to {path.name}")

# =========================
# EXPORT TAB
# =========================

with tabs[3]:
    st.subheader("📤 Export Research Plan to LaTeX")

    selected = st.multiselect(
        "Select phases to export",
        ["Phase 1", "Phase 2", "Phase 3"],
        default=["Phase 1", "Phase 2", "Phase 3"]
    )

    if st.button("🧾 Generate LaTeX", use_container_width=True):
        export_phases = {k: edited_phases[k] for k in selected}

        latex_text = generate_latex(export_phases)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        tex_path = LATEX_DIR / f"research_plan_{timestamp}.tex"

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_text)

        st.success(f"LaTeX generated: {tex_path.name}")

        st.download_button(
            "⬇️ Download LaTeX",
            latex_text.encode("utf-8"),
            file_name=tex_path.name,
            mime="text/plain"
        )

        st.code(latex_text, language="latex")
