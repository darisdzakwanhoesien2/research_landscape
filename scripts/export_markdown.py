from pathlib import Path
import pandas as pd
import re

# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = BASE_DIR / "data" / "processed" / "merged_all.csv"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "literature.md"

# =====================================================
# VALIDATION
# =====================================================

if not INPUT_PATH.exists():
    raise FileNotFoundError(f"❌ Input file not found: {INPUT_PATH}")

df = pd.read_csv(INPUT_PATH)

required_cols = {"Title", "DOI", "Abstract"}
missing = required_cols - set(df.columns)

if missing:
    raise RuntimeError(f"❌ Missing required columns: {missing}")

# =====================================================
# HELPERS
# =====================================================

def clean_text(text: str) -> str:
    """Normalize whitespace and remove broken newlines."""
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def slugify(text: str) -> str:
    """Safe filename slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80]


# =====================================================
# MARKDOWN GENERATION
# =====================================================

lines = []
count = 0

for _, row in df.iterrows():
    title = clean_text(row.get("Title"))
    doi = clean_text(row.get("DOI"))
    abstract = clean_text(row.get("Abstract"))

    if not title or not abstract:
        continue

    lines.append(f"## {title}\n")

    if doi:
        lines.append(f"**DOI:** {doi}\n")

    lines.append(f"{abstract}\n")
    lines.append("---\n")

    count += 1

markdown_text = "\n".join(lines)

OUTPUT_PATH.write_text(markdown_text, encoding="utf-8")

print("✅ Markdown export complete")
print(f"📄 Output file: {OUTPUT_PATH}")
print(f"📚 Records exported: {count}")
