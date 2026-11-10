
import duckdb

from module3_demand_forecasting.config.settings import OUTPUT_DIR

sample_file = OUTPUT_DIR / "forecast_sample_expanded.parquet"

db = duckdb.connect()

print("\n1. DATA QUALITY")

quality = db.execute(f"""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(*) - COUNT(DISTINCT
            (sales_date, sku, store_id)
        ) AS duplicate_rows,
        COUNT(*) FILTER (
            WHERE quantity_sold IS NULL
        ) AS missing_quantities,
        COUNT(*) FILTER (
            WHERE quantity_sold = 0
        ) AS zero_sales_days,
        COUNT(*) FILTER (
            WHERE quantity_sold < 0
        ) AS negative_sales_days,
        MIN(quantity_sold) AS minimum_quantity,
        AVG(quantity_sold) AS average_quantity,
        MEDIAN(quantity_sold) AS median_quantity,
        MAX(quantity_sold) AS maximum_quantity
    FROM read_parquet('{sample_file.as_posix()}')
""").fetchdf()

print(quality.to_string(index=False))

print("\n2. SKU-STORE COVERAGE")

coverage = db.execute(f"""
    SELECT
        COUNT(DISTINCT sku) AS skus,
        COUNT(DISTINCT store_id) AS stores,
        COUNT(DISTINCT (sku, store_id)) AS sku_store_pairs
    FROM read_parquet('{sample_file.as_posix()}')
""").fetchdf()

print(coverage.to_string(index=False))

print("\n3. CATEGORY AND STORE DISTRIBUTION")

distribution = db.execute(f"""
    SELECT
        category_id,
        COUNT(DISTINCT sku) AS skus,
        COUNT(DISTINCT store_id) AS stores,
        COUNT(DISTINCT (sku, store_id)) AS sku_store_pairs
    FROM read_parquet('{sample_file.as_posix()}')
    GROUP BY category_id
    ORDER BY category_id
""").fetchdf()

print(distribution.to_string(index=False))

db.close()
