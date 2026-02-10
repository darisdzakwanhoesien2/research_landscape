from pathlib import Path
import bibtexparser

def load_bib_files(files):
    records = []

    for bib_file in files:
        try:
            with open(bib_file, encoding="utf-8") as f:
                db = bibtexparser.load(f)
                for entry in db.entries:
                    entry["_source_file"] = bib_file.name
                    records.append(entry)
        except Exception as e:
            print(f"Failed loading {bib_file}: {e}")

    return records


# from pathlib import Path
# import bibtexparser

# def load_bib_folder(folder: Path):
#     records = []
#     for bib_file in sorted(folder.glob("*.bib")):
#         try:
#             with open(bib_file, encoding="utf-8") as f:
#                 db = bibtexparser.load(f)
#                 for entry in db.entries:
#                     entry["_source_file"] = bib_file.name
#                     records.append(entry)
#         except Exception as e:
#             print(f"Failed loading {bib_file}: {e}")
#     return records


# from pathlib import Path
# import bibtexparser

# def load_bib_folder(folder: Path):
#     records = []
#     for bib_file in folder.glob("*.bib"):
#         with open(bib_file, encoding="utf-8") as f:
#             db = bibtexparser.load(f)
#             for entry in db.entries:
#                 entry["_source_file"] = bib_file.name
#                 records.append(entry)
#     return records