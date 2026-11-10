
import duckdb
import numpy as np
import pandas as pd

from module3_demand_forecasting.config.settings import OUTPUT_DIR
from module3_demand_forecasting.forecasting.tsb_model import tsb_forecast

INPUT_FILE = OUTPUT_DIR / "forecast_sample.parquet"
OUTPUT_FILE = OUTPUT_DIR / "tsb_model_results.csv"

HORIZON = 28
ALPHA = 0.1
BETA = 0.1

FORECAST_ORIGINS = [
    pd.Timestamp("2015-12-27"),
    pd.Timestamp("2016-01-24"),
    pd.Timestamp("2016-02-21"),
]

db = duckdb.connect()

try:
    data = db.execute(
        f"""
        SELECT
            sku,
            store_id,
            sales_date,
            quantity_sold
        FROM read_parquet('{INPUT_FILE.as_posix()}')
        ORDER BY sku, store_id, sales_date
        """
    ).fetchdf()
finally:
    db.close()

data["sales_date"] = pd.to_datetime(data["sales_date"])

results = []

for origin in FORECAST_ORIGINS:
    forecast_start = origin + pd.Timedelta(days=1)
    forecast_end = origin + pd.Timedelta(days=HORIZON)

    for (sku, store), group in data.groupby(
        ["sku", "store_id"]
    ):
        group = group.sort_values("sales_date")

        history = group.loc[
            group["sales_date"] <= origin,
            "quantity_sold"
        ].to_numpy(dtype=float)

        actual = group.loc[
            (group["sales_date"] >= forecast_start)
            & (group["sales_date"] <= forecast_end),
            ["sales_date", "quantity_sold"]
        ]

        if len(history) < 90 or len(actual) != HORIZON:
            continue

        prediction = tsb_forecast(
            history,
            horizon=HORIZON,
            alpha=ALPHA,
            beta=BETA
        )

        actual_values = actual[
            "quantity_sold"
        ].to_numpy(dtype=float)

        results.append({
            "origin": origin,
            "sku": sku,
            "store_id": store,
            "model": "TSB",
            "actual_units": actual_values.sum(),
            "forecast_units": prediction.sum(),
            "absolute_daily_error": np.abs(
                actual_values - prediction
            ).sum(),
        })

result_df = pd.DataFrame(results)

if result_df.empty:
    raise RuntimeError("No complete forecast windows found.")

result_df.to_csv(OUTPUT_FILE, index=False)

summary = result_df.agg({
    "actual_units": "sum",
    "forecast_units": "sum",
    "absolute_daily_error": "sum",
})

total_windows = len(result_df)

mae = (
    summary["absolute_daily_error"]
    / (total_windows * HORIZON)
)

wape = (
    summary["absolute_daily_error"]
    / summary["actual_units"]
    * 100
)

print("\nTSB ROLLING-ORIGIN RESULTS")
print("Forecast windows:", total_windows)
print("Actual units:", round(summary["actual_units"], 2))
print("Forecast units:", round(summary["forecast_units"], 2))
print("Daily MAE:", round(mae, 4))
print("WAPE:", round(wape, 4), "%")
print("\nSaved report:", OUTPUT_FILE)
