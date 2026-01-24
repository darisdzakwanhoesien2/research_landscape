from pathlib import Path
from datetime import datetime
import json
import pandas as pd

from pipeline.loaders import load_csv, load_bib
from pipeline.merger import deduplicate
from pipeline.export import export_all


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
INTERIM_DIR = BASE_DIR / "data" / "interim"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REGISTRY_PATH = BASE_DIR / "data" / "registry" / "ingestion_log.json"

INTERIM_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def main():
    all_dfs = []
    inputs = []

    for rq_dir in RAW_DIR.iterdir():
        if not rq_dir.is_dir():
            continue

        rq = rq_dir.name

        for file in rq_dir.iterdir():
            inputs.append(str(file))

            if file.suffix == ".csv":
                df = load_csv(file, rq)

            elif file.suffix == ".bib":
                df = load_bib(file, rq)

            else:
                continue

            df.to_csv(INTERIM_DIR / f"{rq}_normalized.csv", index=False)
            all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)
    deduped = deduplicate(combined)

    outputs = export_all(deduped, PROCESSED_DIR)

    log = {
        "run_id": datetime.utcnow().isoformat(),
        "inputs": inputs,
        "records_raw": len(combined),
        "records_deduped": len(deduped),
        "outputs": {k: str(v) for k, v in outputs.items()}
    }

    REGISTRY_PATH.write_text(json.dumps(log, indent=2))
    print("✅ Ingestion complete")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
