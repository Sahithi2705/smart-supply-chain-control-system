
from pathlib import Path
import shutil

import pandas as pd
import pyarrow.parquet as pq

from config.settings import M5_FILES, CURATED
from transformations.common import write_parquet, assert_finite_numeric


# ==========================================================
# PATHS AND EXPECTED VALUES
# ==========================================================

MODULE_ROOT = Path(__file__).resolve().parents[1]

SALES_SOURCE = (
    MODULE_ROOT
    / "data"
    / "interim"
    / "m5_full"
    / "fact_sales"
    / "part-00000.parquet"
)

EXPECTED_SALES_ROWS = 59_181_090
EXPECTED_PRODUCTS = 3_049
EXPECTED_STORES = 10
EXPECTED_DATES = 1_941


# ==========================================================
# HELPER: PRIMARY KEY VALIDATION
# ==========================================================

def validate_primary_key(df, key, entity):

    if df[key].isna().any():
        raise ValueError(
            f"{entity}: NULL values found in primary key {key}"
        )

    duplicates = df[key].duplicated().sum()

    if duplicates:
        raise ValueError(
            f"{entity}: {duplicates} duplicate primary keys"
        )

    print(f"{entity}: primary key validation passed")


# ==========================================================
# MAIN M5 ETL
# ==========================================================

def run_m5():

    print("\n========== M5 CANONICAL ETL ==========")

    output = CURATED / "m5"
    output.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------
    # 1. VERIFY EXISTING SALES FACT
    # ------------------------------------------------------

    print("\n[1/6] Verifying existing sales fact...")

    if not SALES_SOURCE.exists():
        raise FileNotFoundError(
            f"Existing sales fact not found: {SALES_SOURCE}"
        )

    sales_metadata = pq.ParquetFile(SALES_SOURCE).metadata
    sales_rows = sales_metadata.num_rows

    if sales_rows != EXPECTED_SALES_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_SALES_ROWS:,} sales rows, "
            f"found {sales_rows:,}"
        )

    print(f"Verified sales rows: {sales_rows:,}")

    # ------------------------------------------------------
    # 2. CREATE DIM_DATE
    # ------------------------------------------------------

    print("\n[2/6] Creating dim_date...")

    calendar = pd.read_csv(M5_FILES["calendar"])

    calendar["date"] = pd.to_datetime(
        calendar["date"],
        errors="coerce"
    )

    if calendar["d"].duplicated().any():
        raise ValueError("Duplicate M5 day IDs found.")

    if calendar["date"].isna().any():
        raise ValueError("Invalid dates found in M5 calendar.")

    dim_date = calendar.rename(
        columns={"d": "day_id"}
    ).copy()

    dim_date["source_system"] = "M5"
    dim_date["source_record_id"] = (
        dim_date["day_id"].astype("string")
    )

    validate_primary_key(
        dim_date,
        "day_id",
        "dim_date"
    )

    write_parquet(
        dim_date,
        output / "dim_date" / "part-00000.parquet"
    )

    print(f"dim_date rows: {len(dim_date):,}")

    # ------------------------------------------------------
    # 3. LOAD M5 PRODUCT AND STORE METADATA
    # ------------------------------------------------------

    print("\n[3/6] Creating dim_product and dim_store...")

    sales_meta = pd.read_csv(
        M5_FILES["evaluation"],
        usecols=[
            "id",
            "item_id",
            "dept_id",
            "cat_id",
            "store_id",
            "state_id"
        ],
        dtype="string"
    )

    # Product dimension
    dim_product = (
        sales_meta[
            ["item_id", "dept_id", "cat_id"]
        ]
        .drop_duplicates("item_id")
        .rename(
            columns={
                "item_id": "sku",
                "cat_id": "category_id"
            }
        )
        .copy()
    )

    dim_product["source_system"] = "M5"
    dim_product["source_record_id"] = (
        dim_product["sku"].astype("string")
    )

    validate_primary_key(
        dim_product,
        "sku",
        "dim_product"
    )

    if len(dim_product) != EXPECTED_PRODUCTS:
        raise ValueError(
            f"Expected {EXPECTED_PRODUCTS:,} products, "
            f"found {len(dim_product):,}"
        )

    write_parquet(
        dim_product,
        output / "dim_product" / "part-00000.parquet"
    )

    print(f"dim_product rows: {len(dim_product):,}")

    # Store dimension
    dim_store = (
        sales_meta[
            ["store_id", "state_id"]
        ]
        .drop_duplicates("store_id")
        .copy()
    )

    dim_store["source_system"] = "M5"
    dim_store["source_record_id"] = (
        dim_store["store_id"].astype("string")
    )

    validate_primary_key(
        dim_store,
        "store_id",
        "dim_store"
    )

    if len(dim_store) != EXPECTED_STORES:
        raise ValueError(
            f"Expected {EXPECTED_STORES} stores, "
            f"found {len(dim_store)}"
        )

    write_parquet(
        dim_store,
        output / "dim_store" / "part-00000.parquet"
    )

    print(f"dim_store rows: {len(dim_store):,}")

    # ------------------------------------------------------
    # 4. CREATE FACT_SELL_PRICES
    # ------------------------------------------------------

    print("\n[4/6] Creating fact_sell_prices...")

    prices = pd.read_csv(
        M5_FILES["prices"],
        dtype={
            "store_id": "string",
            "item_id": "string"
        }
    )

    prices["wm_yr_wk"] = pd.to_numeric(
        prices["wm_yr_wk"],
        errors="coerce"
    ).astype("Int32")

    prices["sell_price"] = pd.to_numeric(
        prices["sell_price"],
        errors="coerce"
    )

    assert_finite_numeric(
        prices,
        ["sell_price"],
        "M5.fact_sell_prices"
    )

    prices = prices.rename(
        columns={"item_id": "sku"}
    )

    prices["source_system"] = "M5"

    prices["source_record_id"] = (
        prices["store_id"].astype("string")
        + ":"
        + prices["sku"].astype("string")
        + ":"
        + prices["wm_yr_wk"].astype("string")
    )

    validate_primary_key(
        prices,
        "source_record_id",
        "fact_sell_prices"
    )

    write_parquet(
        prices,
        output / "fact_sell_prices" / "part-00000.parquet"
    )

    print(f"fact_sell_prices rows: {len(prices):,}")

    # ------------------------------------------------------
    # 5. COPY EXISTING FACT_SALES
    # ------------------------------------------------------

    print("\n[5/6] Integrating existing fact_sales...")

    sales_output = (
        output
        / "fact_sales"
        / "part-00000.parquet"
    )

    sales_output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy2(
        SALES_SOURCE,
        sales_output
    )

    copied_rows = pq.ParquetFile(
        sales_output
    ).metadata.num_rows

    if copied_rows != EXPECTED_SALES_ROWS:
        raise ValueError(
            "Curated fact_sales row count validation failed."
        )

    print(f"fact_sales rows: {copied_rows:,}")

    # ------------------------------------------------------
    # 6. VALIDATE ALL FIVE CANONICAL ENTITIES
    # ------------------------------------------------------

    print("\n[6/6] Final M5 entity validation...")

    entity_files = {
        "dim_date": output / "dim_date" / "part-00000.parquet",
        "dim_product": output / "dim_product" / "part-00000.parquet",
        "dim_store": output / "dim_store" / "part-00000.parquet",
        "fact_sell_prices": output / "fact_sell_prices" / "part-00000.parquet",
        "fact_sales": output / "fact_sales" / "part-00000.parquet",
    }

    for entity, file_path in entity_files.items():

        if not file_path.exists():
            raise FileNotFoundError(
                f"{entity} output missing: {file_path}"
            )

        metadata = pq.ParquetFile(file_path).metadata

        print(
            f"{entity}: {metadata.num_rows:,} rows | "
            f"{file_path.stat().st_size / (1024 * 1024):.2f} MB"
        )

    # Sales key uniqueness, checked without loading all rows into RAM.
    import duckdb

    con = duckdb.connect()

    sales_path = str(
        entity_files["fact_sales"].resolve()
    ).replace("\\", "/").replace("'", "''")

    duplicate_sales_keys = con.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT source_record_id, d
            FROM read_parquet('{sales_path}')
            GROUP BY source_record_id, d
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    con.close()

    if duplicate_sales_keys:
        raise ValueError(
            f"fact_sales contains {duplicate_sales_keys:,} "
            "duplicate source_record_id/day combinations."
        )

    print("fact_sales duplicate-key groups: 0")

    print("\n========== M5 ETL COMPLETED SUCCESSFULLY ==========")


if __name__ == "__main__":
    run_m5()
