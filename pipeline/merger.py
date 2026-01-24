import pandas as pd


def deduplicate(df):
    """
    Deduplicate using DOI first, fallback to Title.
    """
    df = df.copy()

    has_doi = df["DOI"].notna()
    doi_dedup = df[has_doi].drop_duplicates(subset=["DOI"])

    no_doi = df[~has_doi].drop_duplicates(subset=["Title"])

    return pd.concat([doi_dedup, no_doi], ignore_index=True)
