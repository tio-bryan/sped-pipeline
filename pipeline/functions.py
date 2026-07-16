from pathlib import Path
import pandas as pd


# Append only new rows to an existing parquet file without duplicating data
def save_parquet_idempotent(df: pd.DataFrame, file_path: str | Path) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # If new DF is empty, just create the parquet file if it doesn't exist and return
    if df.empty:
        if not path.exists():
            df.to_parquet(path, engine='pyarrow', compression='snappy')
        return

    # If the parquet file already exists, read it and concatenate with the new DF and drop duplicates
    if path.exists() and path.stat().st_size > 0:
        existing_df = pd.read_parquet(path)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        df = combined_df.drop_duplicates(ignore_index=True)

    df.to_parquet(path, engine='pyarrow', compression='snappy')
