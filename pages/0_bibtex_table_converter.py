import streamlit as st
import pandas as pd
import re
from io import StringIO

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="📚 BibTeX → Table Converter",
    layout="wide"
)

st.title("📚 BibTeX → Table Converter")
st.caption("Paste BibTeX entries and convert them into a structured table.")

# =====================================================
# SAMPLE DATA
# =====================================================
SAMPLE_BIBTEX = """@article{zhang2023dynamic,
  title={Dynamic Heterogeneous Graph Neural Networks for Real-Time Event Prediction},
  author={Zhang, Y. and Liang, H. and Wang, S.},
  journal={IEEE Transactions on Knowledge and Data Engineering},
  volume={35},
  number={4},
  pages={3421--3435},
  year={2023}
}

@inproceedings{wang2022knowledge,
  title={Knowledge-Enhanced Short Text Graph Construction for Social Media Analysis},
  author={Wang, L. and Li, Z.},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence},
  year={2022}
}"""

# =====================================================
# INPUT AREA
# =====================================================
bibtex_text = st.text_area(
    "📥 Paste BibTeX entries here:",
    value=SAMPLE_BIBTEX,
    height=350
)

# =====================================================
# PARSER FUNCTIONS
# =====================================================
def split_entries(text):
    """
    Split BibTeX text into individual entries.
    """
    entries = re.findall(r'@.*?\n}\s*', text, flags=re.DOTALL)
    return entries


def parse_entry(entry_text):
    """
    Parse a single BibTeX entry into dict.
    """
    record = {}

    # Entry type and ID
    header_match = re.search(r'@(\w+)\s*{\s*([^,]+),', entry_text)
    if header_match:
        record["entry_type"] = header_match.group(1)
        record["id"] = header_match.group(2)

    # Key-value pairs
    fields = re.findall(r'(\w+)\s*=\s*[{"](.*?)[}"]\s*,?', entry_text, re.DOTALL)
    for key, value in fields:
        clean_value = " ".join(value.replace("\n", " ").split())
        record[key.lower()] = clean_value

    return record


def parse_bibtex(text):
    """
    Parse full BibTeX text into list of dicts.
    """
    entries = split_entries(text)
    parsed = [parse_entry(e) for e in entries]
    return parsed


# =====================================================
# ACTION
# =====================================================
if st.button("🚀 Convert to Table"):

    try:
        records = parse_bibtex(bibtex_text)

        if not records:
            st.warning("No valid BibTeX entries detected.")
            st.stop()

        df = pd.DataFrame(records)

        # Normalize important columns
        preferred_cols = [
            "id",
            "entry_type",
            "title",
            "author",
            "journal",
            "booktitle",
            "volume",
            "number",
            "pages",
            "year"
        ]

        for col in preferred_cols:
            if col not in df.columns:
                df[col] = ""

        df = df[preferred_cols]

        # Rename for readability
        df = df.rename(columns={
            "author": "authors"
        })

        st.success(f"✅ Parsed {len(df)} BibTeX entries")

        # =====================================================
        # TABLE PREVIEW
        # =====================================================
        st.subheader("📊 Table Preview")
        edited_df = st.data_editor(df, use_container_width=True)

        # =====================================================
        # DOWNLOADS
        # =====================================================
        st.subheader("⬇️ Export")

        # CSV
        csv_buffer = StringIO()
        edited_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "📄 Download CSV",
            csv_buffer.getvalue(),
            file_name="bibtex_table.csv",
            mime="text/csv"
        )

        # Markdown
        markdown_table = edited_df.to_markdown(index=False)
        st.download_button(
            "📝 Download Markdown",
            markdown_table,
            file_name="bibtex_table.md",
            mime="text/markdown"
        )

        # Show markdown preview
        with st.expander("👀 Preview Markdown"):
            st.code(markdown_table, language="markdown")

    except Exception as e:
        st.error(f"❌ Parsing failed: {e}")

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption("Built for literature processing, dataset preparation, and research pipelines.")
