
import duckdb
import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from module3_demand_forecasting.config.settings import (
    OUTPUT_DIR,
    DIM_DATE,
    RANDOM_SEED,
)

from module3_demand_forecasting.forecasting.intermittent_models import (
    croston,
    sba,
)

from module3_demand_forecasting.forecasting.tsb_model import (
    tsb_forecast,
)


# =========================================================
# 1. CONFIGURATION
# =========================================================

SAMPLE_FILE = OUTPUT_DIR / "forecast_sample.parquet"

RESULT_FILE = OUTPUT_DIR / "all_models_comparison.csv"
SUMMARY_FILE = OUTPUT_DIR / "all_models_summary.csv"

HORIZON = 28
ALPHA = 0.1
BETA = 0.1

FORECAST_ORIGINS = [
    pd.Timestamp("2015-12-27"),
    pd.Timestamp("2016-01-24"),
    pd.Timestamp("2016-02-21"),
]

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

MODEL_NAMES = [
    "xgboost",
    "moving_average",
    "seasonal_naive",
    "croston",
    "sba",
    "tsb",
]


# =========================================================
# 2. METRICS
# =========================================================

def calculate_metrics(actual, predicted):

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    absolute_error = np.abs(actual - predicted)

    denominator = np.abs(actual).sum()

    return {
        "MAE_daily": mean_absolute_error(
            actual, predicted
        ),
        "RMSE_daily": np.sqrt(
            mean_squared_error(actual, predicted)
        ),
        "WAPE_percent": (
            absolute_error.sum() / denominator * 100
            if denominator > 0 else np.nan
        ),
        "actual_units": actual.sum(),
        "forecast_units": predicted.sum(),
    }


# =========================================================
# 3. LOAD SALES AND CALENDAR DATA
# =========================================================

def load_data():

    db = duckdb.connect()

    sales_path = SAMPLE_FILE.as_posix()
    calendar_path = DIM_DATE.as_posix()

    try:

        sales = db.execute(f"""
            SELECT
                CAST(sales_date AS DATE) AS sales_date,
                sku,
                store_id,
                quantity_sold
            FROM read_parquet('{sales_path}')
            ORDER BY sku, store_id, sales_date
        """).fetchdf()

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
        """).fetchdf()

    finally:
        db.close()

    sales["sales_date"] = pd.to_datetime(
        sales["sales_date"]
    )

    calendar["sales_date"] = pd.to_datetime(
        calendar["sales_date"]
    )

    return sales, calendar


# =========================================================
# 4. FEATURE GENERATION
# =========================================================

def create_features(history, forecast_date, calendar_row):

    if len(history) < 28:
        raise ValueError(
            "At least 28 historical observations are required."
        )

    return {
        "lag_7": history[-7],
        "lag_14": history[-14],
        "lag_28": history[-28],
        "rolling_mean_7": np.mean(history[-7:]),
        "rolling_mean_28": np.mean(history[-28:]),
        "rolling_std_28": np.std(history[-28:]),
        "day_of_week": (forecast_date.weekday() + 1) % 7,
        "month": forecast_date.month,
        "is_weekend": int(forecast_date.weekday() >= 5),
        "has_event_1": int(
            pd.notna(calendar_row["event_name_1"])
        ),
        "has_event_2": int(
            pd.notna(calendar_row["event_name_2"])
        ),
        "snap_CA": calendar_row["snap_CA"],
        "snap_TX": calendar_row["snap_TX"],
        "snap_WI": calendar_row["snap_WI"],
    }


# =========================================================
# 5. TRAIN XGBOOST USING PRE-ORIGIN DATA ONLY
# =========================================================

def train_xgboost(train, calendar):

    calendar_lookup = calendar.set_index("sales_date")

    training_rows = []

    for (sku, store), group in train.groupby(
        ["sku", "store_id"]
    ):

        group = group.sort_values("sales_date")

        values = group["quantity_sold"].to_numpy(
            dtype=float
        )

        dates = group["sales_date"].tolist()

        for index in range(28, len(group)):

            current_date = dates[index]

            if current_date not in calendar_lookup.index:
                continue

            features = create_features(
                values[:index],
                current_date,
                calendar_lookup.loc[current_date],
            )

            training_rows.append({
                **features,
                "quantity_sold": values[index],
            })

    training = pd.DataFrame(training_rows)

    if training.empty:
        raise ValueError(
            "No valid XGBoost training records found."
        )

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
        training[FEATURE_COLUMNS],
        training["quantity_sold"],
        verbose=False,
    )

    print("XGBOOST TRAINING RECORDS:", len(training))

    return model


# =========================================================
# 6. EVALUATE ONE FORECAST ORIGIN
# =========================================================

def evaluate_origin(sales, calendar, origin):

    forecast_start = origin + pd.Timedelta(days=1)

    forecast_end = origin + pd.Timedelta(days=HORIZON)

    print("\n" + "=" * 65)
    print("FORECAST ORIGIN:", origin.date())
    print(
        "FORECAST PERIOD:",
        forecast_start.date(),
        "TO",
        forecast_end.date(),
    )
    print("=" * 65)

    # Only information available before the forecast origin.

    train = sales[
        sales["sales_date"] <= origin
    ].copy()

    actuals = sales[
        (sales["sales_date"] >= forecast_start)
        & (sales["sales_date"] <= forecast_end)
    ].copy()

    forecast_calendar = calendar[
        (calendar["sales_date"] >= forecast_start)
        & (calendar["sales_date"] <= forecast_end)
    ].copy()

    if len(forecast_calendar) != HORIZON:
        raise ValueError(
            "Incomplete calendar forecast period."
        )

    sku_stores = train[
        ["sku", "store_id"]
    ].drop_duplicates()

    expected_records = len(sku_stores) * HORIZON

    if len(actuals) != expected_records:
        raise ValueError(
            f"Expected {expected_records} actual records, "
            f"found {len(actuals)}."
        )

    if train.empty:
        raise ValueError("Training data is empty.")

    # -----------------------------------------------------
    # Train XGBoost
    # -----------------------------------------------------

    model = train_xgboost(train, calendar)

    # -----------------------------------------------------
    # Initialize independent histories for each model
    # -----------------------------------------------------

    histories = {}

    for (sku, store), group in train.groupby(
        ["sku", "store_id"]
    ):

        group = group.sort_values("sales_date")

        historical_values = (
            group["quantity_sold"]
            .astype(float)
            .tolist()
        )

        if len(historical_values) < 28:
            raise ValueError(
                f"Insufficient history for {sku}, {store}."
            )

        histories[(sku, store)] = {
            "xgboost": historical_values.copy(),
            "moving_average": historical_values.copy(),
            "seasonal_naive": historical_values.copy(),
        }

    # -----------------------------------------------------
    # Lookup actual values and calendar information
    # -----------------------------------------------------

    actual_lookup = actuals.set_index(
        ["sales_date", "sku", "store_id"]
    )["quantity_sold"]

    calendar_lookup = forecast_calendar.set_index(
        "sales_date"
    )

    rows = []

    # -----------------------------------------------------
    # Calculate fixed-origin Croston, SBA and TSB forecasts
    # -----------------------------------------------------

    intermittent_forecasts = {}

    for (sku, store), group in train.groupby(
        ["sku", "store_id"]
    ):

        group = group.sort_values("sales_date")

        history = group["quantity_sold"].to_numpy(
            dtype=float
        )

        intermittent_forecasts[(sku, store)] = {
            "croston": float(
                croston(history, HORIZON, alpha=ALPHA)[0]
            ),
            "sba": float(
                sba(history, HORIZON, alpha=ALPHA)[0]
            ),
            "tsb": float(
                tsb_forecast(
                    history,
                    HORIZON,
                    alpha=ALPHA,
                    beta=BETA,
                )[0]
            ),
        }

    # -----------------------------------------------------
    # Recursive 28-day forecasting
    # -----------------------------------------------------

    for forecast_date in pd.date_range(
        forecast_start,
        forecast_end,
        freq="D",
    ):

        if forecast_date not in calendar_lookup.index:
            raise ValueError(
                f"Missing calendar date: {forecast_date.date()}"
            )

        cal = calendar_lookup.loc[forecast_date]

        for key, model_histories in histories.items():

            sku, store = key

            actual_key = (forecast_date, sku, store)

            if actual_key not in actual_lookup.index:
                raise ValueError(
                    f"Missing actual value for {actual_key}"
                )

            actual = float(
                actual_lookup.loc[actual_key]
            )

            # -------------------------------------------------
            # XGBoost: uses only its own previous predictions
            # -------------------------------------------------

            xgb_history = model_histories["xgboost"]

            features = create_features(
                xgb_history,
                forecast_date,
                cal,
            )

            X = pd.DataFrame(
                [features],
                columns=FEATURE_COLUMNS,
            )

            xgb_prediction = max(
                float(model.predict(X)[0]),
                0.0,
            )

            # -------------------------------------------------
            # Moving Average: uses its own history
            # -------------------------------------------------

            ma_history = model_histories["moving_average"]

            ma_prediction = max(
                float(np.mean(ma_history[-7:])),
                0.0,
            )

            # -------------------------------------------------
            # Seasonal Naive: uses its own history
            # -------------------------------------------------

            naive_history = model_histories["seasonal_naive"]

            naive_prediction = max(
                float(naive_history[-7]),
                0.0,
            )

            # -------------------------------------------------
            # Intermittent methods: fixed-origin daily rates
            # -------------------------------------------------

            intermittent = intermittent_forecasts[key]

            rows.append({
                "origin": origin,
                "sales_date": forecast_date,
                "sku": sku,
                "store_id": store,
                "actual": actual,
                "xgboost": xgb_prediction,
                "moving_average": ma_prediction,
                "seasonal_naive": naive_prediction,
                "croston": intermittent["croston"],
                "sba": intermittent["sba"],
                "tsb": intermittent["tsb"],
            })

            # -------------------------------------------------
            # Update each recursive model independently
            # -------------------------------------------------

            xgb_history.append(xgb_prediction)

            ma_history.append(ma_prediction)

            naive_history.append(naive_prediction)

    result = pd.DataFrame(rows)

    expected = len(sku_stores) * HORIZON

    if len(result) != expected:
        raise ValueError(
            f"Expected {expected} forecast rows, "
            f"generated {len(result)}."
        )

    return result


# =========================================================
# 7. MAIN
# =========================================================

def main():

    # Protect existing reports.

    for path in [RESULT_FILE, SUMMARY_FILE]:

        if path.exists():
            raise FileExistsError(
                f"Output already exists. Inspect before rerunning: {path}"
            )

    print("LOADING MODULE 3 DATA...")

    sales, calendar = load_data()

    print("SALES RECORDS:", len(sales))
    print("UNIQUE SKUS:", sales["sku"].nunique())
    print("UNIQUE STORES:", sales["store_id"].nunique())

    all_results = []

    for origin in FORECAST_ORIGINS:

        result = evaluate_origin(
            sales,
            calendar,
            origin,
        )

        all_results.append(result)

    combined = pd.concat(
        all_results,
        ignore_index=True,
    )

    # -----------------------------------------------------
    # Evaluate all six models on identical records
    # -----------------------------------------------------

    summaries = []

    for model_name in MODEL_NAMES:

        scores = calculate_metrics(
            combined["actual"],
            combined[model_name],
        )

        summaries.append({
            "model": model_name,
            "forecast_records": len(combined),
            **scores,
        })

    summary = pd.DataFrame(summaries).sort_values(
        "WAPE_percent"
    )

    # -----------------------------------------------------
    # Save new reports only
    # -----------------------------------------------------

    combined.to_csv(
        RESULT_FILE,
        index=False,
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    print("\n" + "=" * 65)
    print("COMMON ROLLING-ORIGIN MODEL COMPARISON")
    print("=" * 65)

    print(summary.round(4).to_string(index=False))

    print("\nFORECAST ORIGINS:", len(FORECAST_ORIGINS))
    print("TOTAL FORECAST RECORDS:", len(combined))

    print("\nSAVED REPORTS:")
    print(RESULT_FILE)
    print(SUMMARY_FILE)


if __name__ == "__main__":
    main()
