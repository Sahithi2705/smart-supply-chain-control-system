
import duckdb

from module3_demand_forecasting.config.settings import (
    FACT_SALES,
    OUTPUT_DIR,
    SAMPLE_SKUS,
    SAMPLE_STORES,
)

output_file = OUTPUT_DIR / "forecast_sample.parquet"

if output_file.exists():
    raise FileExistsError(
        f"Sample already exists: {output_file}. "
        "Inspect it before creating another."
    )

db = duckdb.connect()

sales_path = FACT_SALES.as_posix()

# Select representative SKUs and stores
db.execute(f"""
    CREATE TEMP TABLE selected_skus AS
    SELECT sku
    FROM read_parquet('{sales_path}')
    GROUP BY sku
    ORDER BY sku
    LIMIT {SAMPLE_SKUS}
""")

db.execute(f"""
    CREATE TEMP TABLE selected_stores AS
    SELECT store_id
    FROM read_parquet('{sales_path}')
    GROUP BY store_id
    ORDER BY store_id
    LIMIT {SAMPLE_STORES}
""")

# Extract daily sales for the selected combinations
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
        MIN(sales_date) AS start_date,
        MAX(sales_date) AS end_date,
        SUM(quantity_sold) AS total_units_sold
    FROM read_parquet('{output_file.as_posix()}')
""").fetchdf()

print("\nSAMPLE EXTRACTION SUCCESSFUL")
print(result.to_string(index=False))
print("\nSaved to:", output_file)

db.close()
