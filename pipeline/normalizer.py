TARGET_COLUMNS = [
    "RQ",
    "Source",
    "DOI",
    "Title",
    "Authors",
    "Journal",
    "Year",
    "Abstract",
    "LitmapsId",
    "Cited By",
    "References",
    "PubMedId",
    "Tags",
]


def normalize_dataframe(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    for col in TARGET_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[TARGET_COLUMNS]
