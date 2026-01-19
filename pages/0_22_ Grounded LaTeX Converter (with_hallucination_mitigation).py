import streamlit as st
import re
import pandas as pd

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(page_title="LaTeX Citation Normalizer", layout="wide")
st.title("📚 LaTeX Citation Normalizer & Hallucination Detector")
st.caption("Normalize DOI/BibKey citations → canonical BibTeX keys with audit trail")

# =========================================================
# CURATED DOI DATABASE (extend anytime)
# =========================================================

DOI_DB = {
    "Li2024Greenwashing": "10.1002/csr.70133",
    "Li2021Carbonwashing": "10.2139/ssrn.3901278",
    "Li2022Carbonwashing": "10.2139/ssrn.4207369",
    "Boiral2013Simulacra": "10.1108/aaaj-04-2012-00998",
    "Boiral2016GHG": "10.1007/s10551-015-2979-4",
    "Wu2025Disclosure": "10.54097/hks0kp94",
    "hks0kp94": "10.54097/hks0kp94",
    "Chen2024How": "10.1108/cfri-02-2024-0079",
    "GRI_Greenwashing2021": "10.1108/sampj-07-2022-0365",
    "GreenScreen2024": "10.1007/978-3-031-56435-2_8",

    "LayoutLMv2": "10.18653/v1/2021.acl-long.201",
    "DocFormer": "10.1109/iccv48922.2021.00103",
    "LayoutLM": "10.1145/3394486.3403172",
    "FINDSum": "10.1109/tkde.2023.3324012",
    "MMESGBench": "10.1145/3746027.3758225",
    "MTVAF": "10.1007/s10462-023-10685-z",
    "MTVAF2023": "10.1007/s10462-023-10685-z",
    "HIMT": "10.1109/taffc.2022.3171091",
    "EmeraldGraph": "10.48550/arxiv.2512.11506",
    "EmeraldMind": "10.48550/arxiv.2512.11506",
    "EulerESG": "10.48550/arxiv.2511.21712",
    "ESGBench": "10.48550/arxiv.2511.16438",
    "vqzg-em46": "10.48448/vqzg-em46",

    "Fan2024Textual": "10.3390/su16219270",
    "ESGNewsSentiment2024": "10.1111/acfi.70015",
    "csr.70350": "10.1002/csr.70350",
    "csr.70133": "10.1002/csr.70133",
    "ssrn.3722973": "10.2139/ssrn.3722973",
    "sampj-01-2024-0045": "10.1108/sampj-01-2024-0045",
    "su16062571": "10.3390/su16062571",
    "su18010236": "10.3390/su18010236",
    "s10479-023-05514-z": "10.1007/s10479-023-05514-z",
    "ijfe.3096": "10.1108/ijfe.3096",

    "bse.3995": "10.1002/bse.3995",
    "cinti63048": "10.1109/cinti63048.2024.10830823",
    "creditRiskSME": "10.1080/01605682.2022.2072781",
    "su152416872": "10.3390/su152416872",
    "su17178029": "10.3390/su17178029",

    "systems13100899": "10.3390/systems13100899",
    "ssrn.5468389": "10.2139/ssrn.5468389",
    "su172411128": "10.3390/su172411128",
    "systems13090783": "10.3390/systems13090783",
    "srj-03-2012-0035": "10.1108/srj-03-2012-0035",
    "app12199691": "10.3390/app12199691",
}

DB_DOI_TO_KEY = {}
for k, d in DOI_DB.items():
    DB_DOI_TO_KEY.setdefault(d, []).append(k)

# =========================================================
# HELPERS
# =========================================================

DOI_REGEX = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.I)

def parse_bibtex_maps(bib_text: str):
    entries = re.findall(r'@.+?\{([^,]+),([\s\S]*?)\n\}', bib_text)
    doi_to_key, key_to_doi = {}, {}
    for key, body in entries:
        m = re.search(r'doi\s*=\s*\{([^}]+)\}', body, re.I)
        if m:
            doi = m.group(1).strip()
            doi_to_key[doi] = key
            key_to_doi[key] = doi
    return doi_to_key, key_to_doi


def extract_all_citations(text: str):
    patterns = [
        r'\\citep\{([^}]+)\}',
        r'\\cite\{([^}]+)\}',
        r'\\citation\{([^}]+)\}',
    ]
    keys = []
    for p in patterns:
        matches = re.findall(p, text)
        for m in matches:
            keys.extend([x.strip() for x in m.split(",") if x.strip()])
    return sorted(set(keys))


def detect_type(k):
    if DOI_REGEX.match(k):
        return "doi"
    if k.lower().startswith(("csr.", "ssrn.")):
        return "partial-doi"
    return "bibkey"


def rewrite_latex(tex, replace_map):
    def repl(match):
        items = [x.strip() for x in match.group(1).split(",")]
        new_items = [replace_map.get(i, i) for i in items]
        return r"\citep{" + ", ".join(new_items) + "}"

    tex = re.sub(r'\\citep\{([^}]+)\}', repl, tex)
    tex = re.sub(r'\\cite\{([^}]+)\}', repl, tex)
    return tex

# =========================================================
# SIDEBAR INPUT
# =========================================================

st.sidebar.header("📥 Inputs")

bib_file = st.sidebar.file_uploader("Upload BibTeX (.bib)", type=["bib"])
tex_file = st.sidebar.file_uploader("Upload LaTeX (.tex or .aux)", type=["tex", "aux"])

text_input = st.sidebar.text_area("Or paste LaTeX/AUX content", height=200)

# =========================================================
# LOAD
# =========================================================

bib_text = bib_file.read().decode("utf-8") if bib_file else None

latex_text = None
if tex_file:
    latex_text = tex_file.read().decode("utf-8")
elif text_input.strip():
    latex_text = text_input

# =========================================================
# PROCESS
# =========================================================

if latex_text:

    st.success("Input loaded")

    doi_to_key, key_to_doi = parse_bibtex_maps(bib_text) if bib_text else ({}, {})

    all_keys = extract_all_citations(latex_text)

    rows = []
    for raw in all_keys:
        rows.append({
            "raw": raw,
            "type": detect_type(raw),
            "resolved_key": None,
            "resolved_doi": None,
            "method": None,
        })

    # ---------------- Resolution Pipeline ----------------

    for r in rows:
        raw = r["raw"]

        if raw in key_to_doi:
            r["resolved_key"] = raw
            r["resolved_doi"] = key_to_doi[raw]
            r["method"] = "bibtex"
            continue

        if raw in DOI_DB:
            r["resolved_doi"] = DOI_DB[raw]
            if DOI_DB[raw] in DB_DOI_TO_KEY:
                r["resolved_key"] = DB_DOI_TO_KEY[DOI_DB[raw]][0]
            r["method"] = "curated-db"
            continue

        if detect_type(raw) == "doi" and raw in doi_to_key:
            r["resolved_key"] = doi_to_key[raw]
            r["resolved_doi"] = raw
            r["method"] = "bibtex-doi"
            continue

        r["method"] = "unresolved"

    df = pd.DataFrame(rows)

    replace_map = {r["raw"]: r["resolved_key"] for r in rows if r["resolved_key"]}

    fixed_tex = rewrite_latex(latex_text, replace_map)

    # =====================================================
    # UI
    # =====================================================

    tab1, tab2, tab3 = st.tabs(["✅ Results", "⚠ Unresolved", "🔍 Debug"])

    with tab1:
        st.subheader("Citation Resolution Table")
        st.dataframe(df, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original")
            st.code(latex_text, language="latex")
        with col2:
            st.subheader("Fixed")
            st.code(fixed_tex, language="latex")

        st.download_button(
            "⬇ Download Fixed LaTeX",
            fixed_tex,
            file_name="fixed.tex",
            mime="text/plain",
        )

        st.download_button(
            "⬇ Download Resolution Log (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name="citation_log.csv",
            mime="text/csv",
        )

    with tab2:
        unresolved = df[df["method"] == "unresolved"]
        if unresolved.empty:
            st.success("No unresolved citations 🎉")
        else:
            st.error("These citations could not be resolved automatically:")
            st.dataframe(unresolved, use_container_width=True)

    with tab3:
        st.subheader("BibTeX DOI Map")
        st.json(doi_to_key)

        st.subheader("Curated DOI DB")
        st.json(DOI_DB)

else:
    st.info("Upload or paste LaTeX/AUX content to begin.")
