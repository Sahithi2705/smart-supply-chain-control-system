
import duckdb
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from module3_demand_forecasting.config.settings import (
    OUTPUT_DIR,
    MODEL_DIR,
    EVALUATION_DIR,
    DIM_DATE,
    RANDOM_SEED,
)

FEATURE_FILE = OUTPUT_DIR / "forecast_features.parquet"
SAMPLE_FILE = OUTPUT_DIR / "forecast_sample.parquet"
BENCHMARK_FILE = OUTPUT_DIR / "model_predictions.parquet"

PREDICTION_FILE = OUTPUT_DIR / "recursive_28day_predictions.parquet"
MODEL_FILE = MODEL_DIR / "xgboost_recursive_28day.json"
METRICS_FILE = EVALUATION_DIR / "recursive_28day_metrics.csv"

FEATURE_COLUMNS = [
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_28",
    "rolling_std_28",
    "day_of_week",
    "month",
    "is_weekend",
    "has_event_1",
    "has_event_2",
    "snap_CA",
    "snap_TX",
    "snap_WI",
]


def calculate_metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    denominator = np.abs(actual).sum()

    return {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
        "WAPE_percent": (
            np.abs(actual - predicted).sum() / denominator * 100
            if denominator > 0 else np.nan
        ),
    }


def main():

    # Prevent overwriting existing results
    for path in [PREDICTION_FILE, MODEL_FILE, METRICS_FILE]:
        if path.exists():
            raise FileExistsError(
                f"Output already exists. Inspect before rerunning: {path}"
            )

    # -------------------------------------------------
    # 1. Load data and determine the holdout period
    # -------------------------------------------------

    db = duckdb.connect()

    feature_path = FEATURE_FILE.as_posix()
    sample_path = SAMPLE_FILE.as_posix()
    calendar_path = DIM_DATE.as_posix()
    benchmark_path = BENCHMARK_FILE.as_posix()

    holdout = db.execute(f"""
        SELECT
            MIN(CAST(sales_date AS DATE)) AS test_start,
            MAX(CAST(sales_date AS DATE)) AS test_end
        FROM read_parquet('{benchmark_path}')
    """).fetchdf()

    test_start = pd.Timestamp(holdout.loc[0, "test_start"])
    test_end = pd.Timestamp(holdout.loc[0, "test_end"])

    expected_days = (test_end - test_start).days + 1

    if expected_days != 28:
        db.close()
        raise ValueError(
            f"Expected 28 test days, found {expected_days}"
        )

    # -------------------------------------------------
    # 2. Load training data strictly before test period
    # -------------------------------------------------

    train = db.execute(f"""
        SELECT *
        FROM read_parquet('{feature_path}')
        WHERE CAST(sales_date AS DATE) < DATE '{test_start.date()}'
    """).fetchdf()

    # Actual holdout values are loaded only for scoring
    actuals = db.execute(f"""
        SELECT
            CAST(sales_date AS DATE) AS sales_date,
            sku,
            store_id,
            quantity_sold
        FROM read_parquet('{sample_path}')
        WHERE CAST(sales_date AS DATE)
            BETWEEN DATE '{test_start.date()}'
            AND DATE '{test_end.date()}'
    """).fetchdf()

    # Historical sales available before forecast origin
    history_df = db.execute(f"""
        SELECT
            CAST(sales_date AS DATE) AS sales_date,
            sku,
            store_id,
            quantity_sold
        FROM read_parquet('{sample_path}')
        WHERE CAST(sales_date AS DATE) < DATE '{test_start.date()}'
        ORDER BY sku, store_id, sales_date
    """).fetchdf()

    # Calendar information for the forecast horizon
    calendar = db.execute(f"""
        SELECT
            CAST(date AS DATE) AS sales_date,
            month,
            weekday,
            event_name_1,
            event_name_2,
            snap_CA,
            snap_TX,
            snap_WI
        FROM read_parquet('{calendar_path}')
        WHERE CAST(date AS DATE)
            BETWEEN DATE '{test_start.date()}'
            AND DATE '{test_end.date()}'
    """).fetchdf()

    db.close()

    # -------------------------------------------------
    # 3. Prepare data and train the model
    # -------------------------------------------------

    train["sales_date"] = pd.to_datetime(train["sales_date"])
    actuals["sales_date"] = pd.to_datetime(actuals["sales_date"])
    history_df["sales_date"] = pd.to_datetime(history_df["sales_date"])
    calendar["sales_date"] = pd.to_datetime(calendar["sales_date"])

    train = train.dropna(subset=FEATURE_COLUMNS).copy()

    if train.empty:
        raise ValueError("No valid training records available")

    model = XGBRegressor(
        n_estimators=500,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        eval_metric="mae",
        random_state=RANDOM_SEED,
        n_jobs=4,
    )

    model.fit(
        train[FEATURE_COLUMNS],
        train["quantity_sold"],
        verbose=False,
    )

    print("TRAINING RECORDS:", len(train))
    print("FORECAST START:", test_start.date())
    print("FORECAST END:", test_end.date())

    # -------------------------------------------------
    # 4. Prepare historical demand for each SKU-store
    # -------------------------------------------------

    histories = {}

    for (sku, store_id), group in history_df.groupby(
        ["sku", "store_id"]
    ):
        group = group.sort_values("sales_date")

        histories[(sku, store_id)] = (
            group["quantity_sold"].astype(float).tolist()
        )

    if not histories:
        raise ValueError("No SKU-store historical series found")

    actual_lookup = actuals.set_index(
        ["sales_date", "sku", "store_id"]
    )["quantity_sold"]

    calendar_lookup = calendar.set_index("sales_date")

    forecast_dates = pd.date_range(
        start=test_start,
        end=test_end,
        freq="D",
    )

    if len(calendar_lookup) != 28:
        raise ValueError(
            f"Expected 28 calendar records, found {len(calendar_lookup)}"
        )

    # -------------------------------------------------
    # 5. Generate recursive predictions
    # -------------------------------------------------

    rows = []

    for forecast_date in forecast_dates:

        # Use Timestamp consistently for all date lookups
        date_key = pd.Timestamp(forecast_date)

        if date_key not in calendar_lookup.index:
            raise ValueError(
                f"Calendar information missing for {date_key.date()}"
            )

        cal = calendar_lookup.loc[date_key]

        for (sku, store_id), history in histories.items():

            if len(history) < 28:
                raise ValueError(
                    f"Insufficient history for {sku}, {store_id}"
                )

            features = {
                "lag_7": history[-7],
                "lag_14": history[-14],
                "lag_28": history[-28],
                "rolling_mean_7": np.mean(history[-7:]),
                "rolling_mean_28": np.mean(history[-28:]),
                "rolling_std_28": np.std(history[-28:]),
                "day_of_week": (forecast_date.weekday() + 1) % 7,
                "month": forecast_date.month,
                "is_weekend": forecast_date.weekday() >= 5,
                "has_event_1": int(pd.notna(cal["event_name_1"])),
                "has_event_2": int(pd.notna(cal["event_name_2"])),
                "snap_CA": cal["snap_CA"],
                "snap_TX": cal["snap_TX"],
                "snap_WI": cal["snap_WI"],
            }

            X = pd.DataFrame(
                [[features[column] for column in FEATURE_COLUMNS]],
                columns=FEATURE_COLUMNS,
            )

            prediction = max(
                float(model.predict(X)[0]),
                0.0,
            )

            seasonal_naive = max(float(history[-7]), 0.0)
            moving_average = max(float(np.mean(history[-7:])), 0.0)

            actual_key = (date_key, sku, store_id)

            if actual_key not in actual_lookup.index:
                raise ValueError(
                    f"Missing actual holdout record: {actual_key}"
                )

            actual = float(actual_lookup.loc[actual_key])

            rows.append({
                "sales_date": date_key,
                "sku": sku,
                "store_id": store_id,
                "actual": actual,
                "xgboost_prediction": prediction,
                "seasonal_naive_prediction": seasonal_naive,
                "moving_average_prediction": moving_average,
            })

            # Append prediction, never future actual demand
            history.append(prediction)

    predictions = pd.DataFrame(rows)

    expected_records = len(histories) * 28

    if len(predictions) != expected_records:
        raise ValueError(
            f"Expected {expected_records} records, "
            f"generated {len(predictions)}"
        )

    # -------------------------------------------------
    # 6. Save predictions and evaluate models
    # -------------------------------------------------

    predictions.to_parquet(
        PREDICTION_FILE,
        index=False,
        compression="zstd",
    )

    results = []

    model_columns = [
        ("Seasonal Naive", "seasonal_naive_prediction"),
        ("Moving Average", "moving_average_prediction"),
        ("XGBoost Recursive", "xgboost_prediction"),
    ]

    for model_name, prediction_column in model_columns:

        scores = calculate_metrics(
            predictions["actual"],
            predictions[prediction_column],
        )

        results.append({
            "model": model_name,
            **scores,
        })

    metrics_df = pd.DataFrame(results).sort_values(
        "WAPE_percent"
    )

    metrics_df.to_csv(METRICS_FILE, index=False)

    model.save_model(str(MODEL_FILE))

    print("\nRECURSIVE 28-DAY EVALUATION")
    print(metrics_df.to_string(index=False))

    print("\nPREDICTION RECORDS:", len(predictions))
    print("PREDICTIONS:", PREDICTION_FILE)
    print("MODEL:", MODEL_FILE)
    print("METRICS:", METRICS_FILE)


if __name__ == "__main__":
    main()
