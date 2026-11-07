
import pandas as pd
from pathlib import Path

# Locate the repository and raw M5 files
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "m5"

sales_file = RAW / "sales_train_validation.csv"
calendar_file = RAW / "calendar.csv"
prices_file = RAW / "sell_prices.csv"

print("Loading 100 M5 sales rows...")

# Read only 100 sales records
sales = pd.read_csv(sales_file, nrows=100)

# Identify day columns
day_cols = [c for c in sales.columns if c.startswith("d_")]

print("Sales rows:", len(sales))
print("Day columns:", len(day_cols))

# Convert wide sales data into long format
id_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]

long_sales = sales.melt(
    id_vars=id_cols,
    value_vars=day_cols,
    var_name="d",
    value_name="quantity_sold"
)

print("Melted sales rows:", len(long_sales))

# Load calendar and join
calendar = pd.read_csv(calendar_file)

result = long_sales.merge(
    calendar[["d", "date", "wm_yr_wk"]],
    on="d",
    how="left",
    validate="many_to_one"
)

# Load prices and join
prices = pd.read_csv(prices_file)

result = result.merge(
    prices,
    on=["store_id", "item_id", "wm_yr_wk"],
    how="left",
    validate="many_to_one"
)
# Investigate missing prices
missing = result[result["sell_price"].isna()]

print("\n--- PRICE INVESTIGATION ---")
print("Missing price records:", len(missing))
print("Missing price percentage:",
      round(len(missing) / len(result) * 100, 2), "%")

print("Unique products with missing prices:",
      missing["item_id"].nunique())

print("Unique stores with missing prices:",
      missing["store_id"].nunique())

print("\nSample missing-price records:")
print(
    missing[["item_id", "store_id", "d", "date", "wm_yr_wk"]]
    .head(10)
    .to_string(index=False)
)

print("\nPrice table duplicate keys:",
      prices.duplicated(
          ["store_id", "item_id", "wm_yr_wk"]
      ).sum())
print("\n--- MISSING PRICE DATE RANGE ---")

print("Earliest missing date:", missing["date"].min())
print("Latest missing date:", missing["date"].max())

print("\nMissing prices by year:")
print(
    missing.groupby(
        pd.to_datetime(missing["date"]).dt.year
    ).size()
)

print("\nMissing prices by week:")
print(
    missing.groupby("wm_yr_wk").size().head(15)
)
print("\n--- MISSING PRICE VS SALES ---")

missing = result[result["sell_price"].isna()]

print("Missing-price rows:", len(missing))

print(
    "Rows with missing price AND positive sales:",
    (missing["quantity_sold"] > 0).sum()
)

print(
    "Rows with missing price AND zero sales:",
    (missing["quantity_sold"] == 0).sum()
)

print(
    "Rows with missing price AND null sales:",
    missing["quantity_sold"].isna().sum()
)

print("\nExamples with positive sales but missing price:")

print(
    missing.loc[
        missing["quantity_sold"] > 0,
        ["item_id", "store_id", "date", "quantity_sold", "wm_yr_wk"]
    ].head(10).to_string(index=False)
)
# Basic checks
print("\n--- SAMPLE VALIDATION ---")
print("Final rows:", len(result))
print("Missing calendar dates:", result["date"].isna().sum())
print("Missing prices:", result["sell_price"].isna().sum())
print("Duplicate sales keys:", result.duplicated(["id", "d"]).sum())

# Save a small Parquet sample
output_dir = ROOT / "module1_data_integration" / "data" / "interim"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "m5_sample.parquet"

result.to_parquet(
    output_file,
    engine="pyarrow",
    compression="zstd",
    index=False
)

print("\nSample Parquet saved:", output_file)
print("Sample size (MB):", round(output_file.stat().st_size / (1024 * 1024), 2))
print("\nM5 sample test completed.")
