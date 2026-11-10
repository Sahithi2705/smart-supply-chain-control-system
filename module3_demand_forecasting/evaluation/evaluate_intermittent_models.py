
import duckdb
import numpy as np
import pandas as pd

from module3_demand_forecasting.config.settings import OUTPUT_DIR
from module3_demand_forecasting.forecasting.intermittent_models import (
    croston,
    sba,
)

INPUT_FILE = OUTPUT_DIR / "forecast_sample.parquet"
OUTPUT_FILE = OUTPUT_DIR / "intermittent_model_results.csv"

HORIZON = 28
ALPHA = 0.1

# Three chronological rolling forecast origins.
# Every origin uses only sales dated before its forecast window.
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
        ].copy()

        # Require a complete 28-day actual forecast window.
        if len(history) < 90 or len(actual) != HORIZON:
            continue

        actual_units = actual["quantity_sold"].to_numpy()

        croston_prediction = croston(
            history,
            HORIZON,
            alpha=ALPHA
        )

        sba_prediction = sba(
            history,
            HORIZON,
            alpha=ALPHA
        )

        for model_name, prediction in [
            ("Croston", croston_prediction),
            ("SBA", sba_prediction),
        ]:
            results.append({
                "origin": origin,
                "forecast_start": forecast_start,
                "forecast_end": forecast_end,
                "sku": sku,
                "store_id": store,
                "model": model_name,
                "actual_units": actual_units.sum(),
                "forecast_units": prediction.sum(),
                "absolute_error": abs(
                    actual_units.sum() - prediction.sum()
                ),
                "absolute_daily_error": np.abs(
                    actual_units - prediction
                ).sum(),
            })

result_df = pd.DataFrame(results)

if result_df.empty:
    raise RuntimeError(
        "No complete forecast windows were available."
    )

result_df.to_csv(OUTPUT_FILE, index=False)

summary = (
    result_df.groupby("model")
    .agg(
        forecast_windows=("sku", "count"),
        actual_units=("actual_units", "sum"),
        forecast_units=("forecast_units", "sum"),
        total_absolute_daily_error=(
            "absolute_daily_error",
            "sum"
        ),
    )
)

summary["MAE_daily"] = (
    summary["total_absolute_daily_error"]
    / (summary["forecast_windows"] * HORIZON)
)

summary["WAPE"] = (
    summary["total_absolute_daily_error"]
    / summary["actual_units"].replace(0, np.nan)
    * 100
)

print("\nROLLING-ORIGIN INTERMITTENT MODEL RESULTS")
print(summary.round(4).to_string())

print("\nForecast origins:", len(FORECAST_ORIGINS))
print("SKU-store forecast windows:", len(result_df))
print("Saved report:", OUTPUT_FILE)
