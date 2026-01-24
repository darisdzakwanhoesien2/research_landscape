import streamlit as st
import pandas as pd
from utils.bib_utils import (
    extract_citations_from_aux,
    load_bib_entries,
    filter_bib_entries,
    export_bib
)

st.set_page_config(layout="wide")
st.title("📚 AUX → Filtered BibTeX Generator")

st.markdown("""
Upload:
- ✅ a `.aux` file (from LaTeX build)
- ✅ a `.bib` file (reference database)

The app will extract citation keys and generate a filtered `.bib`.
""")

# ======================================
# Upload files
# ======================================
col1, col2 = st.columns(2)

with col1:
    aux_file = st.file_uploader("Upload .aux file", type=["aux"])

with col2:
    bib_file = st.file_uploader("Upload .bib file", type=["bib"])


if aux_file and bib_file:

    aux_text = aux_file.read().decode("utf-8", errors="ignore")
    bib_text = bib_file.read().decode("utf-8", errors="ignore")

    # ======================================
    # Parse
    # ======================================
    citation_keys = extract_citations_from_aux(aux_text)
    bib_entries = load_bib_entries(bib_text)
    matched, missing = filter_bib_entries(bib_entries, citation_keys)

    st.success(f"Found {len(citation_keys)} citation keys")

    # ======================================
    # Layout
    # ======================================
    t1, t2, t3 = st.tabs(["📌 Citation Keys", "✅ Matched Entries", "⚠️ Missing Keys"])

    # -----------------------
    # Citation keys
    # -----------------------
    with t1:
        st.subheader("Extracted Citation Keys")
        st.write(sorted(citation_keys))

    # -----------------------
    # Matched entries
    # -----------------------
    with t2:
        st.subheader(f"Matched Entries ({len(matched)})")

        if matched:
            df = pd.DataFrame(matched.values())
            st.dataframe(df, use_container_width=True)

            # Export bib
            bib_output = export_bib(matched)

            st.download_button(
                "⬇️ Download filtered_references.bib",
                data=bib_output,
                file_name="filtered_references.bib",
                mime="text/plain"
            )
        else:
            st.warning("No matching BibTeX entries found.")

    # -----------------------
    # Missing keys
    # -----------------------
    with t3:
        st.subheader(f"Missing Keys ({len(missing)})")

        if missing:
            st.error("These citation keys were NOT found in the Bib file:")
            st.write(sorted(missing))
        else:
            st.success("All citation keys were found 🎉")

else:
    st.info("Please upload both .aux and .bib files.")
