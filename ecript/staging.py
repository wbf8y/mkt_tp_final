"""ETL staging: lee CSVs desde `raw/`, aplica limpieza mínima y escribe a `denormalized/staging/`.

Salida por archivo: `denormalized/staging/<name>.parquet` y `.csv`.
"""
from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
STAGING_DIR = ROOT / "denormalized" / "staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)


COMMON_FILES = [
    'address', 'channel', 'customer', 'product_category', 'product', 'payment',
    'nps_response', 'web_session', 'store', 'shipment', 'sales_order_item', 'sales_order', 'province'
]


def read_csv_if_exists(name):
    p = RAW_DIR / f"{name}.csv"
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, dtype=str, keep_default_na=False, na_values=['', 'NA', 'NaN'])
    except Exception:
        # fallback: try without forcing dtypes
        return pd.read_csv(p)


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    # Trim strings and replace empty strings with NaN
    for c in df.select_dtypes(include=['object']).columns:
        df[c] = df[c].astype(str).str.strip()
        df.loc[df[c] == '', c] = pd.NA
    return df


def parse_common_dates(df: pd.DataFrame) -> pd.DataFrame:
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ('date', 'time', 'timestamp'))]
    for c in date_cols:
        try:
            df[c] = pd.to_datetime(df[c], errors='coerce')
        except Exception:
            pass
    return df


def cast_numeric(df: pd.DataFrame) -> pd.DataFrame:
    # common numeric columns
    for c in df.columns:
        if any(k in c.lower() for k in ('price', 'amount', 'total', 'qty', 'quantity')):
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def build_staging_table(name: str):
    df = read_csv_if_exists(name)
    if df.empty:
        return df
    # lowercase column names for consistency
    df.columns = [c.strip() for c in df.columns]
    df = clean_strings(df)
    df = parse_common_dates(df)
    df = cast_numeric(df)
    # deduplicate using an id-like column if present
    id_cols = [c for c in df.columns if c.endswith('_id') or c == f"{name}_id" or c == 'id']
    if id_cols:
        df = df.drop_duplicates(subset=id_cols).reset_index(drop=True)
    else:
        df = df.drop_duplicates().reset_index(drop=True)
    return df


def write_staging(df: pd.DataFrame, name: str):
    if df is None or df.empty:
        return
    p_parquet = STAGING_DIR / f"{name}.parquet"
    p_csv = STAGING_DIR / f"{name}.csv"
    try:
        df.to_parquet(p_parquet, index=False)
    except Exception:
        # if pyarrow not available, skip parquet write
        pass
    df.to_csv(p_csv, index=False)


def main():
    created = []
    for name in COMMON_FILES:
        df = build_staging_table(name)
        write_staging(df, name)
        if not df.empty:
            created.append((name, len(df)))

    # Adicional: crear una tabla staging_products_enriched que combine product + category
    prod = build_staging_table('product')
    cat = build_staging_table('product_category')
    if not prod.empty:
        if not cat.empty and 'product_category_id' in prod.columns and 'product_category_id' in cat.columns:
            enriched = prod.merge(cat[['product_category_id','product_category_name']].drop_duplicates(), on='product_category_id', how='left')
        else:
            enriched = prod
        write_staging(enriched, 'product_enriched')
        created.append(('product_enriched', len(enriched)))

    print('Staging creado en:', STAGING_DIR)
    for n, cnt in created:
        print(f" - {n}: {cnt} filas")


if __name__ == '__main__':
    main()
