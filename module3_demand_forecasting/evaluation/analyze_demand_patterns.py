
import duckdb
import pandas as pd

from module3_demand_forecasting.config.settings import OUTPUT_DIR

INPUT_FILE = OUTPUT_DIR / "forecast_sample.parquet"
OUTPUT_FILE = (
    OUTPUT_DIR / "intermittent_demand_analysis.csv"
)

ZERO_STREAK_THRESHOLD = 14

db = duckdb.connect()

try:
    query = f"""
        WITH daily_sales AS (
            SELECT
                sku,
                store_id,
                sales_date,
                quantity_sold,
                CASE
                    WHEN quantity_sold = 0 THEN 1
                    ELSE 0
                END AS is_zero
            FROM read_parquet('{INPUT_FILE.as_posix()}')
        ),
        grouped_sales AS (
            SELECT
                *,
                SUM(
                    CASE WHEN is_zero = 0 THEN 1 ELSE 0 END
                ) OVER (
                    PARTITION BY sku, store_id
                    ORDER BY sales_date
                    ROWS BETWEEN UNBOUNDED PRECEDING
                    AND CURRENT ROW
                ) AS sales_group
            FROM daily_sales
        ),
        zero_streaks AS (
            SELECT
                sku,
                store_id,
                sales_group,
                MIN(sales_date) AS zero_start,
                MAX(sales_date) AS zero_end,
                COUNT(*) AS consecutive_zero_days
            FROM grouped_sales
            WHERE is_zero = 1
            GROUP BY sku, store_id, sales_group
        ),
        streak_analysis AS (
            SELECT
                z.sku,
                z.store_id,
                z.zero_start,
                z.zero_end,
                z.consecutive_zero_days,
                COALESCE(
                    SUM(
                        CASE
                            WHEN d.sales_date > z.zero_end
                            THEN d.quantity_sold
                            ELSE 0
                        END
                    ),
                    0
                ) AS units_sold_after_zero_streak,
                COUNT(*) FILTER (
                    WHERE d.sales_date > z.zero_end
                      AND d.quantity_sold > 0
                ) AS selling_days_after_zero_streak
            FROM zero_streaks z
            LEFT JOIN daily_sales d
                ON z.sku = d.sku
                AND z.store_id = d.store_id
            GROUP BY
                z.sku,
                z.store_id,
                z.zero_start,
                z.zero_end,
                z.consecutive_zero_days
        )
        SELECT *
        FROM streak_analysis
        WHERE consecutive_zero_days >= {ZERO_STREAK_THRESHOLD}
        ORDER BY
            consecutive_zero_days DESC,
            sku,
            store_id
    """

    result = db.execute(query).fetchdf()

    if result.empty:
        print("No zero-sales streaks found.")
    else:
        result.to_csv(OUTPUT_FILE, index=False)

        print("\nLONG ZERO-SALES PERIODS")
        print(result.to_string(index=False))

        print("\nSUMMARY")
        print(
            "Affected SKU-store combinations:",
            result[["sku", "store_id"]]
            .drop_duplicates()
            .shape[0]
        )

        print(
            "Zero-sales streaks:",
            len(result)
        )

        print(
            "Streaks followed by resumed sales:",
            (
                result["selling_days_after_zero_streak"] > 0
            ).sum()
        )

        print(
            "Longest zero-sales streak:",
            result["consecutive_zero_days"].max(),
            "days"
        )

        print("\nSaved report:", OUTPUT_FILE)

finally:
    db.close()
