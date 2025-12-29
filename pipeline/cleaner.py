import pandas as pd
# def clean_keywords(df: pd.DataFrame):
#     df = df.copy()
#     df["keywords"] = (
#         df["keywords"]
#         .fillna("")
#         .str.lower()
#         .str.replace("-", " ")
#         .str.split(";")
#     )
#     df["keywords"] = df["keywords"].apply(lambda x: [k.strip() for k in x if k.strip()])
#     return df

def filter_nonempty_keywords(df):
    return df[df["keywords"].apply(len) > 0]


def clean_keywords(df):
    df = df.copy()

    if "keywords" not in df.columns:
        df["keywords"] = [[] for _ in range(len(df))]
        return df

    def parse_keywords(x):
        if not isinstance(x, str):
            return []
        if x.strip() == "":
            return []
        return [k.strip().lower() for k in x.split(";") if k.strip()]

    df["keywords"] = df["keywords"].apply(parse_keywords)
    return df


def normalize_columns(df):
    rename_map = {
        "Title": "title",
        "Abstract": "abstract",
        "Tags": "keywords",
        "Journal": "venue",
        "Year": "year"
    }

    df = df.rename(columns=rename_map)

    for col in ["keywords", "abstract"]:
        if col not in df:
            df[col] = ""

    return df

def clean_abstracts(df):
    df = df.copy()
    df["abstract"] = (
        df["abstract"]
        .fillna("")
        .replace("(missing abstract)", "")
        .str.strip()
    )
    return df

def infer_source_type(df):
    """
    Infer whether a paper is from a journal or conference
    based on venue name heuristics.
    """
    df = df.copy()

    def classify(venue):
        if not isinstance(venue, str):
            return "unknown"

        v = venue.lower()

        conference_keywords = [
            "conference",
            "proceedings",
            "symposium",
            "workshop",
            "congress",
            "ieee",
            "acm"
        ]

        if any(k in v for k in conference_keywords):
            return "conference"

        return "journal"

    df["source_type"] = df["venue"].apply(classify)
    return df
