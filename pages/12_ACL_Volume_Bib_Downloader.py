import streamlit as st
import json
import pandas as pd
from pathlib import Path
import re

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="ACL Volume BibTeX Builder", layout="wide")
st.title("📚 ACL Volume → BibTeX Link Generator")

DATA_PATH = Path("data/acl_anthology_venue/acl/extracted.json")
BASE_URL = "https://aclanthology.org"

st.markdown("""
This page extracts **ACL volume links** from scraped venue JSON and converts them into:
/volumes/2025.acl-long/   →
[https://aclanthology.org/volumes/2025.acl-long.bib](https://aclanthology.org/volumes/2025.acl-long.bib)
You can then use these URLs for:
- bulk BibTeX download
- batch processing in the BibTeX dashboard
""")

# =====================================================
# LOAD JSON
# =====================================================

if not DATA_PATH.exists():
    st.error(f"File not found: {DATA_PATH}")
    st.stop()

with st.spinner("Loading venue JSON..."):
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

links = data.get("links", {})

st.success(f"Loaded {len(links)} raw links")

# =====================================================
# EXTRACT VOLUME LINKS
# =====================================================

rows = []

volume_pattern = re.compile(r"^/volumes/.+/$")

for title, url in links.items():

    if not isinstance(url, str):
        continue

    if volume_pattern.match(url):
        bib_url = f"{BASE_URL}{url}.bib" if not url.endswith(".bib") else f"{BASE_URL}{url}"

        rows.append({
            "title": title,
            "volume_path": url,
            "bib_url": bib_url
        })

df = pd.DataFrame(rows)

st.success(f"Detected {len(df)} volume BibTeX links")

# =====================================================
# FILTERING
# =====================================================

st.subheader("🔎 Filter")

c1, c2 = st.columns(2)

text_filter = c1.text_input("Search in title")
year_filter = c2.text_input("Filter year (e.g. 2025)")

mask = pd.Series(True, index=df.index)

if text_filter:
    mask &= df["title"].str.lower().str.contains(text_filter.lower(), na=False)

if year_filter:
    mask &= df["volume_path"].str.contains(year_filter)

filtered = df[mask]

st.info(f"Showing {len(filtered)} volumes")

# =====================================================
# TABLE
# =====================================================

st.subheader("📄 Volume → BibTeX URLs")

st.dataframe(filtered, use_container_width=True)

# =====================================================
# BULK URL LIST
# =====================================================

st.subheader("📋 Bulk Download List")

url_text = "\n".join(filtered["bib_url"].tolist())

st.text_area(
    "Copy-paste into wget / curl / downloader",
    value=url_text,
    height=250
)

# =====================================================
# EXPORT
# =====================================================

st.subheader("⬇️ Export")

st.download_button(
    "Download CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="acl_volume_bib_links.csv",
    mime="text/csv"
)

st.download_button(
    "Download URL List (.txt)",
    url_text.encode("utf-8"),
    file_name="acl_volume_bib_urls.txt",
    mime="text/plain"
)

# =====================================================
# QUICK COMMAND GENERATOR
# =====================================================

st.subheader("💻 wget Command")

wget_script = "\n".join([f"wget {u}" for u in filtered["bib_url"]])

st.text_area(
    "Bulk download command",
    value=wget_script,
    height=200
)