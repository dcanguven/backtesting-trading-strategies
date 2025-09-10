from pathlib import Path
import pandas as pd
from trader.config import PROC_DIR

def save(df: pd.DataFrame, name: str) -> None:
    """DataFrame'i processed klasörüne parquet olarak kaydet."""
    Path(PROC_DIR).mkdir(parents=True, exist_ok=True)
    df.to_parquet(f"{PROC_DIR}/{name}.parquet")

def load_raw() -> pd.DataFrame:
    """data/raw/prices.parquet dosyasını oku."""
    return pd.read_parquet("data/raw/prices.parquet")