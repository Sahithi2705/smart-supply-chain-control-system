from pathlib import Path
import pandas as pd
import numpy as np


def write_parquet(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow", compression="zstd")


def add_source_metadata(df: pd.DataFrame, source: str, source_id_col: str):
    out = df.copy()
    out["source_system"] = source
    out["source_record_id"] = out[source_id_col].astype("string")
    return out


def stable_key(*values):
    import hashlib
    text = "|".join("" if pd.isna(v) else str(v).strip().casefold() for v in values)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def parse_dates(df, columns, dayfirst=False):
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce", dayfirst=dayfirst)
    return out


def assert_finite_numeric(df: pd.DataFrame, columns, context: str):
    """Reject +/- infinity while allowing documented null/missing source values."""
    for column in columns:
        if column not in df.columns:
            continue
        values = pd.to_numeric(df[column], errors="coerce").to_numpy(dtype="float64", na_value=np.nan)
        if np.isinf(values).any():
            raise ValueError(f"{context}.{column} contains infinite numeric values")
