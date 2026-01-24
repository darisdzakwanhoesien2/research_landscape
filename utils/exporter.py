import pandas as pd
from pathlib import Path

def export_csv(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False)

def export_markdown(df: pd.DataFrame, path: Path):
    lines = []
    for _, row in df.iterrows():
        title = row.get("title") or ""
        abstract = row.get("abstract") or ""
        lines.append(f"## {title}\n\n{abstract}\n")

    path.write_text("\n\n".join(lines), encoding="utf-8")
