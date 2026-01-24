import pandas as pd
from pathlib import Path

def load_csv_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["source"] = "csv"
    df["file"] = path.name

    return df
