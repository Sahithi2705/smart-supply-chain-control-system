
import duckdb

from module3_demand_forecasting.config.settings import (
    FACT_SALES,
    OUTPUT_DIR,
)

output_file = OUTPUT_DIR / "forecast_sample_expanded.parquet"

if output_file.exists():
    raise FileExistsError(
        f"Expanded sample already exists: {output_file}. "
        "Inspect it before creating another."
    )

db = duckdb.connect()
sales_path = FACT_SALES.as_posix()

# Select 20 SKUs from each major M5 product category.
db.execute(f"""
    CREATE TEMP TABLE selected_skus AS
    SELECT sku
    FROM (
        SELECT
            sku,
            category_id,
            ROW_NUMBER() OVER (
                PARTITION BY category_id
                ORDER BY sku
            ) AS sku_rank
        FROM (
            SELECT DISTINCT sku, category_id
            FROM read_parquet('{sales_path}')
        )
    )
    WHERE sku_rank <= 20
""")

# Include every available store.
db.execute(f"""
    CREATE TEMP TABLE selected_stores AS
    SELECT DISTINCT store_id
    FROM read_parquet('{sales_path}')
""")

# Extract all historical records for the selected SKU-store combinations.
db.execute(f"""
    COPY (
        SELECT
            s.sales_date,
            s.sku,
            s.store_id,
            s.quantity_sold,
            s.unit_price,
            s.dept_id,
            s.category_id,
            s.state_id,
            s.wm_yr_wk
        FROM read_parquet('{sales_path}') AS s
        INNER JOIN selected_skus p
            ON s.sku = p.sku
        INNER JOIN selected_stores st
            ON s.store_id = st.store_id
        ORDER BY s.sku, s.store_id, s.sales_date
    )
    TO '{output_file.as_posix()}'
    (FORMAT PARQUET, COMPRESSION ZSTD)
""")

result = db.execute(f"""
    SELECT
        COUNT(*) AS total_records,
        COUNT(DISTINCT sku) AS unique_skus,
        COUNT(DISTINCT store_id) AS unique_stores,
        COUNT(DISTINCT category_id) AS unique_categories,
        MIN(sales_date) AS start_date,
        MAX(sales_date) AS end_date,
        SUM(quantity_sold) AS total_units_sold
    FROM read_parquet('{output_file.as_posix()}')
""").fetchdf()

category_result = db.execute(f"""
    SELECT
        category_id,
        COUNT(DISTINCT sku) AS unique_skus,
        COUNT(*) AS total_records
    FROM read_parquet('{output_file.as_posix()}')
    GROUP BY category_id
    ORDER BY category_id
""").fetchdf()

print("\\nEXPANDED SAMPLE EXTRACTION SUCCESSFUL")
print(result.to_string(index=False))

print("\\nCATEGORY BREAKDOWN")
print(category_result.to_string(index=False))

print("\\nSaved to:", output_file)

db.close()
