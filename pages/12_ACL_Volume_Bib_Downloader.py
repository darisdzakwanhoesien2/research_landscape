import streamlit as st
import json
import pandas as pd
from pathlib import Path
import re

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="ACL Volume BibTeX Builder", layout="wide")
st.title("📚 ACL Venue → Volume BibTeX Link Generator")

BASE_DIR = Path("data/acl_anthology_venue")
BASE_URL = "https://aclanthology.org"

st.markdown("""
Select an ACL-related **venue dataset** and extract all volume-level BibTeX links:

`/volumes/2025.acl-long/` →  
`https://aclanthology.org/volumes/2025.acl-long.bib`
""")

# =====================================================
# DATASET DROPDOWN
# =====================================================

venue_dirs = sorted([
    p for p in BASE_DIR.iterdir()
    if p.is_dir() and (p / "extracted.json").exists()
])

if not venue_dirs:
    st.error(f"No venue folders with extracted.json found in {BASE_DIR}")
    st.stop()

venue_map = {p.name: p for p in venue_dirs}

selected_venue = st.selectbox(
    "📁 Select Venue",
    options=list(venue_map.keys()),
    index=list(venue_map.keys()).index("acl") if "acl" in venue_map else 0
)

DATA_PATH = venue_map[selected_venue] / "extracted.json"

st.caption(f"Using dataset: `{DATA_PATH}`")

# =====================================================
# LOAD JSON
# =====================================================

with st.spinner("Loading venue JSON..."):
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        st.error(f"Failed to load JSON: {e}")
        st.stop()

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
        clean_path = url.rstrip("/")
        bib_url = f"{BASE_URL}{clean_path}.bib"

        rows.append({
            "title": title,
            "volume_path": url,
            "bib_url": bib_url
        })

df = pd.DataFrame(rows)

if df.empty:
    st.warning("No volume links detected in this venue.")
    st.stop()

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

st.dataframe(filtered, use_container_width=True, hide_index=True)

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
    "⬇️ Download CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name=f"{selected_venue}_volume_bib_links.csv",
    mime="text/csv"
)

st.download_button(
    "⬇️ Download URL List (.txt)",
    url_text.encode("utf-8"),
    file_name=f"{selected_venue}_volume_bib_urls.txt",
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


# import streamlit as st
# import json
# import pandas as pd
# from pathlib import Path
# import re

# # =====================================================
# # CONFIG
# # =====================================================

# st.set_page_config(page_title="ACL Volume BibTeX Builder", layout="wide")
# st.title("📚 ACL Volume → BibTeX Link Generator")

# DATA_PATH = Path("data/acl_anthology_venue/acl/extracted.json")
# BASE_URL = "https://aclanthology.org"

# st.markdown("""
# This page extracts **ACL volume links** from scraped venue JSON and converts them into:

# `/volumes/2025.acl-long/` →  
# `https://aclanthology.org/volumes/2025.acl-long.bib`

# You can use these URLs for:
# - bulk BibTeX download
# - batch processing in your BibTeX tools
# """)

# # =====================================================
# # LOAD JSON
# # =====================================================

# if not DATA_PATH.exists():
#     st.error(f"❌ File not found: {DATA_PATH}")
#     st.stop()

# with st.spinner("Loading venue JSON..."):
#     data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

# links = data.get("links", {})

# st.success(f"Loaded {len(links)} raw links")

# # =====================================================
# # EXTRACT VOLUME LINKS
# # =====================================================

# rows = []

# volume_pattern = re.compile(r"^/volumes/.+/$")

# for title, url in links.items():

#     if not isinstance(url, str):
#         continue

#     if volume_pattern.match(url):

#         # ---- FIX: remove trailing slash before adding .bib
#         clean_path = url.rstrip("/")
#         bib_url = f"{BASE_URL}{clean_path}.bib"

#         rows.append({
#             "title": title,
#             "volume_path": url,
#             "bib_url": bib_url
#         })

# df = pd.DataFrame(rows)

# if df.empty:
#     st.warning("No volume links detected.")
#     st.stop()

# st.success(f"Detected {len(df)} volume BibTeX links")

# # =====================================================
# # FILTERING
# # =====================================================

# st.subheader("🔎 Filter")

# c1, c2 = st.columns(2)

# text_filter = c1.text_input("Search in title")
# year_filter = c2.text_input("Filter year (e.g. 2025)")

# mask = pd.Series(True, index=df.index)

# if text_filter:
#     mask &= df["title"].str.lower().str.contains(text_filter.lower(), na=False)

# if year_filter:
#     mask &= df["volume_path"].str.contains(year_filter)

# filtered = df[mask]

# st.info(f"Showing {len(filtered)} volumes")

# # =====================================================
# # TABLE
# # =====================================================

# st.subheader("📄 Volume → BibTeX URLs")

# st.dataframe(
#     filtered,
#     use_container_width=True,
#     hide_index=True
# )

# # =====================================================
# # BULK URL LIST
# # =====================================================

# st.subheader("📋 Bulk Download List")

# url_text = "\n".join(filtered["bib_url"].tolist())

# st.text_area(
#     "Copy-paste into wget / curl / downloader",
#     value=url_text,
#     height=250
# )

# # =====================================================
# # EXPORT
# # =====================================================

# st.subheader("⬇️ Export")

# st.download_button(
#     "⬇️ Download CSV",
#     filtered.to_csv(index=False).encode("utf-8"),
#     file_name="acl_volume_bib_links.csv",
#     mime="text/csv"
# )

# st.download_button(
#     "⬇️ Download URL List (.txt)",
#     url_text.encode("utf-8"),
#     file_name="acl_volume_bib_urls.txt",
#     mime="text/plain"
# )

# # =====================================================
# # QUICK COMMAND GENERATOR
# # =====================================================

# st.subheader("💻 wget Command")

# wget_script = "\n".join([f"wget {u}" for u in filtered["bib_url"]])

# st.text_area(
#     "Bulk download command",
#     value=wget_script,
#     height=200
# )


# import streamlit as st
# import json
# import pandas as pd
# from pathlib import Path
# import re

# # =====================================================
# # CONFIG
# # =====================================================

# st.set_page_config(page_title="ACL Volume BibTeX Builder", layout="wide")
# st.title("📚 ACL Volume → BibTeX Link Generator")

# DATA_PATH = Path("data/acl_anthology_venue/acl/extracted.json")
# BASE_URL = "https://aclanthology.org"

# st.markdown("""
# This page extracts **ACL volume links** from scraped venue JSON and converts them into:
# /volumes/2025.acl-long/   →
# [https://aclanthology.org/volumes/2025.acl-long.bib](https://aclanthology.org/volumes/2025.acl-long.bib)
# You can then use these URLs for:
# - bulk BibTeX download
# - batch processing in the BibTeX dashboard
# """)

# # =====================================================
# # LOAD JSON
# # =====================================================

# if not DATA_PATH.exists():
#     st.error(f"File not found: {DATA_PATH}")
#     st.stop()

# with st.spinner("Loading venue JSON..."):
#     data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

# links = data.get("links", {})

# st.success(f"Loaded {len(links)} raw links")

# # =====================================================
# # EXTRACT VOLUME LINKS
# # =====================================================

# rows = []

# volume_pattern = re.compile(r"^/volumes/.+/$")

# for title, url in links.items():

#     if not isinstance(url, str):
#         continue

#     if volume_pattern.match(url):
#         bib_url = f"{BASE_URL}{url}.bib" if not url.endswith(".bib") else f"{BASE_URL}{url}"

#         rows.append({
#             "title": title,
#             "volume_path": url,
#             "bib_url": bib_url
#         })

# df = pd.DataFrame(rows)

# st.success(f"Detected {len(df)} volume BibTeX links")

# # =====================================================
# # FILTERING
# # =====================================================

# st.subheader("🔎 Filter")

# c1, c2 = st.columns(2)

# text_filter = c1.text_input("Search in title")
# year_filter = c2.text_input("Filter year (e.g. 2025)")

# mask = pd.Series(True, index=df.index)

# if text_filter:
#     mask &= df["title"].str.lower().str.contains(text_filter.lower(), na=False)

# if year_filter:
#     mask &= df["volume_path"].str.contains(year_filter)

# filtered = df[mask]

# st.info(f"Showing {len(filtered)} volumes")

# # =====================================================
# # TABLE
# # =====================================================

# st.subheader("📄 Volume → BibTeX URLs")

# st.dataframe(filtered, use_container_width=True)

# # =====================================================
# # BULK URL LIST
# # =====================================================

# st.subheader("📋 Bulk Download List")

# url_text = "\n".join(filtered["bib_url"][:-1].tolist())

# st.text_area(
#     "Copy-paste into wget / curl / downloader",
#     value=url_text,
#     height=250
# )

# # =====================================================
# # EXPORT
# # =====================================================

# st.subheader("⬇️ Export")

# st.download_button(
#     "Download CSV",
#     filtered.to_csv(index=False).encode("utf-8"),
#     file_name="acl_volume_bib_links.csv",
#     mime="text/csv"
# )

# st.download_button(
#     "Download URL List (.txt)",
#     url_text.encode("utf-8"),
#     file_name="acl_volume_bib_urls.txt",
#     mime="text/plain"
# )

# # =====================================================
# # QUICK COMMAND GENERATOR
# # =====================================================

# st.subheader("💻 wget Command")

# wget_script = "\n".join([f"wget {u}" for u in filtered["bib_url"]])

# st.text_area(
#     "Bulk download command",
#     value=wget_script,
#     height=200
# )