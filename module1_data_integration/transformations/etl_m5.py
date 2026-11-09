
from pathlib import Path
import shutil

import duckdb
import pandas as pd
import pyarrow.parquet as pq

from config.settings import M5_FILES, CURATED, INTERIM
from transformations.common import write_parquet, assert_finite_numeric


# ==========================================================
# PATHS AND EXPECTED VALUES
# ==========================================================

SALES_SOURCE = (
    INTERIM
    / "m5_full_canonical_v2"
    / "fact_sales"
    / "part-00000.parquet"
)

# Separate output to protect existing curated M5 files.
OUTPUT = CURATED / "m5_canonical_v2"

EXPECTED_SALES_ROWS = 59_181_090
EXPECTED_PRODUCTS = 3_049
EXPECTED_STORES = 10
EXPECTED_DATES = 1_969
EXPECTED_PRICE_ROWS = 6_841_121


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
            f"{entity}: {duplicates:,} duplicate primary keys"
        )

    print(f"{entity}: primary key validation passed")


def check_output_is_safe():

    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise FileExistsError(
            f"Output directory is not empty: {OUTPUT}\n"
            "Existing output will not be overwritten. "
            "Choose a new versioned output directory."
        )


# ==========================================================
# MAIN M5 CANONICAL ETL
# ==========================================================

def run_m5():

    print("\n========== M5 CANONICAL ETL ==========")

    print("Intermediate input:", SALES_SOURCE)
    print("Curated output:", OUTPUT)

    # Protect previous output and existing curated data.
    check_output_is_safe()

    # ------------------------------------------------------
    # 1. VERIFY CHUNKED SALES FACT
    # ------------------------------------------------------

    print("\n[1/6] Verifying chunked sales fact...")

    if not SALES_SOURCE.exists():
        raise FileNotFoundError(
            f"M5 chunked sales fact not found: {SALES_SOURCE}"
        )

    sales_metadata = pq.ParquetFile(SALES_SOURCE).metadata
    sales_rows = sales_metadata.num_rows

    if sales_rows != EXPECTED_SALES_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_SALES_ROWS:,} sales rows, "
            f"found {sales_rows:,}"
        )

    print(f"Verified sales rows: {sales_rows:,}")

    sales_schema = pq.read_schema(SALES_SOURCE)

    required_sales_columns = {
        "sales_date",
        "sku",
        "store_id",
        "quantity_sold",
        "unit_price",
        "source_system",
        "source_record_id",
        "d",
    }

    missing_columns = (
        required_sales_columns - set(sales_schema.names)
    )

    if missing_columns:
        raise ValueError(
            f"M5 sales fact is missing columns: "
            f"{sorted(missing_columns)}"
        )

    # ------------------------------------------------------
    # 2. CREATE DIM_DATE
    # ------------------------------------------------------

    print("\n[2/6] Creating dim_date...")

    calendar = pd.read_csv(M5_FILES["calendar"])

    # Match the Parquet Date type in fact_sales.sales_date.
    calendar["date"] = pd.to_datetime(
        calendar["date"],
        errors="raise"
    ).dt.date

    if calendar["d"].duplicated().any():
        raise ValueError("Duplicate M5 calendar day IDs found.")

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

    if len(dim_date) != EXPECTED_DATES:
        raise ValueError(
            f"Expected {EXPECTED_DATES:,} dates, "
            f"found {len(dim_date):,}"
        )

    write_parquet(
        dim_date,
        OUTPUT / "dim_date" / "part-00000.parquet"
    )

    print(f"dim_date rows: {len(dim_date):,}")

    # ------------------------------------------------------
    # 3. CREATE DIM_PRODUCT AND DIM_STORE
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
            "state_id",
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
                "cat_id": "category_id",
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
        OUTPUT / "dim_product" / "part-00000.parquet"
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
        OUTPUT / "dim_store" / "part-00000.parquet"
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
            "item_id": "string",
        }
    )

    prices["wm_yr_wk"] = pd.to_numeric(
        prices["wm_yr_wk"],
        errors="raise"
    ).astype("int32")

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
        columns={
            "item_id": "sku",
            "sell_price": "unit_price",
        }
    )

    prices["source_system"] = "M5"

    prices["source_record_id"] = (
        prices["store_id"]
        + ":"
        + prices["sku"]
        + ":"
        + prices["wm_yr_wk"].astype("string")
    )

    validate_primary_key(
        prices,
        "source_record_id",
        "fact_sell_prices"
    )

    if len(prices) != EXPECTED_PRICE_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_PRICE_ROWS:,} price rows, "
            f"found {len(prices):,}"
        )

    prices = prices[
        [
            "store_id",
            "sku",
            "wm_yr_wk",
            "unit_price",
            "source_system",
            "source_record_id",
        ]
    ]

    write_parquet(
        prices,
        OUTPUT / "fact_sell_prices" / "part-00000.parquet"
    )

    print(f"fact_sell_prices rows: {len(prices):,}")

    # ------------------------------------------------------
    # 5. INTEGRATE FACT_SALES
    # ------------------------------------------------------

    print("\n[5/6] Integrating fact_sales...")

    sales_output = (
        OUTPUT
        / "fact_sales"
        / "part-00000.parquet"
    )

    sales_output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Copy the validated chunked Parquet file unchanged.
    shutil.copy2(SALES_SOURCE, sales_output)

    copied_rows = pq.ParquetFile(
        sales_output
    ).metadata.num_rows

    if copied_rows != EXPECTED_SALES_ROWS:
        raise ValueError(
            "Curated fact_sales row count validation failed."
        )

    print(f"fact_sales rows: {copied_rows:,}")

    # ------------------------------------------------------
    # 6. VALIDATE ALL FIVE ENTITIES
    # ------------------------------------------------------

    print("\n[6/6] Final M5 entity validation...")

    entity_files = {
        "dim_date": OUTPUT / "dim_date" / "part-00000.parquet",
        "dim_product": OUTPUT / "dim_product" / "part-00000.parquet",
        "dim_store": OUTPUT / "dim_store" / "part-00000.parquet",
        "fact_sell_prices": OUTPUT / "fact_sell_prices" / "part-00000.parquet",
        "fact_sales": OUTPUT / "fact_sales" / "part-00000.parquet",
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

    # Validate fact_sales source key uniqueness.
    con = duckdb.connect()

    try:
        sales_path = (
            str(entity_files["fact_sales"].resolve())
            .replace("\\", "/")
            .replace("'", "''")
        )

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

    finally:
        con.close()

    if duplicate_sales_keys:
        raise ValueError(
            f"fact_sales contains {duplicate_sales_keys:,} "
            "duplicate source_record_id/day combinations."
        )

    print("fact_sales duplicate-key groups: 0")

    print("\n========== M5 ETL COMPLETED SUCCESSFULLY ==========")
    print("Curated M5 output:", OUTPUT)


if __name__ == "__main__":
    run_m5()
