import pandas as pd

def load_papers(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    elif name.endswith(".json"):
        return pd.read_json(uploaded_file)

    else:
        raise ValueError("Unsupported file format")


# import pandas as pd
# from pathlib import Path

# def load_papers(path: Path):
#     if path.suffix == ".csv":
#         return pd.read_csv(path)
#     elif path.suffix == ".json":
#         return pd.read_json(path)
#     else:
#         raise ValueError("Unsupported file format")