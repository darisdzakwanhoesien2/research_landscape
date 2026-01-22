import streamlit as st
import json
from datetime import datetime
from pathlib import Path

from utils.parser import parse_text_to_json


# =========================================================
# PATH CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw_inputs"
PARSED_DIR = DATA_DIR / "parsed_json"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="📄 Text → JSON Parser",
    layout="wide"
)

st.title("📄 Research Paper Text → JSON Parser")
st.caption("Paste raw paper listings and convert them into structured JSON datasets.")


# =========================================================
# INPUT
# =========================================================

raw_text = st.text_area(
    "📋 Paste Raw Text",
    height=350
)


# =========================================================
# ACTION
# =========================================================

if st.button("🚀 Parse Text"):

    if not raw_text.strip():
        st.warning("Please paste some text.")
        st.stop()

    papers = parse_text_to_json(raw_text)

    st.success(f"✅ Parsed {len(papers)} paper(s)")
    st.subheader("📦 Parsed Preview")
    st.json(papers)

    # -----------------------------------------------------
    # Save JSON
    # -----------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = PARSED_DIR / f"papers_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    st.success(f"💾 Saved to `{output_path.relative_to(BASE_DIR)}`")

    # Download
    json_bytes = json.dumps(papers, indent=2, ensure_ascii=False).encode("utf-8")

    st.download_button(
        "⬇️ Download JSON",
        data=json_bytes,
        file_name=output_path.name,
        mime="application/json"
    )

    # Optional: Save raw text
    raw_path = RAW_DIR / f"raw_{timestamp}.txt"
    raw_path.write_text(raw_text, encoding="utf-8")
