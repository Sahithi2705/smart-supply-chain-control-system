
import pandas as pd
import numpy as np

from module3_demand_forecasting.config.settings import (
    OUTPUT_DIR,
    EVALUATION_DIR,
)

INPUT_FILE = OUTPUT_DIR / "recursive_28day_predictions.parquet"

SKU_REPORT = EVALUATION_DIR / "sku_forecast_performance.csv"
STORE_REPORT = EVALUATION_DIR / "store_forecast_performance.csv"
DAILY_REPORT = EVALUATION_DIR / "daily_forecast_performance.csv"


def calculate_group_metrics(df, group_columns):
    rows = []

    for key, group in df.groupby(group_columns):
        actual = group["actual"].to_numpy(dtype=float)
        predicted = group["xgboost_prediction"].to_numpy(dtype=float)

        denominator = np.abs(actual).sum()

        result = {
            "records": len(group),
            "actual_units": actual.sum(),
            "forecast_units": predicted.sum(),
            "MAE": np.mean(np.abs(actual - predicted)),
            "WAPE_percent": (
                np.abs(actual - predicted).sum() / denominator * 100
                if denominator > 0 else np.nan
            ),
            "forecast_bias": predicted.sum() - actual.sum(),
        }

        if not isinstance(key, tuple):
            key = (key,)

        result.update(dict(zip(group_columns, key)))
        rows.append(result)

    return pd.DataFrame(rows)


def main():
    for path in [SKU_REPORT, STORE_REPORT, DAILY_REPORT]:
        if path.exists():
            raise FileExistsError(
                f"Report already exists: {path}"
            )

    df = pd.read_parquet(INPUT_FILE)

    # SKU-level evaluation across both stores
    sku_metrics = calculate_group_metrics(df, ["sku"])
    sku_metrics = sku_metrics.sort_values(
        "WAPE_percent", ascending=False
    )
    sku_metrics.to_csv(SKU_REPORT, index=False)

    # Store-level evaluation across all selected SKUs
    store_metrics = calculate_group_metrics(df, ["store_id"])
    store_metrics.to_csv(STORE_REPORT, index=False)

    # Forecast accuracy by day of the 28-day horizon
    df["forecast_day"] = (
        pd.to_datetime(df["sales_date"])
        - pd.to_datetime(df["sales_date"]).min()
    ).dt.days + 1

    daily_metrics = calculate_group_metrics(
        df, ["forecast_day"]
    )
    daily_metrics.to_csv(DAILY_REPORT, index=False)

    print("\nWORST 10 SKU FORECASTS")
    print(sku_metrics.head(10).to_string(index=False))

    print("\nSTORE PERFORMANCE")
    print(store_metrics.to_string(index=False))

    print("\nDAILY FORECAST PERFORMANCE")
    print(daily_metrics.to_string(index=False))

    print("\nREPORTS SAVED:")
    print(SKU_REPORT)
    print(STORE_REPORT)
    print(DAILY_REPORT)


if __name__ == "__main__":
    main()
