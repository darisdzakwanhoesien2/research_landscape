import streamlit as st
import re
import pandas as pd
from rapidfuzz import fuzz
from pathlib import Path
import json
from datetime import datetime
import uuid

# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).parent
RUNS_DIR = BASE_DIR / "runs"
RUNS_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="LaTeX Citation Aligner", layout="wide")
st.title("📚 LaTeX Citation Aligner + Highlighter")
st.caption("Align citations, visualize common language, and persist experiment runs.")

# =========================================================
# HELPERS
# =========================================================

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_all_citations(text):
    patterns = [
        r'\\citep\{([^}]+)\}',
        r'\\cite\{([^}]+)\}',
    ]
    keys = []
    for p in patterns:
        for m in re.findall(p, text):
            keys.extend([x.strip() for x in m.split(",") if x.strip()])
    return sorted(set(keys))


def similarity(a, b):
    return fuzz.token_set_ratio(normalize_text(a), normalize_text(b))


def align_citations(cites_a, cites_b, threshold=70):
    rows = []
    used_b = set()
    canonical_map = {}

    for idx, a in enumerate(cites_a, 1):
        best_b = None
        best_score = 0

        for b in cites_b:
            score = similarity(a, b)
            if score > best_score:
                best_b = b
                best_score = score

        canonical_id = f"cite_{idx:03d}"

        if best_score >= threshold:
            canonical_map[a] = canonical_id
            canonical_map[best_b] = canonical_id
            used_b.add(best_b)
            status = "aligned"
        else:
            canonical_map[a] = canonical_id
            status = "unmatched-A"

        rows.append({
            "canonical_id": canonical_id,
            "A_raw": a,
            "B_raw": best_b,
            "similarity": best_score,
            "status": status
        })

    # Unmatched B
    for b in cites_b:
        if b not in used_b:
            cid = f"cite_{len(rows)+1:03d}"
            canonical_map[b] = cid
            rows.append({
                "canonical_id": cid,
                "A_raw": None,
                "B_raw": b,
                "similarity": None,
                "status": "unmatched-B"
            })

    return pd.DataFrame(rows), canonical_map


def rewrite_latex(tex, mapping):
    def repl(match):
        items = [x.strip() for x in match.group(1).split(",")]
        new_items = [mapping.get(i, i) for i in items]
        return r"\citep{" + ", ".join(new_items) + "}"

    tex = re.sub(r'\\citep\{([^}]+)\}', repl, tex)
    tex = re.sub(r'\\cite\{([^}]+)\}', repl, tex)
    return tex


STOPWORDS = {
    "the", "and", "or", "of", "to", "in", "a", "for", "on", "with",
    "as", "is", "are", "was", "were", "by", "an", "be", "this",
    "that", "from", "at", "it", "not", "which", "their", "has",
    "have", "had", "but", "also"
}


def clean_text_for_tokens(text):
    text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"[^a-zA-Z ]+", " ", text)

    tokens = [t.lower() for t in text.split() if len(t) > 3]
    tokens = [t for t in tokens if t not in STOPWORDS]
    return set(tokens)


def highlight_common_words(text, common_tokens):
    def repl(match):
        word = match.group(0)
        if word.lower() in common_tokens:
            return f"<span style='background-color:#FFF3B0'>{word}</span>"
        return word

    pattern = re.compile(r"\b[A-Za-z]{4,}\b")
    return pattern.sub(repl, text)


def save_run(payload):
    run_id = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir()

    # Save text files
    (run_dir / "docA.tex").write_text(payload["docA"], encoding="utf-8")
    (run_dir / "docB.tex").write_text(payload["docB"], encoding="utf-8")
    (run_dir / "docA_fixed.tex").write_text(payload["docA_fixed"], encoding="utf-8")
    (run_dir / "docB_fixed.tex").write_text(payload["docB_fixed"], encoding="utf-8")

    # Save CSV
    payload["alignment_df"].to_csv(run_dir / "alignment.csv", index=False)

    # Save JSON metadata
    meta = {
        "run_id": run_id,
        "created": datetime.utcnow().isoformat(),
        "threshold": payload["threshold"],
        "common_token_count": len(payload["common_tokens"]),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    return run_id


def list_runs():
    return sorted([p.name for p in RUNS_DIR.iterdir() if p.is_dir()], reverse=True)


def load_run(run_id):
    run_dir = RUNS_DIR / run_id

    return {
        "docA": (run_dir / "docA.tex").read_text(),
        "docB": (run_dir / "docB.tex").read_text(),
        "docA_fixed": (run_dir / "docA_fixed.tex").read_text(),
        "docB_fixed": (run_dir / "docB_fixed.tex").read_text(),
        "alignment_df": pd.read_csv(run_dir / "alignment.csv"),
        "meta": json.loads((run_dir / "meta.json").read_text())
    }

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📥 Input")

docA = st.sidebar.text_area("Paste LaTeX Document A", height=180)
docB = st.sidebar.text_area("Paste LaTeX Document B", height=180)

threshold = st.sidebar.slider("Citation Similarity Threshold", 50, 95, 75)

st.sidebar.divider()
st.sidebar.header("📂 Saved Runs")

runs = list_runs()
selected_run = st.sidebar.selectbox("Load previous run", [""] + runs)

# =========================================================
# LOAD SAVED RUN
# =========================================================

if selected_run:
    saved = load_run(selected_run)
    docA = saved["docA"]
    docB = saved["docB"]

# =========================================================
# PROCESS
# =========================================================

if docA.strip() and docB.strip():

    cites_a = extract_all_citations(docA)
    cites_b = extract_all_citations(docB)

    align_df, canonical_map = align_citations(cites_a, cites_b, threshold)

    fixed_a = rewrite_latex(docA, canonical_map)
    fixed_b = rewrite_latex(docB, canonical_map)

    # Token highlighting
    tokens_a = clean_text_for_tokens(docA)
    tokens_b = clean_text_for_tokens(docB)
    common_tokens = tokens_a & tokens_b

    highlight_a = highlight_common_words(docA, common_tokens)
    highlight_b = highlight_common_words(docB, common_tokens)

    # =====================================================
    # SAVE BUTTON
    # =====================================================

    if st.button("💾 Save This Run"):
        run_id = save_run({
            "docA": docA,
            "docB": docB,
            "docA_fixed": fixed_a,
            "docB_fixed": fixed_b,
            "alignment_df": align_df,
            "threshold": threshold,
            "common_tokens": common_tokens
        })
        st.success(f"Saved as run: {run_id}")

    # =====================================================
    # UI
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Alignment",
        "🖍️ Highlighted Text",
        "📄 Canonical LaTeX",
        "⬇ Downloads"
    ])

    with tab1:
        st.dataframe(align_df, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Document A")
            st.markdown(
                f"<div style='white-space:pre-wrap;font-family:monospace'>{highlight_a}</div>",
                unsafe_allow_html=True
            )

        with c2:
            st.subheader("Document B")
            st.markdown(
                f"<div style='white-space:pre-wrap;font-family:monospace'>{highlight_b}</div>",
                unsafe_allow_html=True
            )

    with tab3:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Canonical Document A")
            st.code(fixed_a, language="latex")

        with c2:
            st.subheader("Canonical Document B")
            st.code(fixed_b, language="latex")

    with tab4:
        st.download_button("Download Alignment CSV", align_df.to_csv(index=False), "alignment.csv")
        st.download_button("Download Doc A", fixed_a, "docA_fixed.tex")
        st.download_button("Download Doc B", fixed_b, "docB_fixed.tex")

else:
    st.info("⬅ Paste both documents to begin.")


# import streamlit as st
# import re
# import pandas as pd
# from rapidfuzz import fuzz

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(page_title="Citation Aligner", layout="wide")
# st.title("🔗 LaTeX Citation Alignment (No Alias DB)")
# st.caption("Align citations between two LaTeX documents using fuzzy similarity only.")

# # =========================================================
# # HELPERS
# # =========================================================

# def normalize_text(text):
#     text = text.lower()
#     text = re.sub(r"[^a-z0-9 ]+", " ", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     return text


# def extract_all_citations(text):
#     patterns = [
#         r'\\citep\{([^}]+)\}',
#         r'\\cite\{([^}]+)\}',
#     ]
#     keys = []
#     for p in patterns:
#         for m in re.findall(p, text):
#             keys.extend([x.strip() for x in m.split(",") if x.strip()])
#     return sorted(set(keys))


# def similarity(a, b):
#     return fuzz.token_set_ratio(normalize_text(a), normalize_text(b))


# def align_citations(cites_a, cites_b, threshold=70):
#     rows = []
#     used_b = set()
#     canonical_map = {}

#     for idx, a in enumerate(cites_a, 1):
#         best_b = None
#         best_score = 0

#         for b in cites_b:
#             score = similarity(a, b)
#             if score > best_score:
#                 best_b = b
#                 best_score = score

#         canonical_id = f"cite_{idx:03d}"

#         if best_score >= threshold:
#             canonical_map[a] = canonical_id
#             canonical_map[best_b] = canonical_id
#             used_b.add(best_b)
#             status = "aligned"
#         else:
#             canonical_map[a] = canonical_id
#             status = "unmatched-A"

#         rows.append({
#             "canonical_id": canonical_id,
#             "A_raw": a,
#             "B_raw": best_b,
#             "similarity": best_score,
#             "status": status
#         })

#     # Unmatched B
#     for b in cites_b:
#         if b not in used_b:
#             cid = f"cite_{len(rows)+1:03d}"
#             canonical_map[b] = cid
#             rows.append({
#                 "canonical_id": cid,
#                 "A_raw": None,
#                 "B_raw": b,
#                 "similarity": None,
#                 "status": "unmatched-B"
#             })

#     return pd.DataFrame(rows), canonical_map


# def rewrite_latex(tex, mapping):
#     def repl(match):
#         items = [x.strip() for x in match.group(1).split(",")]
#         new_items = [mapping.get(i, i) for i in items]
#         return r"\citep{" + ", ".join(new_items) + "}"

#     tex = re.sub(r'\\citep\{([^}]+)\}', repl, tex)
#     tex = re.sub(r'\\cite\{([^}]+)\}', repl, tex)
#     return tex

# # =========================================================
# # UI INPUT
# # =========================================================

# st.sidebar.header("📥 Input Documents")

# tex_a = st.sidebar.file_uploader("Upload LaTeX A", type=["tex"], key="a")
# text_a = st.sidebar.text_area("Or paste LaTeX A", height=150)

# tex_b = st.sidebar.file_uploader("Upload LaTeX B", type=["tex"], key="b")
# text_b = st.sidebar.text_area("Or paste LaTeX B", height=150)

# threshold = st.sidebar.slider("Similarity Threshold", 50, 95, 75)

# # =========================================================
# # LOAD
# # =========================================================

# def load_tex(file, text):
#     if file:
#         return file.read().decode("utf-8", errors="ignore")
#     return text.strip() if text.strip() else None

# latex_a = load_tex(tex_a, text_a)
# latex_b = load_tex(tex_b, text_b)

# # =========================================================
# # PROCESS
# # =========================================================

# if latex_a and latex_b:

#     cites_a = extract_all_citations(latex_a)
#     cites_b = extract_all_citations(latex_b)

#     align_df, canonical_map = align_citations(cites_a, cites_b, threshold)

#     fixed_a = rewrite_latex(latex_a, canonical_map)
#     fixed_b = rewrite_latex(latex_b, canonical_map)

#     # =====================================================
#     # UI
#     # =====================================================

#     tab1, tab2, tab3 = st.tabs([
#         "📊 Alignment",
#         "📄 Canonicalized LaTeX",
#         "⬇ Downloads"
#     ])

#     with tab1:
#         st.subheader("Citation Alignment Table")
#         st.dataframe(align_df, use_container_width=True)

#     with tab2:
#         col1, col2 = st.columns(2)

#         with col1:
#             st.subheader("Document A")
#             st.code(fixed_a, language="latex")

#         with col2:
#             st.subheader("Document B")
#             st.code(fixed_b, language="latex")

#     with tab3:
#         st.download_button(
#             "Download Canonical Doc A",
#             fixed_a,
#             file_name="docA_canonical.tex",
#             mime="text/plain"
#         )

#         st.download_button(
#             "Download Canonical Doc B",
#             fixed_b,
#             file_name="docB_canonical.tex",
#             mime="text/plain"
#         )

#         st.download_button(
#             "Download Alignment Table",
#             align_df.to_csv(index=False).encode("utf-8"),
#             file_name="alignment.csv",
#             mime="text/csv"
#         )

# else:
#     st.info("⬅ Upload BOTH LaTeX documents to begin.")


# import streamlit as st
# import re
# import pandas as pd

# # =========================================================
# # PAGE CONFIG
# # =========================================================

# st.set_page_config(page_title="LaTeX Citation Comparator", layout="wide")
# st.title("📚 LaTeX Citation Comparator & Hallucination Detector")
# st.caption("Normalize BibTeX/DOI citations and compare two LaTeX documents with audit trail.")

# # =========================================================
# # CURATED DOI DATABASE
# # =========================================================

# DOI_DB = {
#     "Li2024Greenwashing": "10.1002/csr.70133",
#     "Li2021Carbonwashing": "10.2139/ssrn.3901278",
#     "Li2022Carbonwashing": "10.2139/ssrn.4207369",
#     "Boiral2013Simulacra": "10.1108/aaaj-04-2012-00998",
#     "Boiral2016GHG": "10.1007/s10551-015-2979-4",
#     "Wu2025Disclosure": "10.54097/hks0kp94",
#     "hks0kp94": "10.54097/hks0kp94",
#     "Chen2024How": "10.1108/cfri-02-2024-0079",
#     "GRI_Greenwashing2021": "10.1108/sampj-07-2022-0365",
#     "GreenScreen2024": "10.1007/978-3-031-56435-2_8",

#     "LayoutLMv2": "10.18653/v1/2021.acl-long.201",
#     "DocFormer": "10.1109/iccv48922.2021.00103",
#     "LayoutLM": "10.1145/3394486.3403172",
#     "FINDSum": "10.1109/tkde.2023.3324012",
#     "MMESGBench": "10.1145/3746027.3758225",
#     "MTVAF": "10.1007/s10462-023-10685-z",
#     "MTVAF2023": "10.1007/s10462-023-10685-z",
#     "HIMT": "10.1109/taffc.2022.3171091",
#     "EmeraldGraph": "10.48550/arxiv.2512.11506",
#     "EmeraldMind": "10.48550/arxiv.2512.11506",
#     "EulerESG": "10.48550/arxiv.2511.21712",
#     "ESGBench": "10.48550/arxiv.2511.16438",
#     "vqzg-em46": "10.48448/vqzg-em46",

#     "Fan2024Textual": "10.3390/su16219270",
#     "ESGNewsSentiment2024": "10.1111/acfi.70015",
#     "csr.70350": "10.1002/csr.70350",
#     "csr.70133": "10.1002/csr.70133",
#     "ssrn.3722973": "10.2139/ssrn.3722973",
#     "sampj-01-2024-0045": "10.1108/sampj-01-2024-0045",
#     "su16062571": "10.3390/su16062571",
#     "su18010236": "10.3390/su18010236",
#     "s10479-023-05514-z": "10.1007/s10479-023-05514-z",
#     "ijfe.3096": "10.1108/ijfe.3096",

#     "bse.3995": "10.1002/bse.3995",
#     "cinti63048": "10.1109/cinti63048.2024.10830823",
#     "creditRiskSME": "10.1080/01605682.2022.2072781",
#     "su152416872": "10.3390/su152416872",
#     "su17178029": "10.3390/su17178029",

#     "systems13100899": "10.3390/systems13100899",
#     "ssrn.5468389": "10.2139/ssrn.5468389",
#     "su172411128": "10.3390/su172411128",
#     "systems13090783": "10.3390/systems13090783",
#     "srj-03-2012-0035": "10.1108/srj-03-2012-0035",
#     "app12199691": "10.3390/app12199691",
# }

# DB_DOI_TO_KEY = {}
# for k, d in DOI_DB.items():
#     DB_DOI_TO_KEY.setdefault(d, []).append(k)

# # =========================================================
# # HELPERS
# # =========================================================

# DOI_REGEX = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.I)

# def parse_bibtex_maps(bib_text: str):
#     entries = re.findall(r'@.+?\{([^,]+),([\s\S]*?)\n\}', bib_text or "")
#     doi_to_key, key_to_doi = {}, {}
#     for key, body in entries:
#         m = re.search(r'doi\s*=\s*\{([^}]+)\}', body, re.I)
#         if m:
#             doi = m.group(1).strip()
#             doi_to_key[doi] = key
#             key_to_doi[key] = doi
#     return doi_to_key, key_to_doi


# def extract_all_citations(text: str):
#     patterns = [
#         r'\\citep\{([^}]+)\}',
#         r'\\cite\{([^}]+)\}',
#         r'\\citation\{([^}]+)\}',
#     ]
#     keys = []
#     for p in patterns:
#         matches = re.findall(p, text)
#         for m in matches:
#             keys.extend([x.strip() for x in m.split(",") if x.strip()])
#     return sorted(set(keys))


# def detect_type(k):
#     if DOI_REGEX.match(k):
#         return "doi"
#     if k.lower().startswith(("csr.", "ssrn.")):
#         return "partial-doi"
#     return "bibkey"


# def rewrite_latex(tex, replace_map):
#     def repl(match):
#         items = [x.strip() for x in match.group(1).split(",")]
#         new_items = [replace_map.get(i, i) for i in items]
#         return r"\citep{" + ", ".join(new_items) + "}"

#     tex = re.sub(r'\\citep\{([^}]+)\}', repl, tex)
#     tex = re.sub(r'\\cite\{([^}]+)\}', repl, tex)
#     return tex


# def normalize_document(latex_text, bib_text):
#     doi_to_key, key_to_doi = parse_bibtex_maps(bib_text)

#     all_keys = extract_all_citations(latex_text)

#     rows = []
#     for raw in all_keys:
#         rows.append({
#             "raw": raw,
#             "type": detect_type(raw),
#             "resolved_key": None,
#             "resolved_doi": None,
#             "method": None,
#         })

#     for r in rows:
#         raw = r["raw"]

#         if raw in key_to_doi:
#             r["resolved_key"] = raw
#             r["resolved_doi"] = key_to_doi[raw]
#             r["method"] = "bibtex"
#             continue

#         if raw in DOI_DB:
#             r["resolved_doi"] = DOI_DB[raw]
#             if DOI_DB[raw] in DB_DOI_TO_KEY:
#                 r["resolved_key"] = DB_DOI_TO_KEY[DOI_DB[raw]][0]
#             r["method"] = "curated-db"
#             continue

#         if detect_type(raw) == "doi" and raw in doi_to_key:
#             r["resolved_key"] = doi_to_key[raw]
#             r["resolved_doi"] = raw
#             r["method"] = "bibtex-doi"
#             continue

#         r["method"] = "unresolved"

#     df = pd.DataFrame(rows)

#     replace_map = {r["raw"]: r["resolved_key"] for r in rows if r["resolved_key"]}
#     fixed_tex = rewrite_latex(latex_text, replace_map)

#     return {
#         "df": df,
#         "fixed_tex": fixed_tex,
#         "resolved_keys": set(df["resolved_key"].dropna()),
#         "unresolved": df[df["method"] == "unresolved"]
#     }

# # =========================================================
# # SIDEBAR INPUT
# # =========================================================

# st.sidebar.header("📥 Inputs")

# bib_file = st.sidebar.file_uploader("Upload BibTeX (.bib)", type=["bib"])

# st.sidebar.divider()
# st.sidebar.subheader("📄 Document A")
# tex_a = st.sidebar.file_uploader("Upload LaTeX A", type=["tex", "aux"], key="a")
# text_a = st.sidebar.text_area("Or paste LaTeX A", height=150, key="ta")

# st.sidebar.divider()
# st.sidebar.subheader("📄 Document B")
# tex_b = st.sidebar.file_uploader("Upload LaTeX B", type=["tex", "aux"], key="b")
# text_b = st.sidebar.text_area("Or paste LaTeX B", height=150, key="tb")

# # =========================================================
# # LOAD FILES
# # =========================================================

# def load_tex(file, text):
#     if file:
#         return file.read().decode("utf-8", errors="ignore")
#     return text.strip() if text.strip() else None

# bib_text = bib_file.read().decode("utf-8", errors="ignore") if bib_file else ""
# latex_a = load_tex(tex_a, text_a)
# latex_b = load_tex(tex_b, text_b)

# # =========================================================
# # PROCESS
# # =========================================================

# if latex_a and latex_b:

#     st.success("✅ Both documents loaded")

#     doc_a = normalize_document(latex_a, bib_text)
#     doc_b = normalize_document(latex_b, bib_text)

#     A = doc_a["resolved_keys"]
#     B = doc_b["resolved_keys"]

#     common = sorted(A & B)
#     only_a = sorted(A - B)
#     only_b = sorted(B - A)

#     # =====================================================
#     # UI
#     # =====================================================

#     tab1, tab2, tab3, tab4 = st.tabs([
#         "📊 Comparison",
#         "📄 Normalized LaTeX",
#         "⚠ Hallucinations",
#         "🔍 Audit Logs"
#     ])

#     # ---------------- Comparison ----------------
#     with tab1:
#         c1, c2, c3 = st.columns(3)
#         c1.metric("Common", len(common))
#         c2.metric("Only A", len(only_a))
#         c3.metric("Only B", len(only_b))

#         st.subheader("✅ Common Citations")
#         st.dataframe(pd.DataFrame({"BibKey": common}), use_container_width=True)

#         st.subheader("🅰 Only in Document A")
#         st.dataframe(pd.DataFrame({"BibKey": only_a}), use_container_width=True)

#         st.subheader("🅱 Only in Document B")
#         st.dataframe(pd.DataFrame({"BibKey": only_b}), use_container_width=True)

#     # ---------------- Normalized ----------------
#     with tab2:
#         col1, col2 = st.columns(2)

#         with col1:
#             st.subheader("Document A (Fixed)")
#             st.code(doc_a["fixed_tex"], language="latex")

#         with col2:
#             st.subheader("Document B (Fixed)")
#             st.code(doc_b["fixed_tex"], language="latex")

#     # ---------------- Hallucinations ----------------
#     with tab3:
#         st.subheader("⚠ Unresolved Citations")

#         st.markdown("#### 📄 Document A")
#         if doc_a["unresolved"].empty:
#             st.success("No unresolved citations 🎉")
#         else:
#             st.dataframe(doc_a["unresolved"], use_container_width=True)

#         st.markdown("#### 📄 Document B")
#         if doc_b["unresolved"].empty:
#             st.success("No unresolved citations 🎉")
#         else:
#             st.dataframe(doc_b["unresolved"], use_container_width=True)

#     # ---------------- Audit ----------------
#     with tab4:
#         st.subheader("Document A Resolution Log")
#         st.dataframe(doc_a["df"], use_container_width=True)

#         st.subheader("Document B Resolution Log")
#         st.dataframe(doc_b["df"], use_container_width=True)

#         st.download_button(
#             "⬇ Download Full Audit Log",
#             pd.concat([
#                 doc_a["df"].assign(Document="A"),
#                 doc_b["df"].assign(Document="B")
#             ]).to_csv(index=False).encode("utf-8"),
#             file_name="citation_audit.csv",
#             mime="text/csv",
#         )

# else:
#     st.info("⬅ Upload BibTeX and BOTH LaTeX documents to begin.")


# import streamlit as st
# import pandas as pd
# import re
# from io import StringIO

# # =====================================================
# # PAGE CONFIG
# # =====================================================

# st.set_page_config(
#     page_title="📚 LaTeX Citation Comparator",
#     layout="wide"
# )

# st.title("📚 LaTeX Citation Comparator")
# st.caption("Compare two LaTeX documents and extract all \\citep{...} references.")

# # =====================================================
# # UTILITIES
# # =====================================================

# CITE_PATTERN = r"\\citep\{([^}]+)\}"

# def extract_citep(text: str):
#     """
#     Extract all citep keys from LaTeX text.
#     Handles multiple keys in one citep: \\citep{a,b,c}
#     """
#     matches = re.findall(CITE_PATTERN, text)
#     citations = []

#     for m in matches:
#         parts = [p.strip() for p in m.split(",")]
#         citations.extend(parts)

#     return sorted(set(citations))


# def build_table(citations, source_name):
#     return pd.DataFrame({
#         "CitationKey": citations,
#         "Source": source_name
#     })


# # =====================================================
# # INPUT UI
# # =====================================================

# st.header("📄 Input LaTeX Documents")

# col1, col2 = st.columns(2)

# with col1:
#     st.subheader("Document A")

#     file_a = st.file_uploader(
#         "Upload LaTeX file (A)",
#         type=["tex"],
#         key="file_a"
#     )

#     text_a = st.text_area(
#         "Or paste LaTeX content",
#         height=300,
#         key="text_a"
#     )

# with col2:
#     st.subheader("Document B")

#     file_b = st.file_uploader(
#         "Upload LaTeX file (B)",
#         type=["tex"],
#         key="file_b"
#     )

#     text_b = st.text_area(
#         "Or paste LaTeX content",
#         height=300,
#         key="text_b"
#     )

# # =====================================================
# # LOAD CONTENT
# # =====================================================

# def load_text(file, text):
#     if file is not None:
#         return file.read().decode("utf-8", errors="ignore")
#     return text.strip()

# doc_a = load_text(file_a, text_a)
# doc_b = load_text(file_b, text_b)

# # =====================================================
# # PROCESS
# # =====================================================

# if st.button("🔍 Compare Citations"):

#     if not doc_a or not doc_b:
#         st.error("❌ Please provide both documents.")
#         st.stop()

#     cites_a = extract_citep(doc_a)
#     cites_b = extract_citep(doc_b)

#     set_a = set(cites_a)
#     set_b = set(cites_b)

#     common = sorted(set_a & set_b)
#     only_a = sorted(set_a - set_b)
#     only_b = sorted(set_b - set_a)

#     # =====================================================
#     # METRICS
#     # =====================================================

#     st.divider()
#     st.header("📊 Summary")

#     m1, m2, m3, m4 = st.columns(4)
#     m1.metric("Doc A Citations", len(set_a))
#     m2.metric("Doc B Citations", len(set_b))
#     m3.metric("Common", len(common))
#     m4.metric("Total Unique", len(set_a | set_b))

#     # =====================================================
#     # TABLES
#     # =====================================================

#     tab1, tab2, tab3, tab4 = st.tabs([
#         "✅ Common",
#         "🅰 Only in A",
#         "🅱 Only in B",
#         "📋 All"
#     ])

#     with tab1:
#         df = pd.DataFrame({"CitationKey": common})
#         st.dataframe(df, use_container_width=True)

#     with tab2:
#         df = pd.DataFrame({"CitationKey": only_a})
#         st.dataframe(df, use_container_width=True)

#     with tab3:
#         df = pd.DataFrame({"CitationKey": only_b})
#         st.dataframe(df, use_container_width=True)

#     with tab4:
#         df_all = pd.concat([
#             build_table(cites_a, "A"),
#             build_table(cites_b, "B")
#         ]).sort_values(["CitationKey", "Source"])
#         st.dataframe(df_all, use_container_width=True)

#     # =====================================================
#     # DOWNLOADS
#     # =====================================================

#     st.divider()
#     st.header("⬇️ Export")

#     csv_common = df.to_csv(index=False).encode()
#     csv_all = df_all.to_csv(index=False).encode()

#     st.download_button(
#         "Download Common Citations (CSV)",
#         csv_common,
#         file_name="common_citations.csv",
#         mime="text/csv"
#     )

#     st.download_button(
#         "Download All Citations (CSV)",
#         csv_all,
#         file_name="all_citations.csv",
#         mime="text/csv"
#     )

#     # =====================================================
#     # RAW VIEW (OPTIONAL)
#     # =====================================================

#     with st.expander("🔎 Debug View"):
#         st.write("Extracted A:", cites_a)
#         st.write("Extracted B:", cites_b)
