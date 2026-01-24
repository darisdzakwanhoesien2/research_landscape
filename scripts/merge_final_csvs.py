from pathlib import Path
import pandas as pd

# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "merged_all.csv"

# =====================================================
# LOAD + MERGE
# =====================================================

dfs = []

print("🔍 Scanning RQ folders...")

for rq_dir in sorted(RAW_DIR.iterdir()):
    if not rq_dir.is_dir():
        continue

    rq = rq_dir.name
    csv_files = list(rq_dir.glob("*_final.csv"))

    if not csv_files:
        print(f"⚠️ No *_final.csv found in {rq_dir}")
        continue

    for csv_path in csv_files:
        print(f"📥 Loading {csv_path}")
        df = pd.read_csv(csv_path)

        # Add provenance columns
        df["RQ"] = rq
        df["SourceFile"] = csv_path.name

        dfs.append(df)

if not dfs:
    raise RuntimeError("❌ No CSV files loaded.")

combined_df = pd.concat(dfs, ignore_index=True)
print(f"📊 Total rows before filtering: {len(combined_df)}")

# =====================================================
# FILTER: REMOVE MISSING ABSTRACTS
# =====================================================

if "Abstract" not in combined_df.columns:
    raise RuntimeError("❌ Column 'Abstract' not found in dataset.")

before_filter = len(combined_df)

# Normalize abstract text
abstract_series = (
    combined_df["Abstract"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Define invalid patterns
INVALID_ABSTRACTS = {
    "",
    "nan",
    "none",
    "(missing abstract)",
    "missing abstract"
}

valid_mask = ~abstract_series.isin(INVALID_ABSTRACTS)

filtered_df = combined_df[valid_mask].copy()

after_filter = len(filtered_df)

print(
    f"🧹 Filtered missing abstracts: "
    f"{before_filter} → {after_filter} "
    f"(removed {before_filter - after_filter})"
)

# =====================================================
# OPTIONAL: DEDUPLICATION (DOI → TITLE FALLBACK)
# =====================================================

if "DOI" in filtered_df.columns:
    before_dedup = len(filtered_df)

    has_doi = filtered_df["DOI"].notna() & (filtered_df["DOI"].astype(str).str.strip() != "")
    with_doi = filtered_df[has_doi].drop_duplicates(subset=["DOI"])
    without_doi = filtered_df[~has_doi].drop_duplicates(subset=["Title"])

    filtered_df = pd.concat([with_doi, without_doi], ignore_index=True)

    after_dedup = len(filtered_df)

    print(
        f"🧬 Deduplicated: "
        f"{before_dedup} → {after_dedup} "
        f"(removed {before_dedup - after_dedup})"
    )

# =====================================================
# SAVE OUTPUT
# =====================================================

filtered_df.to_csv(OUTPUT_PATH, index=False)

print("\n✅ Merge complete!")
print(f"📁 Output file: {OUTPUT_PATH}")
print(f"📊 Final record count: {len(filtered_df)}")


# from pathlib import Path
# import pandas as pd

# # =====================================================
# # PATHS
# # =====================================================

# BASE_DIR = Path(__file__).resolve().parents[1]
# RAW_DIR = BASE_DIR / "data" / "raw"
# OUTPUT_DIR = BASE_DIR / "data" / "processed"
# OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OUTPUT_PATH = OUTPUT_DIR / "merged_all.csv"

# # =====================================================
# # LOAD + MERGE
# # =====================================================

# dfs = []

# for rq_dir in sorted(RAW_DIR.iterdir()):
#     if not rq_dir.is_dir():
#         continue

#     rq = rq_dir.name
#     csv_files = list(rq_dir.glob("*_final.csv"))

#     if not csv_files:
#         print(f"⚠️ No final CSV found in {rq_dir}")
#         continue

#     for csv_path in csv_files:
#         print(f"📥 Loading {csv_path}")
#         df = pd.read_csv(csv_path)
#         df["RQ"] = rq
#         df["SourceFile"] = csv_path.name
#         dfs.append(df)

# if not dfs:
#     raise RuntimeError("❌ No CSV files loaded.")

# combined_df = pd.concat(dfs, ignore_index=True)

# # =====================================================
# # OPTIONAL: DEDUPLICATION
# # =====================================================

# if "DOI" in combined_df.columns:
#     before = len(combined_df)
#     combined_df = combined_df.drop_duplicates(subset=["DOI"])
#     after = len(combined_df)
#     print(f"🧹 Deduplicated by DOI: {before} → {after}")

# # =====================================================
# # SAVE
# # =====================================================

# combined_df.to_csv(OUTPUT_PATH, index=False)
# print(f"✅ Merged dataset saved to:\n{OUTPUT_PATH}")
# print(f"📊 Total records: {len(combined_df)}")
