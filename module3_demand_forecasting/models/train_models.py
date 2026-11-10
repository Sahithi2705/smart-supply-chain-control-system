
import duckdb
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from module3_demand_forecasting.config.settings import (
    OUTPUT_DIR,
    MODEL_DIR,
    EVALUATION_DIR,
    TEST_DAYS,
    VALIDATION_DAYS,
    RANDOM_SEED,
)

FEATURE_FILE = OUTPUT_DIR / "forecast_features.parquet"
PREDICTION_FILE = OUTPUT_DIR / "model_predictions.parquet"
METRICS_FILE = EVALUATION_DIR / "model_metrics.csv"

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


def wape(actual, predicted):
    denominator = np.abs(actual).sum()

    if denominator == 0:
        return np.nan

    return np.abs(actual - predicted).sum() / denominator * 100


def main():
    if PREDICTION_FILE.exists() or METRICS_FILE.exists():
        raise FileExistsError(
            "Model outputs already exist. Inspect them before rerunning."
        )

    db = duckdb.connect()

    feature_path = FEATURE_FILE.as_posix()

    df = db.execute(f"""
        SELECT *
        FROM read_parquet('{feature_path}')
        ORDER BY sku, store_id, sales_date
    """).fetchdf()

    db.close()

    df["sales_date"] = pd.to_datetime(df["sales_date"])

    # Exclude initial warm-up period and incomplete features
    df = df.dropna(subset=FEATURE_COLUMNS).copy()

    # Chronological global split
    dates = sorted(df["sales_date"].unique())

    test_start = dates[-TEST_DAYS]
    validation_start = dates[-(TEST_DAYS + VALIDATION_DAYS)]

    train = df[df["sales_date"] < validation_start].copy()

    validation = df[
        (df["sales_date"] >= validation_start)
        & (df["sales_date"] < test_start)
    ].copy()

    test = df[df["sales_date"] >= test_start].copy()

    X_train = train[FEATURE_COLUMNS]
    y_train = train["quantity_sold"]

    X_validation = validation[FEATURE_COLUMNS]
    y_validation = validation["quantity_sold"]

    X_test = test[FEATURE_COLUMNS]
    y_test = test["quantity_sold"]

    print("TRAINING RECORDS:", len(train))
    print("VALIDATION RECORDS:", len(validation))
    print("TEST RECORDS:", len(test))

    # XGBoost model
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
        X_train,
        y_train,
        eval_set=[(X_validation, y_validation)],
        verbose=False,
    )

    # Predictions
    predictions = pd.DataFrame({
        "sales_date": test["sales_date"].values,
        "sku": test["sku"].values,
        "store_id": test["store_id"].values,
        "actual": y_test.values,
        "xgboost_prediction": np.maximum(
            model.predict(X_test), 0
        ),
        "seasonal_naive_prediction": np.maximum(
            test["lag_7"].values, 0
        ),
        "moving_average_prediction": np.maximum(
            test["rolling_mean_7"].values, 0
        ),
    })

    predictions.to_parquet(
        PREDICTION_FILE,
        index=False,
        compression="zstd",
    )

    # Evaluation
    results = []

    for model_name, prediction_column in [
        ("Seasonal Naive", "seasonal_naive_prediction"),
        ("Moving Average", "moving_average_prediction"),
        ("XGBoost", "xgboost_prediction"),
    ]:
        actual = predictions["actual"].to_numpy()
        predicted = predictions[prediction_column].to_numpy()

        results.append({
            "model": model_name,
            "MAE": mean_absolute_error(actual, predicted),
            "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
            "WAPE_percent": wape(actual, predicted),
        })

    metrics = pd.DataFrame(results).sort_values("WAPE_percent")

    metrics.to_csv(METRICS_FILE, index=False)

    print("\nMODEL EVALUATION")
    print(metrics.to_string(index=False))

    # Save trained model
    model.save_model(MODEL_DIR / "xgboost_demand_model.json")

    print("\nPREDICTIONS:", PREDICTION_FILE)
    print("METRICS:", METRICS_FILE)
    print("MODEL:", MODEL_DIR / "xgboost_demand_model.json")


if __name__ == "__main__":
    main()
