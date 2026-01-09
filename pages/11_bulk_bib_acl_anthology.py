import streamlit as st
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(page_title="ACL BibTeX Bulk Downloader", layout="wide")
st.title("⬇️ ACL BibTeX Downloader (Single + Bulk with Logs)")

BASE_DIR = Path("data/acl_anthology")
BASE_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = BASE_DIR / "download_log.csv"

st.markdown("""
This app lets you:

- 🌐 Download **single BibTeX** from URL
- 📦 Bulk download **multiple BibTeX URLs**
- 💾 Store files locally
- 📝 Keep a **download log (filename, url, status, timestamp)**

Perfect for downloading ACL Anthology volume BibTeX files like:

```
https://aclanthology.org/volumes/2025.acl-long.bib
```
""")

# =====================================================
# LOGGING
# =====================================================

if not LOG_FILE.exists():
    pd.DataFrame(columns=["timestamp", "filename", "url", "status", "message"]).to_csv(LOG_FILE, index=False)


def append_log(filename, url, status, message=""):
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "filename": filename,
        "url": url,
        "status": status,
        "message": message,
    }
    df = pd.read_csv(LOG_FILE)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(LOG_FILE, index=False)

# =====================================================
# SIDEBAR: MODE
# =====================================================

st.sidebar.header("⚙️ Download Mode")

mode = st.sidebar.radio(
    "Select mode",
    ["Single Download", "Bulk Download (paste URLs)"]
)

# =====================================================
# SINGLE DOWNLOAD
# =====================================================

st.header("🌐 Single BibTeX Download")

if mode == "Single Download":
    url = st.text_input(
        "BibTeX URL",
        "https://aclanthology.org/volumes/2025.acl-long.bib"
    )

    custom_name = st.text_input("Optional filename (leave empty to auto-detect)")

    if st.button("Download BibTeX"):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()

            if custom_name.strip():
                filename = custom_name
            else:
                filename = url.split("/")[-1]

            save_path = BASE_DIR / filename
            save_path.write_text(r.text, encoding="utf-8")

            append_log(filename, url, "SUCCESS")
            st.success(f"Saved to {save_path}")

        except Exception as e:
            append_log("", url, "FAILED", str(e))
            st.error(f"Download failed: {e}")

# =====================================================
# BULK DOWNLOAD
# =====================================================

st.header("📦 Bulk BibTeX Download")

if mode == "Bulk Download (paste URLs)":
    st.markdown("Paste one URL per line:")

    bulk_text = st.text_area(
        "BibTeX URLs",
        height=200,
        placeholder="https://aclanthology.org/volumes/2025.acl-long.bib\nhttps://aclanthology.org/volumes/2025.emnlp-main.bib"
    )

    if st.button("Start Bulk Download"):
        urls = [u.strip() for u in bulk_text.splitlines() if u.strip()]

        if not urls:
            st.warning("No URLs provided")
        else:
            st.info(f"Starting download of {len(urls)} files")
            progress = st.progress(0)

            success = 0
            fail = 0

            for i, url in enumerate(urls):
                try:
                    r = requests.get(url, timeout=30)
                    r.raise_for_status()

                    filename = url.split("/")[-1]
                    save_path = BASE_DIR / filename
                    save_path.write_text(r.text, encoding="utf-8")

                    append_log(filename, url, "SUCCESS")
                    success += 1

                except Exception as e:
                    append_log("", url, "FAILED", str(e))
                    fail += 1

                progress.progress((i + 1) / len(urls))

            st.success(f"Completed: {success} success, {fail} failed")

# =====================================================
# LOG VIEWER
# =====================================================

st.header("📝 Download Logs")

log_df = pd.read_csv(LOG_FILE)

st.dataframe(log_df, use_container_width=True)

st.download_button(
    "Download Log CSV",
    log_df.to_csv(index=False).encode("utf-8"),
    file_name="bibtex_download_log.csv",
    mime="text/csv"
)

# =====================================================
# FILE BROWSER
# =====================================================

st.header("📁 Downloaded Files")

files = sorted(BASE_DIR.glob("*.bib"))

if files:
    file_table = pd.DataFrame({
        "filename": [f.name for f in files],
        "size_kb": [round(f.stat().st_size / 1024, 1) for f in files],
        "path": [str(f) for f in files],
    })

    st.dataframe(file_table, use_container_width=True)
else:
    st.info("No BibTeX files downloaded yet.")
