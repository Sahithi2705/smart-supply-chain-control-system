
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

FEATURE_FILE = OUTPUT_DIR / "forecast_features_expanded.parquet"
PREDICTION_FILE = OUTPUT_DIR / "model_predictions_expanded.parquet"
METRICS_FILE = EVALUATION_DIR / "model_metrics_expanded.csv"
MODEL_FILE = MODEL_DIR / "xgboost_demand_model_expanded.json"

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
    protected_outputs = [
        PREDICTION_FILE,
        METRICS_FILE,
        MODEL_FILE,
    ]

    existing = [str(path) for path in protected_outputs if path.exists()]

    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing expanded outputs:\n"
            + "\n".join(existing)
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

    df = df.dropna(subset=FEATURE_COLUMNS).copy()

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

    print("\nTRAIN PERIOD:")
    print(train["sales_date"].min(), "to", train["sales_date"].max())

    print("\nVALIDATION PERIOD:")
    print(validation["sales_date"].min(), "to", validation["sales_date"].max())

    print("\nTEST PERIOD:")
    print(test["sales_date"].min(), "to", test["sales_date"].max())

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

    predictions = pd.DataFrame({
        "sales_date": test["sales_date"].values,
        "sku": test["sku"].values,
        "store_id": test["store_id"].values,
        "category_id": test["category_id"].values,
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

    model.save_model(MODEL_FILE)

    print("\nEXPANDED MODEL EVALUATION")
    print(metrics.to_string(index=False))

    print("\nPREDICTIONS:", PREDICTION_FILE)
    print("METRICS:", METRICS_FILE)
    print("MODEL:", MODEL_FILE)


if __name__ == "__main__":
    main()
