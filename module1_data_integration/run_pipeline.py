
"""Run Module 1 local canonical pipeline."""

from pathlib import Path

import pyarrow.parquet as pq

from config.settings import INTERIM, CURATED

from profiling.profile_sources import main as profile_main
from transformations.etl_m5_chunked import main as run_m5_chunked
from transformations.etl_m5 import run_m5
from transformations.etl_olist import run_olist
from transformations.etl_scms import run_scms
from validation.validate_outputs import main as validate_main
from build_duckdb import main as duckdb_main


EXPECTED_M5_ROWS = 59_181_090

M5_INTERMEDIATE = (
    INTERIM
    / "m5_full_canonical_v2"
    / "fact_sales"
    / "part-00000.parquet"
)

M5_CURATED = CURATED / "m5_canonical_v2"

M5_ENTITIES = [
    "dim_date",
    "dim_product",
    "dim_store",
    "fact_sell_prices",
    "fact_sales",
]


def prepare_m5():

    print("\n========== PREPARING M5 ==========")

    # Reuse the completed chunked transformation if available.
    if M5_INTERMEDIATE.exists():

        rows = pq.ParquetFile(
            M5_INTERMEDIATE
        ).metadata.num_rows

        if rows != EXPECTED_M5_ROWS:
            raise ValueError(
                f"M5 intermediate contains {rows:,} rows. "
                f"Expected {EXPECTED_M5_ROWS:,}."
            )

        print(
            f"Existing M5 intermediate verified: {rows:,} rows"
        )

    else:
        print("M5 intermediate not found. Running chunked ETL...")
        run_m5_chunked()

    # Reuse the canonical M5 outputs if all five are present.
    expected_files = [
        M5_CURATED / entity / "part-00000.parquet"
        for entity in M5_ENTITIES
    ]

    existing_files = [
        path.exists() for path in expected_files
    ]

    if all(existing_files):

        print(
            "All five M5 canonical entities already exist. "
            "Skipping regeneration."
        )

        for path in expected_files:
            print("Verified:", path)

    elif any(existing_files):

        raise RuntimeError(
            "M5 canonical output is incomplete. "
            "Some entity files exist and others are missing. "
            "Inspect the output directory before continuing."
        )

    else:
        print("Running M5 canonical ETL...")
        run_m5()


def main():

    print("\n======================================")
    print(" MODULE 1 DATA INTEGRATION PIPELINE")
    print("======================================")

    print("\n[1/6] Profiling source datasets...")
    profile_main()

    print("\n[2/6] Running M5 transformations...")
    prepare_m5()

    print("\n[3/6] Running Olist ETL...")
    run_olist()

    print("\n[4/6] Running SCMS ETL...")
    run_scms()

    print("\n[5/6] Validating canonical outputs...")
    validate_main()

    print("\n[6/6] Building DuckDB database...")
    duckdb_main()

    print("\n======================================")
    print(" MODULE 1 PIPELINE COMPLETED")
    print("======================================")


if __name__ == "__main__":
    main()
