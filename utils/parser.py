import re
from typing import List, Dict


# =========================================================
# SPLITTING
# =========================================================

def split_into_papers(text: str) -> List[str]:
    """
    Split text into paper blocks.
    """
    blocks = re.split(r"\n(?=[A-Z].+ - arXiv|Save Cite)", text.strip())
    return [b.strip() for b in blocks if len(b.strip()) > 50]


# =========================================================
# EXTRACTION
# =========================================================

def extract_citation_info(text: str) -> Dict:
    cited = re.search(r"Cited by\s+(\d+)", text)
    versions = re.search(r"All\s+(\d+)\s+versions", text)

    return {
        "cited_by": int(cited.group(1)) if cited else None,
        "versions": int(versions.group(1)) if versions else None,
        "pdf_available": "[PDF]" in text
    }


def extract_header(block: str) -> Dict:
    lines = block.split("\n")
    header = lines[0]

    parts = header.split(" - ")

    title = parts[0].strip()

    authors = []
    venue = None
    year = None
    source = None

    if len(parts) >= 2:
        authors = [a.strip() for a in parts[1].split(",")]

    if len(parts) >= 3:
        venue = parts[2].strip()
        year_match = re.search(r"\b(19|20)\d{2}\b", venue)
        if year_match:
            year = int(year_match.group())

    if len(parts) >= 4:
        source = parts[3].strip()

    return {
        "title": title,
        "authors": authors,
        "venue": venue,
        "year": year,
        "source": source
    }


def extract_description_and_highlights(block: str) -> Dict:
    lines = block.split("\n")[1:]

    description_lines = []
    highlights = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.lower().startswith((
            "investigates", "examines", "proposes",
            "performance", "robust", "explains",
            "improvement", "self-"
        )):
            highlights.append(line)
        else:
            description_lines.append(line)

    return {
        "description": " ".join(description_lines),
        "highlights": highlights
    }


# =========================================================
# MAIN PARSER
# =========================================================

def parse_paper_block(block: str) -> Dict:
    header = extract_header(block)
    citation = extract_citation_info(block)
    content = extract_description_and_highlights(block)

    paper_id = re.sub(r"\W+", "_", header["title"].lower())[:80]

    return {
        "paper_id": paper_id,
        **header,
        **content,
        **citation,
        "raw_text": block
    }


def parse_text_to_json(text: str) -> List[Dict]:
    blocks = split_into_papers(text)
    return [parse_paper_block(b) for b in blocks]
