from pathlib import Path


def export_all(df, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "merged_all.csv"
    json_path = output_dir / "merged_all.json"
    parquet_path = output_dir / "merged_all.parquet"

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)
    df.to_parquet(parquet_path)

    return {
        "csv": csv_path,
        "json": json_path,
        "parquet": parquet_path
    }
