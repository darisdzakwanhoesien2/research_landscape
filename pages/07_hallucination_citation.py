import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="LaTeX Citation ↔ DOI Linker", layout="wide")
st.title("🔗 LaTeX Citation → DOI Linker")

st.markdown("""
This app links:

- **LaTeX citation keys** from `\\citation{...}`
- with known **DOI mappings**

and reports:
- ✅ matched references
- ⚠ missing keys
- 📦 exportable BibTeX / CSV
""")

# =========================================================
# 1. DOI DATABASE (Citation Key -> DOI)
# =========================================================

DOI_DB = {
    # --- Greenwashing & Carbonwashing ---
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

    # --- NLP / Multimodal ---
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

    # --- ESG / Finance ---
    "Fan2024Textual": "10.3390/su16219270",
    "ESGNewsSentiment2024": "10.1111/acfi.70015",
    "csr.70350": "10.1002/csr.70350",
    "ssrn.3722973": "10.2139/ssrn.3722973",
    "sampj-01-2024-0045": "10.1108/sampj-01-2024-0045",
    "su16062571": "10.3390/su16062571",
    "su18010236": "10.3390/su18010236",
    "s10479-023-05514-z": "10.1007/s10479-023-05514-z",
    "ijfe.3096": "10.1108/ijfe.3096",

    # --- SME ---
    "bse.3995": "10.1002/bse.3995",
    "cinti63048": "10.1109/cinti63048.2024.10830823",
    "creditRiskSME": "10.1080/01605682.2022.2072781",
    "su152416872": "10.3390/su152416872",
    "su17178029": "10.3390/su17178029",

    # --- Interpretability ---
    "systems13100899": "10.3390/systems13100899",
    "ssrn.5468389": "10.2139/ssrn.5468389",
    "su172411128": "10.3390/su172411128",
    "systems13090783": "10.3390/systems13090783",
    "srj-03-2012-0035": "10.1108/srj-03-2012-0035",
    "app12199691": "10.3390/app12199691",
}

# =========================================================
# 2. INPUT: CITATION BLOCK
# =========================================================

st.subheader("📥 Paste LaTeX Citation Lines")

default_text = r"""
\citation{Li2024Greenwashing,Li2021Carbonwashing}
\citation{Wu2025Disclosure,Fan2024Textual}
\citation{LayoutLMv2,DocFormer,LayoutLM}
\citation{EmeraldGraph,EulerESG}
\citation{bse.3995,cinti63048,creditRiskSME}
"""

citation_text = st.text_area("Paste your \\citation{...} lines here:", value=default_text, height=250)

# =========================================================
# 3. PARSE
# =========================================================

def extract_keys(text):
    pattern = r"\\citation\{([^}]*)\}"
    matches = re.findall(pattern, text)
    keys = []
    for m in matches:
        parts = [p.strip() for p in m.split(",") if p.strip()]
        keys.extend(parts)
    return sorted(set(keys))

keys = extract_keys(citation_text)

# =========================================================
# 4. MATCH WITH DOI DB
# =========================================================

matched = []
missing = []

for k in keys:
    if k in DOI_DB:
        matched.append((k, DOI_DB[k]))
    else:
        missing.append(k)

df = pd.DataFrame(matched, columns=["Citation Key", "DOI"])
df["DOI Link"] = df["DOI"].apply(lambda d: f"https://doi.org/{d}")

# =========================================================
# 5. RESULTS
# =========================================================

st.subheader("✅ Matched Citations")

st.dataframe(df, use_container_width=True)

st.subheader("⚠ Missing / Unknown Keys")

if missing:
    st.error("These citation keys were NOT found in DOI database:")
    st.code("\n".join(missing))
else:
    st.success("All citation keys matched successfully!")

# =========================================================
# 6. EXPORTS
# =========================================================

st.subheader("📤 Export")

# ---- CSV
csv_data = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download CSV Mapping", csv_data, "citation_doi_mapping.csv", "text/csv")

# ---- BibTeX
def bibtex_entry(key, doi):
    return f"""@article{{{key},
  doi = {{{doi}}},
  url = {{https://doi.org/{doi}}}
}}"""

bibtex = "\n\n".join(bibtex_entry(k, d) for k, d in matched)
st.download_button("⬇ Download BibTeX", bibtex.encode("utf-8"), "references.bib", "text/plain")

# ---- Clean citep
citep = "\\citep{" + ",".join(k for k, _ in matched) + "}"
st.text_area("📌 Cleaned LaTeX citep", citep, height=80)
