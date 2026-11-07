
import gc
import re
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


# ==================================================
# 1. PATHS AND SETTINGS
# ==================================================

ROOT = Path(__file__).resolve().parents[2]

RAW = ROOT / "data" / "raw" / "m5"

OUTPUT = (
    ROOT
    / "module1_data_integration"
    / "data"
    / "interim"
    / "m5_full"
    / "fact_sales"
)

VALIDATION_FILE = RAW / "sales_train_validation.csv"
EVALUATION_FILE = RAW / "sales_train_evaluation.csv"
CALENDAR_FILE = RAW / "calendar.csv"
PRICES_FILE = RAW / "sell_prices.csv"

CHUNK_SIZE = 100

# Keep True for testing.
# Change to False only after the sample test passes.
TEST_MODE = False
TEST_CHUNKS = 2

OUTPUT.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT / "part-00000.parquet"


# ==================================================
# 2. LOAD CALENDAR AND PRICE LOOKUP TABLES
# ==================================================

def load_lookups():

    print("\nLoading calendar...")

    calendar = pd.read_csv(CALENDAR_FILE)

    calendar = calendar[
        ["d", "date", "wm_yr_wk"]
    ].copy()

    calendar["date"] = pd.to_datetime(calendar["date"])

    if calendar["d"].duplicated().any():
        raise ValueError("Duplicate day IDs found in calendar.")

    print("Calendar loaded:", len(calendar))

    print("\nLoading sell prices...")

    prices = pd.read_csv(
        PRICES_FILE,
        dtype={
            "store_id": "string",
            "item_id": "string"
        }
    )

    if prices.duplicated(
        ["store_id", "item_id", "wm_yr_wk"]
    ).any():
        raise ValueError("Duplicate price lookup keys found.")

    print("Price records loaded:", f"{len(prices):,}")

    return calendar, prices


# ==================================================
# 3. IDENTIFY DAY COLUMNS
# ==================================================

def get_day_columns(file_path, expected_days):

    columns = pd.read_csv(
        file_path,
        nrows=0
    ).columns.tolist()

    day_columns = [
        column for column in columns
        if re.fullmatch(r"d_\d+", column)
    ]

    if len(day_columns) != expected_days:
        raise ValueError(
            f"Expected {expected_days} day columns, "
            f"found {len(day_columns)}."
        )

    return day_columns


# ==================================================
# 4. VERIFY VALIDATION AND EVALUATION IDs
# ==================================================

def verify_series_ids():

    print("\nVerifying validation/evaluation IDs...")

    validation_ids = pd.read_csv(
        VALIDATION_FILE,
        usecols=["id"],
        dtype={"id": "string"}
    )["id"]

    evaluation_ids = pd.read_csv(
        EVALUATION_FILE,
        usecols=["id"],
        dtype={"id": "string"}
    )["id"].str.replace(
        "_evaluation",
        "_validation",
        regex=False
    )

    if not validation_ids.reset_index(drop=True).equals(
        evaluation_ids.reset_index(drop=True)
    ):
        raise ValueError(
            "Validation and evaluation IDs do not match."
        )

    print("Validation/evaluation IDs match.")
    print("Verified series:", f"{len(validation_ids):,}")

    return len(validation_ids)


# ==================================================
# 5. TRANSFORM ONE CHUNK
# ==================================================

def transform_chunk(chunk, day_columns, calendar, prices):

    id_columns = [
        "id",
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id"
    ]

    # Convert wide data into long format
    long_sales = chunk.melt(
        id_vars=id_columns,
        value_vars=day_columns,
        var_name="d",
        value_name="quantity_sold"
    )

    # Join calendar
    result = long_sales.merge(
        calendar,
        on="d",
        how="left",
        validate="many_to_one"
    )

    if result["date"].isna().any():
        raise ValueError(
            "Calendar join produced missing dates."
        )

    # Join selling prices
    result = result.merge(
        prices,
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left",
        validate="many_to_one"
    )

    # Preserve missing prices as NULL
    result["quantity_sold"] = result[
        "quantity_sold"
    ].astype("int64")

    result["sell_price"] = result[
        "sell_price"
    ].astype("float64")

    # Rename canonical fields
    result = result.rename(
        columns={
            "item_id": "sku",
            "cat_id": "category_id"
        }
    )

    result["source_system"] = "M5"
    result["source_record_id"] = result["id"]

    # Select canonical columns
    result = result[
        [
            "date",
            "sku",
            "store_id",
            "quantity_sold",
            "sell_price",
            "dept_id",
            "category_id",
            "state_id",
            "wm_yr_wk",
            "source_system",
            "source_record_id",
            "d"
        ]
    ]

    return result


# ==================================================
# 6. PROCESS DATASETS IN CHUNKS
# ==================================================

def write_dataset(calendar, prices, total_series):

    writer = None

    total_rows = 0

    datasets = [
        (
            "validation",
            VALIDATION_FILE,
            1913,
            1,
            30_490 * 1913
        ),
        (
            "evaluation_extra",
            EVALUATION_FILE,
            28,
            1914,
            30_490 * 28
        )
    ]

    try:

        for dataset_name, file_path, day_count, first_day, expected_rows in datasets:

            print("\n================================")
            print("Processing:", dataset_name)
            print("================================")

            all_day_columns = get_day_columns(
                file_path,
                1913 if dataset_name == "validation" else 1941
            )

            # Validation uses all 1913 days.
            if dataset_name == "validation":

                day_columns = all_day_columns

            # Evaluation uses only the additional 28 days.
            else:

                day_columns = [
                    f"d_{number}"
                    for number in range(
                        first_day,
                        first_day + day_count
                    )
                ]

                if not set(day_columns).issubset(
                    set(all_day_columns)
                ):
                    raise ValueError(
                        "Evaluation horizon columns are missing."
                    )

            reader = pd.read_csv(
                file_path,
                chunksize=CHUNK_SIZE
            )

            dataset_rows = 0

            for chunk_number, chunk in enumerate(
                reader,
                start=1
            ):

                # Limit processing during sample testing.
                if TEST_MODE and chunk_number > TEST_CHUNKS:
                    break

                # Convert evaluation IDs to canonical IDs.
                if dataset_name == "evaluation_extra":

                    chunk["id"] = chunk["id"].str.replace(
                        "_evaluation",
                        "_validation",
                        regex=False
                    )

                transformed = transform_chunk(
                    chunk,
                    day_columns,
                    calendar,
                    prices
                )

                # Check duplicate keys inside each chunk.
                if transformed.duplicated(
                    ["source_record_id", "d"]
                ).any():

                    raise ValueError(
                        "Duplicate sales keys found inside chunk."
                    )

                # Convert to Arrow table.
                table = pa.Table.from_pandas(
                    transformed,
                    preserve_index=False
                )

                # Initialize Parquet writer once.
                if writer is None:

                    writer = pq.ParquetWriter(
                        OUTPUT_FILE,
                        table.schema,
                        compression="zstd"
                    )

                writer.write_table(table)

                rows = len(transformed)

                dataset_rows += rows
                total_rows += rows

                if chunk_number % 10 == 0:

                    print(
                        f"{dataset_name}: "
                        f"{dataset_rows:,} rows written"
                    )

                del transformed
                del table
                del chunk

                gc.collect()

            # Verify row counts.
            if TEST_MODE:

                expected_test_rows = (
                    min(TEST_CHUNKS, (30_490 + CHUNK_SIZE - 1) // CHUNK_SIZE)
                    * CHUNK_SIZE
                    * day_count
                )

                if dataset_rows != expected_test_rows:

                    raise ValueError(
                        f"{dataset_name}: expected "
                        f"{expected_test_rows:,} test rows, "
                        f"got {dataset_rows:,}."
                    )

            elif dataset_rows != expected_rows:

                raise ValueError(
                    f"{dataset_name}: expected "
                    f"{expected_rows:,} rows, "
                    f"got {dataset_rows:,}."
                )

            print(
                f"{dataset_name} completed: "
                f"{dataset_rows:,} rows"
            )

    finally:

        if writer is not None:
            writer.close()

    # ==================================================
    # 7. VERIFY PARQUET OUTPUT
    # ==================================================

    if not OUTPUT_FILE.exists():
        raise FileNotFoundError("Parquet output was not created.")

    parquet_file = pq.ParquetFile(OUTPUT_FILE)

    parquet_rows = parquet_file.metadata.num_rows

    if parquet_rows != total_rows:
        raise ValueError(
            "Parquet row count does not match written row count."
        )

    print("\n================================")
    print("M5 ETL SUMMARY")
    print("================================")

    print("Validation series:", f"{total_series:,}")
    print("Total rows written:", f"{total_rows:,}")
    print("Parquet rows:", f"{parquet_rows:,}")

    print("Parquet file:", OUTPUT_FILE)

    print(
        "Output size:",
        round(
            OUTPUT_FILE.stat().st_size / (1024 * 1024),
            2
        ),
        "MB"
    )

    print("\nParquet schema:")
    print(parquet_file.schema)

    if TEST_MODE:

        print("\nRunning sample duplicate-key verification...")

        sample = pd.read_parquet(OUTPUT_FILE)

        duplicate_count = sample.duplicated(
            ["source_record_id", "d"]
        ).sum()

        if duplicate_count:
            raise ValueError(
                f"Found {duplicate_count} duplicate sales keys."
            )

        print("Sample duplicate keys:", duplicate_count)

        print(
            "Sample missing prices:",
            sample["sell_price"].isna().sum()
        )

        print("Sample verification passed.")


# ==================================================
# 8. MAIN EXECUTION
# ==================================================

def main():

    if OUTPUT_FILE.exists():

        raise FileExistsError(
            f"Output already exists: {OUTPUT_FILE}\n"
            "Delete or rename the previous test output "
            "before running again."
        )

    print("Starting M5 chunked ETL...")

    total_series = verify_series_ids()

    calendar, prices = load_lookups()

    write_dataset(
        calendar,
        prices,
        total_series
    )

    print("\nM5 chunked ETL completed successfully.")


if __name__ == "__main__":

    main()
