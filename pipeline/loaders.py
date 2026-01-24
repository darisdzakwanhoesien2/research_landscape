import pandas as pd
import bibtexparser
from .normalizer import normalize_dataframe


def load_csv(path, rq):
    df = pd.read_csv(path)
    df["RQ"] = rq
    df["Source"] = "csv"
    return normalize_dataframe(df)


def load_bib(path, rq):
    with open(path, "r", encoding="utf-8") as f:
        bib_db = bibtexparser.load(f)

    rows = []

    for entry in bib_db.entries:
        rows.append({
            "RQ": rq,
            "Source": "bib",
            "DOI": entry.get("doi"),
            "Title": entry.get("title"),
            "Authors": entry.get("author"),
            "Journal": entry.get("journal") or entry.get("booktitle"),
            "Year": entry.get("year"),
            "Abstract": entry.get("abstract"),
            "LitmapsId": None,
            "Cited By": None,
            "References": None,
            "PubMedId": entry.get("pmid"),
            "Tags": entry.get("keywords"),
        })

    df = pd.DataFrame(rows)
    return normalize_dataframe(df)
