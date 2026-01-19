import streamlit as st
from pathlib import Path
import re

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="LaTeX Build Inspector",
    layout="wide"
)

st.title("📄 LaTeX Output Inspector")
st.caption("Visualize LaTeX stdout logs and AUX metadata")

DATA_DIR = Path("data/latex")

# =====================================
# SIDEBAR — SOURCE SELECTION
# =====================================
st.sidebar.header("📥 Input Source")

mode = st.sidebar.radio(
    "Choose input method",
    ["Upload files", "Load from data/latex/"]
)

stdout_text = None
aux_text = None

# =====================================
# FILE LOADING
# =====================================
if mode == "Upload files":
    stdout_file = st.sidebar.file_uploader(
        "Upload LaTeX stdout / log file",
        type=["txt", "log"]
    )
    aux_file = st.sidebar.file_uploader(
        "Upload .aux file",
        type=["aux", "txt"]
    )

    if stdout_file:
        stdout_text = stdout_file.read().decode("utf-8", errors="ignore")

    if aux_file:
        aux_text = aux_file.read().decode("utf-8", errors="ignore")

else:
    if not DATA_DIR.exists():
        st.sidebar.error("data/latex/ folder not found")
    else:
        files = list(DATA_DIR.iterdir())

        stdout_candidates = [f for f in files if f.suffix in [".txt", ".log"]]
        aux_candidates = [f for f in files if f.suffix == ".aux"]

        stdout_path = st.sidebar.selectbox(
            "Select stdout/log file",
            stdout_candidates,
            format_func=lambda p: p.name if p else "None"
        ) if stdout_candidates else None

        aux_path = st.sidebar.selectbox(
            "Select AUX file",
            aux_candidates,
            format_func=lambda p: p.name if p else "None"
        ) if aux_candidates else None

        if stdout_path:
            stdout_text = stdout_path.read_text(errors="ignore")

        if aux_path:
            aux_text = aux_path.read_text(errors="ignore")

# =====================================
# PARSERS
# =====================================
def extract_log_messages(text):
    errors = []
    warnings = []
    overfull = []

    for line in text.splitlines():
        if line.startswith("!"):
            errors.append(line)
        elif "Warning" in line:
            warnings.append(line)
        elif "Overfull" in line or "Underfull" in line:
            overfull.append(line)

    return errors, warnings, overfull


def parse_aux(text):
    sections = []
    labels = []
    citations = []

    for line in text.splitlines():
        if line.startswith("\\@writefile{toc}"):
            sections.append(line)

        if line.startswith("\\newlabel"):
            labels.append(line)

        if line.startswith("\\citation"):
            citations.append(line)

    return sections, labels, citations


# =====================================
# MAIN DISPLAY
# =====================================
tabs = st.tabs(["📄 Stdout / Log", "📌 AUX File", "📊 Summary"])

# ---------- LOG TAB ----------
with tabs[0]:
    if stdout_text:
        errors, warnings, overfull = extract_log_messages(stdout_text)

        col1, col2, col3 = st.columns(3)
        col1.metric("❌ Errors", len(errors))
        col2.metric("⚠️ Warnings", len(warnings))
        col3.metric("📐 Over/Underfull", len(overfull))

        st.subheader("❌ Errors")
        if errors:
            st.code("\n".join(errors))
        else:
            st.success("No errors detected")

        st.subheader("⚠️ Warnings")
        if warnings:
            st.code("\n".join(warnings))
        else:
            st.success("No warnings detected")

        st.subheader("📐 Over/Underfull Boxes")
        if overfull:
            st.code("\n".join(overfull))
        else:
            st.success("No box issues detected")

        with st.expander("📜 Full Log Output"):
            st.text(stdout_text)

    else:
        st.info("Upload or select a stdout/log file to view output.")


# ---------- AUX TAB ----------
with tabs[1]:
    if aux_text:
        sections, labels, citations = parse_aux(aux_text)

        col1, col2, col3 = st.columns(3)
        col1.metric("📑 TOC Entries", len(sections))
        col2.metric("🏷 Labels", len(labels))
        col3.metric("📚 Citations", len(citations))

        st.subheader("📑 Table of Contents Writes")
        if sections:
            st.code("\n".join(sections))
        else:
            st.write("No TOC entries found")

        st.subheader("🏷 Labels")
        if labels:
            st.code("\n".join(labels))
        else:
            st.write("No labels found")

        st.subheader("📚 Citations")
        if citations:
            st.code("\n".join(citations))
        else:
            st.write("No citations found")

        with st.expander("📜 Full AUX File"):
            st.text(aux_text)

    else:
        st.info("Upload or select an AUX file to inspect metadata.")


# ---------- SUMMARY TAB ----------
with tabs[2]:
    st.subheader("🧠 Build Diagnostics")

    if stdout_text:
        errors, warnings, overfull = extract_log_messages(stdout_text)

        if errors:
            st.error("Build failed — errors present.")
        elif warnings:
            st.warning("Build succeeded with warnings.")
        else:
            st.success("Clean build — no issues detected.")

    if aux_text:
        sections, labels, citations = parse_aux(aux_text)
        st.write("### Document Structure")
        st.write(f"- Sections/TOC entries: {len(sections)}")
        st.write(f"- Labels: {len(labels)}")
        st.write(f"- Citations: {len(citations)}")

    if not stdout_text and not aux_text:
        st.info("No files loaded yet.")