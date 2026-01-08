import streamlit as st
import re
from io import StringIO

st.set_page_config(page_title="LaTeX DOI → BibKey Converter", layout="wide")

st.title("📚 LaTeX Citation Fixer (DOI → BibTeX Key)")
st.caption("Convert DOI-based \\citep{...} into BibTeX keys using your .bib file")

# ======================================================
# Helpers
# ======================================================

def parse_bibtex_doi_map(bib_text: str):
    entries = re.findall(r'@.+?\{([^,]+),([\s\S]*?)\n\}', bib_text)
    doi_to_key = {}

    for key, body in entries:
        m = re.search(r'doi\s*=\s*\{([^}]+)\}', body, re.IGNORECASE)
        if m:
            doi = m.group(1).strip()
            doi_to_key[doi] = key

    return doi_to_key


def fix_latex_citations(tex: str, doi_to_key: dict):
    cite_pattern = re.compile(r'\\citep\{([^}]+)\}')

    def repl(match):
        items = [x.strip() for x in match.group(1).split(",")]
        new_items = []

        for it in items:
            if re.fullmatch(r"\d+", it):
                continue
            if it in doi_to_key:
                new_items.append(doi_to_key[it])
            else:
                new_items.append(it)

        if not new_items:
            return ""
        return r"\citep{" + ", ".join(new_items) + "}"

    return cite_pattern.sub(repl, tex)


# ======================================================
# Upload Inputs
# ======================================================

st.sidebar.header("📥 Inputs")

bib_file = st.sidebar.file_uploader("Upload BibTeX (.bib)", type=["bib"])
tex_file = st.sidebar.file_uploader("Upload LaTeX (.tex)", type=["tex"])

st.sidebar.markdown("— or —")

tex_text_input = st.sidebar.text_area(
    "Paste LaTeX content",
    height=250,
    placeholder="Paste your LaTeX here..."
)

# ======================================================
# Load Data
# ======================================================

bib_text = None
if bib_file:
    bib_text = bib_file.read().decode("utf-8")

latex_text = None
if tex_file:
    latex_text = tex_file.read().decode("utf-8")
elif tex_text_input.strip():
    latex_text = tex_text_input

# ======================================================
# Process
# ======================================================

if bib_text and latex_text:

    doi_to_key = parse_bibtex_doi_map(bib_text)

    st.sidebar.success(f"Found {len(doi_to_key)} DOI mappings in BibTeX")

    fixed_text = fix_latex_citations(latex_text, doi_to_key)

    # ============================
    # Display
    # ============================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🟥 Original LaTeX")
        st.code(latex_text, language="latex")

    with col2:
        st.subheader("🟩 Fixed LaTeX")
        st.code(fixed_text, language="latex")

    # ============================
    # Download
    # ============================

    st.download_button(
        "⬇ Download Fixed LaTeX",
        data=fixed_text,
        file_name="fixed.tex",
        mime="text/plain"
    )

else:
    st.info("Upload both BibTeX and LaTeX files, or paste LaTeX and upload BibTeX.")

# ======================================================
# Debug Panel
# ======================================================

with st.expander("🔍 Debug: DOI → Key Mapping"):
    if bib_text:
        mapping = parse_bibtex_doi_map(bib_text)
        st.json(mapping)
    else:
        st.write("No BibTeX uploaded yet.")
