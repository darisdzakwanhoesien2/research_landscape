import streamlit as st
from pathlib import Path
import pandas as pd

from services.bib_loader import load_bib_files
from services.matcher import match_entries
from services.mapping_store import save_mapping
from services.latex_fixer import patch_latex, extract_citations
from services.audit import write_audit_log

# -------------------------
# PATHS
# -------------------------

BASE_DIR = Path(__file__).parents[1]

GEN_BIB = BASE_DIR / "data/generated_bib"
GT_BIB = BASE_DIR / "data/groundtruth_bib"
LATEX_DIR = BASE_DIR / "data/latex_generated"
MAPPING_DIR = BASE_DIR / "data/mappings"
LOG_DIR = BASE_DIR / "data/logs"

# -------------------------
# UI
# -------------------------

st.set_page_config(layout="wide")
st.title("📚 Bib Mapping & LaTeX Repair System")

# -------------------------
# FILE SELECTION
# -------------------------

gen_bib_files = sorted(GEN_BIB.glob("*.bib"))
gt_bib_files = sorted(GT_BIB.glob("*.bib"))

st.sidebar.subheader("📂 Select Generated Bib Files")
selected_gen_files = st.sidebar.multiselect(
    "Generated Bib",
    gen_bib_files,
    default=gen_bib_files,
    format_func=lambda p: p.name
)

st.sidebar.subheader("📂 Select Ground Truth Bib Files")
selected_gt_files = st.sidebar.multiselect(
    "Ground Truth Bib",
    gt_bib_files,
    default=gt_bib_files,
    format_func=lambda p: p.name
)

if not selected_gen_files:
    st.warning("⚠️ No generated Bib files selected.")
    st.stop()

if not selected_gt_files:
    st.warning("⚠️ No ground truth Bib files selected.")
    st.stop()

# -------------------------
# LOAD SELECTED FILES
# -------------------------

generated = load_bib_files(selected_gen_files)
groundtruth = load_bib_files(selected_gt_files)

st.sidebar.success(f"Generated entries: {len(generated)}")
st.sidebar.success(f"Ground Truth entries: {len(groundtruth)}")

# -------------------------
# GENERATED BIB TABLE
# -------------------------

st.subheader("📘 Generated Bib Entries")

gen_df = pd.DataFrame([
    {
        "ID": g.get("ID"),
        "Title": g.get("title"),
        "Author": g.get("author"),
        "Year": g.get("year"),
        "Source": g.get("_source_file"),
    }
    for g in generated
])

search = st.text_input("🔍 Search Generated Bib")

if search:
    mask = (
        gen_df["Title"].str.contains(search, case=False, na=False) |
        gen_df["Author"].str.contains(search, case=False, na=False) |
        gen_df["ID"].str.contains(search, case=False, na=False)
    )
    gen_df = gen_df[mask]

st.dataframe(gen_df, use_container_width=True, height=280)

# -------------------------
# MATCHING
# -------------------------

if st.button("🔍 Run Matching"):
    matches = match_entries(generated, groundtruth)
    st.session_state["matches"] = matches

if "matches" in st.session_state:
    df = pd.DataFrame(st.session_state["matches"])
    st.subheader("🔗 Matching Results (Editable)")
    edited = st.data_editor(df, use_container_width=True)
    st.session_state["validated"] = edited

# -------------------------
# SAVE MAPPING
# -------------------------

if st.button("💾 Save Mapping") and "validated" in st.session_state:
    mapping = {
        row["generated_id"]: row["groundtruth_id"]
        for _, row in st.session_state["validated"].iterrows()
        if row["groundtruth_id"]
    }

    path = save_mapping(mapping, MAPPING_DIR)
    st.success(f"Saved mapping → {path.name}")

# -------------------------
# LATEX FIXER
# -------------------------

st.divider()
st.subheader("🧩 Fix LaTeX Citations")

latex_files = list(LATEX_DIR.glob("*.tex"))
selected_tex = st.selectbox("Select LaTeX file", latex_files)

if selected_tex and "validated" in st.session_state:
    raw_text = selected_tex.read_text(encoding="utf-8")

    st.text_area("📄 Original LaTeX", raw_text, height=200)

    mapping = {
        row["generated_id"]: row["groundtruth_id"]
        for _, row in st.session_state["validated"].iterrows()
        if row["groundtruth_id"]
    }

    cited_keys = extract_citations(raw_text)
    unmapped = sorted(set(cited_keys) - set(mapping.keys()))

    if unmapped:
        st.warning(f"⚠️ Unmapped citations detected: {unmapped}")

    if st.button("🛠 Generate Patched LaTeX"):
        patched = patch_latex(raw_text, mapping)
        st.session_state["patched_text"] = patched
        st.text_area("✅ Patched Preview", patched, height=250)

# -------------------------
# OVERWRITE WITH BACKUP
# -------------------------

if "patched_text" in st.session_state:
    st.warning("⚠️ This will overwrite the original LaTeX file.")

    confirm = st.checkbox("I understand and want to overwrite the original file")

    if confirm and st.button("💾 Overwrite Original LaTeX"):
        backup_path = selected_tex.with_suffix(".backup.tex")
        backup_path.write_text(raw_text, encoding="utf-8")

        selected_tex.write_text(
            st.session_state["patched_text"],
            encoding="utf-8"
        )

        audit_payload = {
            "latex_file": selected_tex.name,
            "backup_file": backup_path.name,
            "num_mappings": len(mapping),
            "unmapped": unmapped
        }

        log_path = write_audit_log(LOG_DIR, audit_payload)

        st.success(f"Updated {selected_tex.name}")
        st.info(f"Backup → {backup_path.name}")
        st.info(f"Audit log → {log_path.name}")


# import streamlit as st
# from pathlib import Path
# import pandas as pd

# from services.bib_loader import load_bib_folder
# from services.matcher import match_entries
# from services.mapping_store import save_mapping
# from services.latex_fixer import patch_latex, extract_citations
# from services.audit import write_audit_log

# # -------------------------
# # PATHS
# # -------------------------

# BASE_DIR = Path(__file__).parents[1]

# GEN_BIB = BASE_DIR / "data/generated_bib"
# GT_BIB = BASE_DIR / "data/groundtruth_bib"
# LATEX_DIR = BASE_DIR / "data/latex_generated"
# MAPPING_DIR = BASE_DIR / "data/mappings"
# LOG_DIR = BASE_DIR / "data/logs"

# # -------------------------
# # UI
# # -------------------------

# st.set_page_config(layout="wide")
# st.title("📚 Bib Mapping & LaTeX Repair System")
# st.markdown("This app helps you map generated bibliographic entries to ground truth entries and fix LaTeX citations. https://chatgpt.com/c/69774f23-5504-8327-a1a6-c0bdf099ed72")
# # -------------------------
# # LOAD DATA
# # -------------------------

# generated = load_bib_folder(GEN_BIB)
# groundtruth = load_bib_folder(GT_BIB)

# # -------------------------
# # GENERATED BIB TABLE
# # -------------------------

# st.subheader("📘 Generated Bib Entries")

# if generated:
#     gen_df = pd.DataFrame([
#         {
#             "ID": g.get("ID"),
#             "Title": g.get("title"),
#             "Author": g.get("author"),
#             "Year": g.get("year"),
#             "Source": g.get("_source_file"),
#         }
#         for g in generated
#     ])

#     st.dataframe(
#         gen_df,
#         use_container_width=True,
#         height=300
#     )
# else:
#     st.warning("No generated Bib entries found.")


# st.sidebar.success(f"Generated: {len(generated)} entries")
# st.sidebar.success(f"Ground Truth: {len(groundtruth)} entries")

# # -------------------------
# # MATCHING
# # -------------------------

# if st.button("🔍 Run Matching"):
#     matches = match_entries(generated, groundtruth)
#     st.session_state["matches"] = matches

# if "matches" in st.session_state:
#     df = pd.DataFrame(st.session_state["matches"])
#     st.subheader("🔗 Matching Results (Editable)")
#     edited = st.data_editor(df, use_container_width=True)
#     st.session_state["validated"] = edited

# # -------------------------
# # SAVE MAPPING
# # -------------------------

# if st.button("💾 Save Mapping") and "validated" in st.session_state:
#     mapping = {
#         row["generated_id"]: row["groundtruth_id"]
#         for _, row in st.session_state["validated"].iterrows()
#         if row["groundtruth_id"]
#     }

#     path = save_mapping(mapping, MAPPING_DIR)
#     st.success(f"Saved mapping → {path.name}")

# # -------------------------
# # LATEX FIXER
# # -------------------------

# st.divider()
# st.subheader("🧩 Fix LaTeX Citations")

# latex_files = list(LATEX_DIR.glob("*.tex"))
# selected_tex = st.selectbox("Select LaTeX file", latex_files)

# if selected_tex and "validated" in st.session_state:
#     raw_text = selected_tex.read_text(encoding="utf-8")

#     st.text_area("📄 Original LaTeX", raw_text, height=200)

#     mapping = {
#         row["generated_id"]: row["groundtruth_id"]
#         for _, row in st.session_state["validated"].iterrows()
#         if row["groundtruth_id"]
#     }

#     cited_keys = extract_citations(raw_text)
#     unmapped = sorted(set(cited_keys) - set(mapping.keys()))

#     if unmapped:
#         st.warning(f"⚠️ Unmapped citations detected: {unmapped}")

#     if st.button("🛠 Generate Patched LaTeX"):
#         patched = patch_latex(raw_text, mapping)
#         st.session_state["patched_text"] = patched

#         st.text_area("✅ Patched Preview", patched, height=250)

# # -------------------------
# # OVERWRITE WITH BACKUP
# # -------------------------

# if "patched_text" in st.session_state:
#     st.warning("⚠️ This will overwrite the original LaTeX file.")

#     confirm = st.checkbox("I understand and want to overwrite the original file")

#     if confirm and st.button("💾 Overwrite Original LaTeX"):
#         # Backup
#         backup_path = selected_tex.with_suffix(".backup.tex")
#         backup_path.write_text(raw_text, encoding="utf-8")

#         # Overwrite
#         selected_tex.write_text(
#             st.session_state["patched_text"],
#             encoding="utf-8"
#         )

#         # Audit log
#         audit_payload = {
#             "latex_file": selected_tex.name,
#             "backup_file": backup_path.name,
#             "num_mappings": len(mapping),
#             "unmapped": unmapped
#         }

#         log_path = write_audit_log(LOG_DIR, audit_payload)

#         st.success(f"Updated {selected_tex.name}")
#         st.info(f"Backup → {backup_path.name}")
#         st.info(f"Audit log → {log_path.name}")


# import streamlit as st
# from pathlib import Path
# import pandas as pd

# from services.bib_loader import load_bib_folder
# from services.matcher import match_entries
# from services.mapping_store import save_mapping
# from services.latex_fixer import patch_latex

# # ----------------------------
# # PATHS
# # ----------------------------

# BASE_DIR = Path(__file__).parents[1]

# GEN_BIB = BASE_DIR / "data/generated_bib"
# GT_BIB = BASE_DIR / "data/groundtruth_bib"
# LATEX_DIR = BASE_DIR / "data/latex_generated"
# MAPPING_DIR = BASE_DIR / "data/mappings"

# # ----------------------------
# # UI
# # ----------------------------

# st.set_page_config(layout="wide")
# st.title("📚 Bib Mapping & LaTeX Repair System")
# st.markdown("This app helps you map generated bibliographic entries to ground truth entries and fix LaTeX citations. https://chatgpt.com/c/69774f23-5504-8327-a1a6-c0bdf099ed72")

# # ----------------------------
# # LOAD DATA
# # ----------------------------

# generated = load_bib_folder(GEN_BIB)
# groundtruth = load_bib_folder(GT_BIB)

# st.sidebar.success(f"Generated: {len(generated)} entries")
# st.sidebar.success(f"Ground Truth: {len(groundtruth)} entries")

# # ----------------------------
# # MATCHING
# # ----------------------------

# if st.button("🔍 Run Matching"):
#     matches = match_entries(generated, groundtruth)
#     st.session_state["matches"] = matches

# if "matches" in st.session_state:
#     df = pd.DataFrame(st.session_state["matches"])
#     st.subheader("🔗 Matching Results")
#     edited = st.data_editor(df, use_container_width=True)
#     st.session_state["validated"] = edited

# # ----------------------------
# # SAVE MAPPING
# # ----------------------------

# if st.button("💾 Save Mapping") and "validated" in st.session_state:
#     mapping = {
#         row["generated_id"]: row["groundtruth_id"]
#         for _, row in st.session_state["validated"].iterrows()
#         if row["groundtruth_id"]
#     }

#     path = save_mapping(mapping, MAPPING_DIR)
#     st.success(f"Saved mapping → {path.name}")

# # ----------------------------
# # LATEX PATCHING
# # ----------------------------

# st.divider()
# st.subheader("🧩 Fix LaTeX Citations")

# latex_files = list(LATEX_DIR.glob("*.tex"))
# selected_tex = st.selectbox("Select LaTeX file", latex_files)

# if selected_tex and "validated" in st.session_state:
#     raw_text = selected_tex.read_text(encoding="utf-8")
#     st.text_area("Original LaTeX", raw_text, height=200)

#     if st.button("🛠 Patch LaTeX"):
#         mapping = {
#             row["generated_id"]: row["groundtruth_id"]
#             for _, row in st.session_state["validated"].iterrows()
#             if row["groundtruth_id"]
#         }

#         patched = patch_latex(raw_text, mapping)
#         st.text_area("Patched LaTeX", patched, height=200)

#         output_path = selected_tex.with_suffix(".patched.tex")
#         output_path.write_text(patched, encoding="utf-8")

#         st.success(f"Saved patched LaTeX → {output_path.name}")