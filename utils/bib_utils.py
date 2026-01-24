import re
from typing import Set, Dict
import bibtexparser


# -----------------------------
# Extract citation keys from AUX
# -----------------------------
def extract_citations_from_aux(aux_text: str) -> Set[str]:
    """
    Extract citation keys from LaTeX .aux content.
    Handles:
      \\citation{key1,key2}
      \\abx@aux@cite{key}
    """
    keys = set()

    # Standard \citation{...}
    matches = re.findall(r"\\citation\{([^}]+)\}", aux_text)
    for m in matches:
        for k in m.split(","):
            keys.add(k.strip())

    # Biblatex format
    matches = re.findall(r"\\abx@aux@cite\{([^}]+)\}", aux_text)
    for m in matches:
        keys.add(m.strip())

    return keys


# -----------------------------
# Load bib file
# -----------------------------
def load_bib_entries(bib_text: str) -> Dict[str, dict]:
    bib_database = bibtexparser.loads(bib_text)
    return {entry["ID"]: entry for entry in bib_database.entries}


# -----------------------------
# Filter bib entries by keys
# -----------------------------
def filter_bib_entries(
    bib_entries: Dict[str, dict],
    citation_keys: Set[str],
):
    matched = {}
    missing = []

    for key in citation_keys:
        if key in bib_entries:
            matched[key] = bib_entries[key]
        else:
            missing.append(key)

    return matched, missing


# -----------------------------
# Export bib entries
# -----------------------------
def export_bib(entries: Dict[str, dict]) -> str:
    db = bibtexparser.bibdatabase.BibDatabase()
    db.entries = list(entries.values())
    writer = bibtexparser.bwriter.BibTexWriter()
    return writer.write(db)
