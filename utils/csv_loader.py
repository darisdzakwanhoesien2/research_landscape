from pathlib import Path

# utils/csv_loader.py
import pandas as pd

def load_csv_from_path(filepath):
    """Load CSV from a given path."""
    return pd.read_csv(filepath)


def load_csv_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["source"] = "csv"
    df["file"] = path.name

    return df
