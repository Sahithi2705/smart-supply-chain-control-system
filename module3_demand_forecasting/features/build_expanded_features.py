
import duckdb

from module3_demand_forecasting.config.settings import (
    OUTPUT_DIR,
    DIM_DATE,
)

SAMPLE_FILE = OUTPUT_DIR / "forecast_sample_expanded.parquet"
FEATURE_FILE = OUTPUT_DIR / "forecast_features_expanded.parquet"


def build_features():
    if FEATURE_FILE.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing file: {FEATURE_FILE}"
        )

    db = duckdb.connect()

    sample_path = SAMPLE_FILE.as_posix()
    calendar_path = DIM_DATE.as_posix()
    output_path = FEATURE_FILE.as_posix()

    query = f"""
    WITH sales AS (
        SELECT
            CAST(sales_date AS DATE) AS sales_date,
            sku,
            store_id,
            quantity_sold,
            unit_price,
            dept_id,
            category_id,
            state_id,
            wm_yr_wk
        FROM read_parquet('{sample_path}')
    ),

    calendar AS (
        SELECT
            CAST(date AS DATE) AS sales_date,
            weekday,
            wday,
            month,
            year,
            event_name_1,
            event_type_1,
            event_name_2,
            event_type_2,
            snap_CA,
            snap_TX,
            snap_WI
        FROM read_parquet('{calendar_path}')
    ),

    combined AS (
        SELECT
            s.*,
            c.weekday,
            c.wday,
            c.month,
            c.year,
            c.event_name_1,
            c.event_type_1,
            c.event_name_2,
            c.event_type_2,
            c.snap_CA,
            c.snap_TX,
            c.snap_WI
        FROM sales s
        LEFT JOIN calendar c
            ON s.sales_date = c.sales_date
    ),

    lagged AS (
        SELECT
            *,
            LAG(quantity_sold, 7) OVER w AS lag_7,
            LAG(quantity_sold, 14) OVER w AS lag_14,
            LAG(quantity_sold, 28) OVER w AS lag_28,

            AVG(quantity_sold) OVER (
                PARTITION BY sku, store_id
                ORDER BY sales_date
                ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
            ) AS rolling_mean_7,

            AVG(quantity_sold) OVER (
                PARTITION BY sku, store_id
                ORDER BY sales_date
                ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
            ) AS rolling_mean_28,

            STDDEV_POP(quantity_sold) OVER (
                PARTITION BY sku, store_id
                ORDER BY sales_date
                ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
            ) AS rolling_std_28

        FROM combined

        WINDOW w AS (
            PARTITION BY sku, store_id
            ORDER BY sales_date
        )
    )

    SELECT
        *,
        EXTRACT(DOW FROM sales_date) AS day_of_week,
        EXTRACT(ISODOW FROM sales_date) IN (6, 7)
            AS is_weekend,

        CASE WHEN event_name_1 IS NOT NULL THEN 1 ELSE 0
            END AS has_event_1,

        CASE WHEN event_name_2 IS NOT NULL THEN 1 ELSE 0
            END AS has_event_2

    FROM lagged
    ORDER BY sku, store_id, sales_date
    """

    db.execute(f"""
        COPY ({query})
        TO '{output_path}'
        (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    summary = db.execute(f"""
        SELECT
            COUNT(*) AS total_records,
            COUNT(DISTINCT sku) AS unique_skus,
            COUNT(DISTINCT store_id) AS unique_stores,
            COUNT(DISTINCT category_id) AS unique_categories,
            COUNT(*) FILTER (WHERE lag_28 IS NULL)
                AS records_without_28_day_history,
            COUNT(*) FILTER (WHERE rolling_mean_7 IS NULL)
                AS records_without_7_day_history,
            COUNT(*) FILTER (WHERE day_of_week IS NULL)
                AS missing_weekday
        FROM read_parquet('{output_path}')
    """).fetchdf()

    print("\\nEXPANDED FEATURE ENGINEERING COMPLETED")
    print(summary.to_string(index=False))
    print("\\nSaved to:", FEATURE_FILE)

    db.close()


if __name__ == "__main__":
    build_features()
