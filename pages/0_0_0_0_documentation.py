import streamlit as st
import re
from pathlib import Path

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(page_title="📘 Application Documentation", layout="wide")
st.title("📘 Application Documentation")
st.caption("Automatically generated from page_doc(...) blocks")

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DOC_DIR = BASE_DIR / "data" / "documentation"
RAW_PATH = DOC_DIR / "raw_page_docs.txt"
OUT_PATH = DOC_DIR / "pages_overview.md"

DOC_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# Regex for page_doc blocks
# -------------------------------------------------
BLOCK_RE = re.compile(
    r"page_doc\s*\(\s*"
    r"title=\"\"\"(.*?)\"\"\"\s*,\s*"
    r"file=\"\"\"(.*?)\"\"\"\s*,\s*"
    r"purpose=\"\"\"(.*?)\"\"\"\s*,\s*"
    r"inputs=\"\"\"(.*?)\"\"\"\s*,\s*"
    r"outputs=\"\"\"(.*?)\"\"\"\s*,\s*"
    r"when_to_use=\"\"\"(.*?)\"\"\"\s*"
    r"\)",
    re.DOTALL,
)

# -------------------------------------------------
# Auto-build Markdown if raw exists
# -------------------------------------------------
def build_docs(raw_text: str) -> str:
    matches = BLOCK_RE.findall(raw_text)

    if not matches:
        return None

    md = ["# 📘 Application Page Documentation\n"]

    for title, file, purpose, inputs, outputs, when in matches:
        md.append(f"## 📄 {title}\n")
        md.append(f"**File:** `{file}`\n")
        md.append("**Purpose**  \n" + purpose + "\n")
        md.append("**Inputs**  \n" + inputs + "\n")
        md.append("**Outputs / Visuals**  \n" + outputs + "\n")
        md.append("**When to use**  \n" + when + "\n")
        md.append("---\n")

    return "\n".join(md)


# -------------------------------------------------
# Processing Logic
# -------------------------------------------------
if RAW_PATH.exists():
    raw_text = RAW_PATH.read_text(encoding="utf-8")

    md = build_docs(raw_text)

    if md:
        # write/update markdown automatically
        OUT_PATH.write_text(md, encoding="utf-8")
        st.success("✅ Documentation auto-generated from raw_page_docs.txt")
    else:
        st.error("⚠️ raw_page_docs.txt found but no valid page_doc blocks detected.")
else:
    st.warning("ℹ️ No raw_page_docs.txt found. Paste NotebookLM output into that file.")

# -------------------------------------------------
# Display Documentation
# -------------------------------------------------
if OUT_PATH.exists():
    st.markdown("---")
    st.markdown(OUT_PATH.read_text(encoding="utf-8"))
else:
    st.info("Documentation file not yet generated.")


# page_doc(
#     title="""Research Landscape Explorer""",
#     file="""app.py""",
#     purpose="""Acts as the central dashboard to visualize academic metadata using knowledge maps, word cloud analysis, and bibliometrics to compare journals and conference papers.""",
#     inputs="""Academic metadata from WoS, Scopus, OpenAlex, or Semantic Scholar in CSV/JSON format.""",
#     outputs="""Interactive word clouds, keyword co-occurrence knowledge graphs, and temporal topic evolution charts.""",
#     when_to_use="""Exploration and PRISMA-adjacent systematic landscape analysis."""
# )

# page_doc(
#     title="""PhD Mapping and Project Traceability""",
#     file="""pages/01_PhD_Mapping.py""",
#     purpose="""Visualizes the flow between high-level research themes, specific research questions, and individual research papers using a multi-layer Sankey structure.""",
#     inputs="""Research themes, research questions, and project target lists (Paper 1-4).""",
#     outputs="""Plotly-based Sankey diagrams illustrating methodological convergence and justified divergence.""",
#     when_to_use="""Research design, project exploration, and proposal writing."""
# )

# page_doc(
#     title="""NotebookLM Prompt Orchestrator""",
#     file="""pages/03_NotebookLM_Master.py""",
#     purpose="""Orchestrates the synthesis process by grouping relevant research papers by batch_id to generate structured prompts for the NotebookLM synthesis engine.""",
#     inputs="""CSV data containing paper references and batch identifiers.""",
#     outputs="""Ready-to-paste prompts tailored for batch-wise research synthesis.""",
#     when_to_use="""Preprocessing and prompt engineering for synthesis tasks."""
# )

# page_doc(
#     title="""LaTeX Build and Aux Analysis""",
#     file="""pages/05_aux.py""",
#     purpose="""Analyzes LaTeX build logs and auxiliary files to provide debugging insights and document structural verification.""",
#     inputs="""LaTeX .log files, stdout.txt, and .aux files.""",
#     outputs="""Highlighted lists of errors, warnings, overfull boxes, and parsed tables of document labels and citations.""",
#     when_to_use="""Debugging and document verification during the reporting phase."""
# )

# page_doc(
#     title="""LaTeX Converter with Hallucination Mitigation""",
#     file="""pages/08_latex_converter_with_hallucination_mitigation.py""",
#     purpose="""Transforms generated research content into LaTeX format while implementing validation checks to ensure citation accuracy and reduce model hallucinations.""",
#     inputs="""Raw research text and associated BibTeX citation keys.""",
#     outputs="""Validated, LaTeX-ready .tex files with grounded citations.""",
#     when_to_use="""Reporting and final assembly with quality control."""
# )

# page_doc(
#     title="""ACL Anthology BibTeX Linker""",
#     file="""pages/10_acl_anthology.py""",
#     purpose="""Parses extracted volume links from the ACL Anthology and converts them into standardized BibTeX download URLs.""",
#     inputs="""extracted.json from ACL Anthology venue data.""",
#     outputs="""Searchable tables of volume titles, original paths, and functional BibTeX URLs for bulk download list generation.""",
#     when_to_use="""Literature search and bibliographic data gathering."""
# )

# page_doc(
#     title="""ACL Volume Bib Downloader""",
#     file="""pages/12_ACL_Volume_Bib_Downloader.py""",
#     purpose="""Performs automated batch retrieval of BibTeX files for identified ACL Anthology volumes to populate local research databases.""",
#     inputs="""Generated lists of ACL BibTeX download URLs.""",
#     outputs="""Local .bib files stored in the data/acl_anthology/ directory and success/failure logs.""",
#     when_to_use="""Data acquisition and bibliographic preprocessing."""
# )

# page_doc(
#     title="""Keyword Co-occurrence Analysis""",
#     file="""pipeline/cooccurrence.py""",
#     purpose="""Processes cleaned academic metadata to calculate relationship strengths between keywords for knowledge mapping.""",
#     inputs="""Cleaned and normalized keyword data from the research pipeline.""",
#     outputs="""Relationship matrices and edge data for network visualization.""",
#     when_to_use="""Preprocessing and intermediate modeling stage."""
# )

# page_doc(
#     title="""Interactive Network Visualization""",
#     file="""viz/network.py""",
#     purpose="""Generates interactive graphical representations of research keyword relationships to identify thematic clusters.""",
#     inputs="""Co-occurrence data and node-edge relationship matrices.""",
#     outputs="""Interactive Plotly or NetworkX visualizations of knowledge graphs.""",
#     when_to_use="""Exploration and thematic evaluation."""
# )