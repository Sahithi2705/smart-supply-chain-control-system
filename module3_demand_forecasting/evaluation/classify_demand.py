
import duckdb
import numpy as np

from module3_demand_forecasting.config.settings import OUTPUT_DIR

INPUT_FILE = OUTPUT_DIR / "forecast_sample.parquet"
OUTPUT_FILE = OUTPUT_DIR / "demand_classification.csv"

db = duckdb.connect()

try:
    query = f"""
        SELECT
            sku,
            store_id,
            COUNT(*) AS total_days,
            SUM(
                CASE WHEN quantity_sold > 0 THEN 1 ELSE 0 END
            ) AS nonzero_days,
            AVG(quantity_sold) AS average_daily_demand,
            AVG(
                CASE
                    WHEN quantity_sold > 0
                    THEN quantity_sold
                END
            ) AS average_nonzero_demand,
            STDDEV_POP(
                CASE
                    WHEN quantity_sold > 0
                    THEN quantity_sold
                END
            ) AS std_nonzero_demand
        FROM read_parquet('{INPUT_FILE.as_posix()}')
        GROUP BY sku, store_id
        ORDER BY sku, store_id
    """

    df = db.execute(query).fetchdf()

    df["ADI"] = (
        df["total_days"] / df["nonzero_days"]
    )

    df["CV_squared"] = (
        df["std_nonzero_demand"]
        / df["average_nonzero_demand"]
    ) ** 2

    def classify(row):
        adi = row["ADI"]
        cv2 = row["CV_squared"]

        if adi <= 1.32 and cv2 <= 0.49:
            return "Smooth"

        if adi <= 1.32 and cv2 > 0.49:
            return "Erratic"

        if adi > 1.32 and cv2 <= 0.49:
            return "Intermittent"

        return "Lumpy"

    df["demand_pattern"] = df.apply(
        classify,
        axis=1
    )

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nDEMAND PATTERN CLASSIFICATION")
    print(
        df[
            [
                "sku",
                "store_id",
                "ADI",
                "CV_squared",
                "demand_pattern"
            ]
        ].to_string(index=False)
    )

    print("\nPATTERN SUMMARY")
    print(
        df["demand_pattern"]
        .value_counts()
        .to_string()
    )

    print("\nSaved report:", OUTPUT_FILE)

finally:
    db.close()
