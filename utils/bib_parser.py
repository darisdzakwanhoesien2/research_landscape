import bibtexparser
import pandas as pd
from pathlib import Path

def parse_bib_file(path: Path) -> pd.DataFrame:
    with open(path) as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)

    records = []
    for entry in bib_database.entries:
        records.append({
            "source": "bib",
            "file": path.name,
            "id": entry.get("ID"),
            "title": entry.get("title"),
            "authors": entry.get("author"),
            "year": entry.get("year"),
            "journal": entry.get("journal") or entry.get("booktitle"),
            "doi": entry.get("doi"),
            "abstract": entry.get("abstract"),
        })

    return pd.DataFrame(records)
