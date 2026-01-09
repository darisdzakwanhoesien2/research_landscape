import streamlit as st
import pandas as pd

st.title("🧼 Clean & Download CSV")

if "raw_df" not in st.session_state:
    st.warning("Please upload a file first in Page 1.")
    st.stop()

df = st.session_state["raw_df"].copy()

# =========================================================
# STEP 1 — Keep only relevant columns
# =========================================================

keep_cols = [
    c for c in df.columns
    if (
        "badge" in c.lower()
        or "card" in c.lower()
        or c.lower().startswith("d-block")
    )
]

df = df[keep_cols]

st.write("Kept columns:")
st.code(keep_cols)

# =========================================================
# STEP 2 — Detect abstract-only rows
# =========================================================

first_col = df.columns[0]
last_col = df.columns[-1]

df["__is_abstract__"] = df[first_col].isna() & df[last_col].notna()

# =========================================================
# STEP 3 — Merge abstract rows upward
# =========================================================

rows = []
current_abstract = ""

for _, row in df.iterrows():
    if row["__is_abstract__"]:
        current_abstract += " " + str(row[last_col])
    else:
        if current_abstract and rows:
            rows[-1]["abstract"] = current_abstract.strip()
            current_abstract = ""

        r = row.to_dict()
        r["abstract"] = ""
        rows.append(r)

clean = pd.DataFrame(rows)

# =========================================================
# STEP 4 — Extract authors
# =========================================================

author_cols = [
    c for c in clean.columns
    if c.lower().startswith("d-block") and "href" not in c.lower()
]

def collect_authors(row):
    names = []
    for c in author_cols:
        v = row.get(c)
        if isinstance(v, str) and 2 < len(v) < 60:
            names.append(v.strip())
    return ", ".join(names)

clean["authors"] = clean.apply(collect_authors, axis=1)

# =========================================================
# STEP 5 — Extract title
# =========================================================

def get_title(row):
    for c in author_cols:
        v = row.get(c)
        if isinstance(v, str) and len(v) > 40:
            return v.strip()
    return ""

clean["title"] = clean.apply(get_title, axis=1)

# =========================================================
# STEP 6 — Final schema
# =========================================================

pdf_col = next((c for c in clean.columns if "badge href" in c.lower()), None)
bib_col = next((c for c in clean.columns if "badge href 2" in c.lower()), None)

final = pd.DataFrame({
    "pdf": clean[pdf_col] if pdf_col else None,
    "bib": clean[bib_col] if bib_col else None,
    "title": clean["title"],
    "authors": clean["authors"],
    "abstract": clean["abstract"],
})

final = final.dropna(subset=["title"])

# =========================================================
# DISPLAY
# =========================================================

st.success(f"Cleaned dataset: {final.shape[0]} papers")

st.subheader("Preview Clean Data")
st.dataframe(final.head(20))

# =========================================================
# DOWNLOAD
# =========================================================

csv = final.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download Clean CSV",
    data=csv,
    file_name="acl_clean.csv",
    mime="text/csv"
)
