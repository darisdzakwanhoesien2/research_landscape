import pandas as pd

STANDARD_COLUMNS = [
    "source", "file", "id", "title", "authors",
    "journal", "year", "doi", "abstract"
]

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    rename_map = {
        "author": "authors",
        "publication": "journal",
        "summary": "abstract",
    }
    df = df.rename(columns=rename_map)

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[STANDARD_COLUMNS]

def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    if "doi" in df.columns:
        df = df.sort_values("doi").drop_duplicates("doi", keep="first")

    df = df.sort_values("title").drop_duplicates("title", keep="first")
    return df.reset_index(drop=True)
