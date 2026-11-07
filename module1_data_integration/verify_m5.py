
import duckdb

file_path = (
    "data/interim/m5_full/"
    "fact_sales/part-00000.parquet"
)

con = duckdb.connect()

print("\n--- FULL M5 DATA VALIDATION ---")

summary = con.execute("""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT source_record_id) AS series,
        COUNT(DISTINCT d) AS distinct_days,
        COUNT(*) FILTER (
            WHERE sell_price IS NULL
        ) AS missing_prices,
        COUNT(*) FILTER (
            WHERE date IS NULL
        ) AS missing_dates
    FROM read_parquet(?)
""", [file_path]).df()

print(summary.to_string(index=False))


print("\n--- DAILY RECORD COUNT CHECK ---")

daily = con.execute("""
    SELECT
        MIN(records) AS minimum_records_per_day,
        MAX(records) AS maximum_records_per_day,
        COUNT(*) AS number_of_days
    FROM (
        SELECT d, COUNT(*) AS records
        FROM read_parquet(?)
        GROUP BY d
    )
""", [file_path]).df()

print(daily.to_string(index=False))


print("\n--- DUPLICATE SALES KEY CHECK ---")

duplicates = con.execute("""
    SELECT COUNT(*) AS duplicate_keys
    FROM (
        SELECT source_record_id, d
        FROM read_parquet(?)
        GROUP BY source_record_id, d
        HAVING COUNT(*) > 1
    )
""", [file_path]).fetchone()[0]

print("Duplicate keys:", duplicates)


print("\n--- DAY RANGE ---")

day_range = con.execute("""
    SELECT
        MIN(CAST(REPLACE(d, 'd_', '') AS INTEGER))
            AS first_day,
        MAX(CAST(REPLACE(d, 'd_', '') AS INTEGER))
            AS last_day
    FROM read_parquet(?)
""", [file_path]).df()

print(day_range.to_string(index=False))

con.close()

print("\nFull M5 verification completed.")
