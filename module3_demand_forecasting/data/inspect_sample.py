
import duckdb

from module3_demand_forecasting.config.settings import OUTPUT_DIR

sample_file = OUTPUT_DIR / "forecast_sample.parquet"

db = duckdb.connect()

path = sample_file.as_posix()

print("\n1. DATA QUALITY")
print(db.execute(f"""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(*) - COUNT(DISTINCT
            (sales_date, sku, store_id)
        ) AS duplicate_records,
        COUNT(*) FILTER (
            WHERE quantity_sold IS NULL
        ) AS missing_quantities,
        COUNT(*) FILTER (
            WHERE quantity_sold = 0
        ) AS zero_sales_days,
        COUNT(*) FILTER (
            WHERE quantity_sold < 0
        ) AS negative_sales_days
    FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))

print("\n2. SALES DISTRIBUTION")
print(db.execute(f"""
    SELECT
        MIN(quantity_sold) AS minimum_sales,
        AVG(quantity_sold) AS average_sales,
        MEDIAN(quantity_sold) AS median_sales,
        MAX(quantity_sold) AS maximum_sales,
        SUM(quantity_sold) AS total_units
    FROM read_parquet('{path}')
""").fetchdf().to_string(index=False))

print("\n3. RECORDS PER SKU-STORE")
print(db.execute(f"""
    SELECT sku, store_id, COUNT(*) AS records
    FROM read_parquet('{path}')
    GROUP BY sku, store_id
    ORDER BY sku, store_id
""").fetchdf().to_string(index=False))

db.close()
