import argparse
from pathlib import Path

import pandas as pd


def transform_m5(sku_limit: int, days: int, output_path: str):
    # ---------------------------------------------------------
    # 1. Define input files
    # ---------------------------------------------------------
    data_dir = Path("data/raw/m5")

    sales_file = data_dir / "sales_train_validation.csv"
    calendar_file = data_dir / "calendar.csv"
    prices_file = data_dir / "sell_prices.csv"

    print("Starting M5 → Canonical transformation...")
    print(f"SKU limit : {sku_limit}")
    print(f"Days      : {days}")

    # ---------------------------------------------------------
    # 2. Read a small M5 sales sample
    # ---------------------------------------------------------
    day_columns = [f"d_{i}" for i in range(1, days + 1)]

    sales_columns = [
        "id",
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id",
    ] + day_columns

    print("\nReading M5 sales data...")

    sales = pd.read_csv(
        sales_file,
        usecols=sales_columns,
        nrows=sku_limit
    )

    print(f"Sales rows loaded: {len(sales)}")

    # ---------------------------------------------------------
    # 3. Convert M5 wide format → long format
    # ---------------------------------------------------------
    print("\nConverting daily columns from wide → long format...")

    sales_long = sales.melt(
        id_vars=[
            "id",
            "item_id",
            "dept_id",
            "cat_id",
            "store_id",
            "state_id",
        ],
        value_vars=day_columns,
        var_name="d",
        value_name="quantity_sold"
    )

    print(f"Rows after unpivot: {len(sales_long)}")

    # ---------------------------------------------------------
    # 4. Read calendar
    # ---------------------------------------------------------
    print("\nReading calendar...")

    calendar = pd.read_csv(calendar_file)

    calendar = calendar[
        [
            "date",
            "wm_yr_wk",
            "weekday",
            "wday",
            "month",
            "year",
            "d",
            "event_name_1",
            "event_type_1",
            "event_name_2",
            "event_type_2",
            "snap_CA",
            "snap_TX",
            "snap_WI",
        ]
    ]

    calendar = calendar.head(days)

    # Convert date to proper date type
    calendar["date"] = pd.to_datetime(calendar["date"]).dt.date

    # ---------------------------------------------------------
    # 5. Join sales with calendar
    # ---------------------------------------------------------
    print("\nJoining sales with calendar...")

    sales_long = sales_long.merge(
        calendar,
        on="d",
        how="left",
        validate="many_to_one"
    )

    # ---------------------------------------------------------
    # 6. Prepare price data
    # ---------------------------------------------------------
    print("\nReading relevant price records...")

    selected_items = set(sales_long["item_id"].unique())
    selected_stores = set(sales_long["store_id"].unique())
    selected_weeks = set(sales_long["wm_yr_wk"].dropna().unique())

    price_chunks = []

    for chunk in pd.read_csv(
        prices_file,
        chunksize=500_000
    ):
        filtered = chunk[
            chunk["item_id"].isin(selected_items)
            & chunk["store_id"].isin(selected_stores)
            & chunk["wm_yr_wk"].isin(selected_weeks)
        ]

        if not filtered.empty:
            price_chunks.append(filtered)

    if price_chunks:
        prices = pd.concat(price_chunks, ignore_index=True)
    else:
        prices = pd.DataFrame(
            columns=[
                "store_id",
                "item_id",
                "wm_yr_wk",
                "sell_price"
            ]
        )

    print(f"Relevant price rows: {len(prices)}")

    # ---------------------------------------------------------
    # 7. Join prices with sales
    # ---------------------------------------------------------
    print("\nJoining prices...")

    sales_long = sales_long.merge(
        prices,
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left",
        validate="many_to_one"
    )

    # ---------------------------------------------------------
    # 8. Create canonical columns
    # ---------------------------------------------------------
    print("\nCreating canonical model...")

    canonical = sales_long[
        [
            "date",
            "item_id",
            "store_id",
            "quantity_sold",
            "sell_price",
            "dept_id",
            "cat_id",
            "state_id",
            "id",
        ]
    ].copy()

    canonical = canonical.rename(
        columns={
            "date": "sales_date",
            "item_id": "sku",
            "sell_price": "unit_price",
            "cat_id": "category_id",
            "id": "source_record_id",
        }
    )

    # ---------------------------------------------------------
    # 9. Add source-system information
    # ---------------------------------------------------------
    canonical["source_system"] = "M5"

    # ---------------------------------------------------------
    # 10. Clean data types
    # ---------------------------------------------------------
    canonical["quantity_sold"] = pd.to_numeric(
        canonical["quantity_sold"],
        errors="coerce"
    ).fillna(0).astype("int64")

    canonical["unit_price"] = pd.to_numeric(
        canonical["unit_price"],
        errors="coerce"
    )

    canonical["sku"] = canonical["sku"].astype(str)
    canonical["store_id"] = canonical["store_id"].astype(str)
    canonical["dept_id"] = canonical["dept_id"].astype(str)
    canonical["category_id"] = canonical["category_id"].astype(str)
    canonical["state_id"] = canonical["state_id"].astype(str)
    canonical["source_system"] = canonical["source_system"].astype(str)
    canonical["source_record_id"] = canonical["source_record_id"].astype(str)

    # ---------------------------------------------------------
    # 11. Reorder columns according to canonical schema
    # ---------------------------------------------------------
    canonical = canonical[
        [
            "sales_date",
            "sku",
            "store_id",
            "quantity_sold",
            "unit_price",
            "dept_id",
            "category_id",
            "state_id",
            "source_system",
            "source_record_id",
        ]
    ]

    # ---------------------------------------------------------
    # 12. Create output directory
    # ---------------------------------------------------------
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 13. Save canonical data
    # ---------------------------------------------------------
    canonical.to_csv(
        output,
        index=False
    )

    print("\nTransformation completed successfully.")
    print(f"Output file: {output}")
    print(f"Canonical rows: {len(canonical)}")
    print(f"Canonical columns: {len(canonical.columns)}")

    # ---------------------------------------------------------
    # 14. Basic validation
    # ---------------------------------------------------------
    print("\nRunning basic validation...")

    required_columns = [
        "sales_date",
        "sku",
        "store_id",
        "quantity_sold",
        "source_system",
        "source_record_id",
    ]

    for column in required_columns:
        null_count = canonical[column].isna().sum()

        if null_count > 0:
            raise ValueError(
                f"Validation failed: {column} contains {null_count} null values."
            )

    if (canonical["quantity_sold"] < 0).any():
        raise ValueError(
            "Validation failed: negative quantity_sold detected."
        )

    print("Validation passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transform M5 sales data into canonical sales format."
    )

    parser.add_argument(
        "--sku-limit",
        type=int,
        default=100
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/curated/canonical_sales_m5_sample.csv"
    )

    args = parser.parse_args()

    transform_m5(
        sku_limit=args.sku_limit,
        days=args.days,
        output_path=args.output
    )