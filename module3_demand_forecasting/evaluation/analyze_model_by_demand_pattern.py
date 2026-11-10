
import numpy as np
import pandas as pd

from module3_demand_forecasting.config.settings import OUTPUT_DIR


# =========================================================
# 1. CONFIGURATION
# =========================================================

SALES_FILE = OUTPUT_DIR / "forecast_sample.parquet"

PREDICTION_FILE = OUTPUT_DIR / "all_models_comparison.csv"

PATTERN_OUTPUT = OUTPUT_DIR / "demand_pattern_by_origin.csv"

SUMMARY_OUTPUT = OUTPUT_DIR / "model_performance_by_demand_pattern.csv"

MODEL_NAMES = [
    "xgboost",
    "moving_average",
    "seasonal_naive",
    "croston",
    "sba",
    "tsb",
]

ADI_THRESHOLD = 1.32
CV2_THRESHOLD = 0.49


# =========================================================
# 2. DEMAND PATTERN CLASSIFICATION
# =========================================================

def classify_demand(history):

    history = np.asarray(history, dtype=float)

    if len(history) == 0:
        raise ValueError("Demand history is empty.")

    if np.any(history < 0):
        raise ValueError("Negative demand is not supported.")

    nonzero = history[history > 0]

    if len(nonzero) == 0:
        return {
            "ADI": np.inf,
            "CV2": np.nan,
            "demand_pattern": "No Demand",
        }

    adi = len(history) / len(nonzero)

    mean_demand = nonzero.mean()

    cv2 = (
        (nonzero.std(ddof=0) / mean_demand) ** 2
        if mean_demand > 0
        else np.nan
    )

    if adi < ADI_THRESHOLD and cv2 < CV2_THRESHOLD:
        pattern = "Smooth"

    elif adi >= ADI_THRESHOLD and cv2 < CV2_THRESHOLD:
        pattern = "Intermittent"

    elif adi < ADI_THRESHOLD and cv2 >= CV2_THRESHOLD:
        pattern = "Erratic"

    else:
        pattern = "Lumpy"

    return {
        "ADI": adi,
        "CV2": cv2,
        "demand_pattern": pattern,
    }


# =========================================================
# 3. CLASSIFY EACH SKU-STORE AT EACH ORIGIN
# =========================================================

def build_origin_classifications(sales, origins):

    results = []

    for origin in origins:

        historical_data = sales[
            sales["sales_date"] <= origin
        ]

        for (sku, store), group in historical_data.groupby(
            ["sku", "store_id"]
        ):

            group = group.sort_values("sales_date")

            history = group[
                "quantity_sold"
            ].to_numpy(dtype=float)

            classification = classify_demand(history)

            results.append({
                "origin": origin,
                "sku": sku,
                "store_id": store,
                "history_days": len(history),
                **classification,
            })

    return pd.DataFrame(results)


# =========================================================
# 4. CONVERT MODEL COLUMNS TO LONG FORMAT
# =========================================================

def convert_to_long_format(data):

    identifier_columns = [
        "origin",
        "sales_date",
        "sku",
        "store_id",
        "actual",
        "demand_pattern",
        "ADI",
        "CV2",
        "history_days",
    ]

    long_data = data.melt(
        id_vars=identifier_columns,
        value_vars=MODEL_NAMES,
        var_name="model",
        value_name="predicted",
    )

    return long_data


# =========================================================
# 5. PERFORMANCE METRICS
# =========================================================

def calculate_metrics(group):

    actual = group["actual"].to_numpy(dtype=float)

    predicted = group["predicted"].to_numpy(dtype=float)

    absolute_errors = np.abs(actual - predicted)

    denominator = np.abs(actual).sum()

    return {
        "forecast_records": len(group),
        "MAE_daily": absolute_errors.mean(),
        "RMSE_daily": np.sqrt(
            np.mean((actual - predicted) ** 2)
        ),
        "WAPE_percent": (
            absolute_errors.sum() / denominator * 100
            if denominator > 0
            else np.nan
        ),
        "actual_units": actual.sum(),
        "forecast_units": predicted.sum(),
    }


# =========================================================
# 6. ANALYZE MODEL PERFORMANCE BY DEMAND PATTERN
# =========================================================

def analyze_model_performance(data):

    results = []

    grouping = data.groupby(
        ["origin", "demand_pattern", "model"]
    )

    for (origin, pattern, model_name), group in grouping:

        metrics = calculate_metrics(group)

        results.append({
            "origin": origin,
            "demand_pattern": pattern,
            "model": model_name,
            **metrics,
        })

    return pd.DataFrame(results)


# =========================================================
# 7. MAIN
# =========================================================

def main():

    for output_file in [
        PATTERN_OUTPUT,
        SUMMARY_OUTPUT,
    ]:

        if output_file.exists():
            raise FileExistsError(
                f"Output already exists. Inspect before rerunning: "
                f"{output_file}"
            )

    if not SALES_FILE.exists():
        raise FileNotFoundError(
            f"Sales sample not found: {SALES_FILE}"
        )

    if not PREDICTION_FILE.exists():
        raise FileNotFoundError(
            f"Forecast comparison not found: {PREDICTION_FILE}"
        )

    print("LOADING SALES AND FORECAST DATA...")

    sales = pd.read_parquet(SALES_FILE)

    predictions = pd.read_csv(PREDICTION_FILE)

    sales["sales_date"] = pd.to_datetime(
        sales["sales_date"]
    )

    predictions["origin"] = pd.to_datetime(
        predictions["origin"]
    )

    predictions["sales_date"] = pd.to_datetime(
        predictions["sales_date"]
    )

    origins = sorted(
        predictions["origin"].unique()
    )

    print("SALES RECORDS:", len(sales))
    print("FORECAST RECORDS:", len(predictions))
    print("FORECAST ORIGINS:", len(origins))

    # -----------------------------------------------------
    # Historical demand classification
    # -----------------------------------------------------

    print("\nCLASSIFYING HISTORICAL DEMAND PATTERNS...")

    classifications = build_origin_classifications(
        sales,
        origins,
    )

    print("\nCLASSIFICATION COUNTS:")

    print(
        classifications["demand_pattern"]
        .value_counts()
        .to_string()
    )

    # -----------------------------------------------------
    # Join classification with forecast results
    # -----------------------------------------------------

    merged = predictions.merge(
        classifications,
        on=["origin", "sku", "store_id"],
        how="left",
        validate="many_to_one",
    )

    if merged["demand_pattern"].isnull().any():
        raise ValueError(
            "Some forecast records have no demand classification."
        )

    # -----------------------------------------------------
    # Convert six model columns into long format
    # -----------------------------------------------------

    print("\nCONVERTING MODEL RESULTS TO LONG FORMAT...")

    long_data = convert_to_long_format(merged)

    print("LONG-FORMAT RECORDS:", len(long_data))

    expected_records = len(predictions) * len(MODEL_NAMES)

    if len(long_data) != expected_records:
        raise ValueError(
            f"Expected {expected_records} long-format records, "
            f"found {len(long_data)}."
        )

    # -----------------------------------------------------
    # Model performance by demand pattern and origin
    # -----------------------------------------------------

    print("\nANALYZING MODEL PERFORMANCE...")

    summary = analyze_model_performance(long_data)

    if summary.empty:
        raise ValueError(
            "No model performance results were generated."
        )

    # -----------------------------------------------------
    # Best model per pattern and origin
    # -----------------------------------------------------

    best_indices = summary.groupby(
        ["origin", "demand_pattern"]
    )["WAPE_percent"].idxmin()

    best_models = summary.loc[
        best_indices
    ].sort_values(
        ["origin", "demand_pattern"]
    )

    # -----------------------------------------------------
    # Save new reports
    # -----------------------------------------------------

    classifications.to_csv(
        PATTERN_OUTPUT,
        index=False,
    )

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    # -----------------------------------------------------
    # Display results
    # -----------------------------------------------------

    print("\nDEMAND PATTERN COUNTS BY ORIGIN")

    print(
        classifications.groupby(
            ["origin", "demand_pattern"]
        ).size().unstack(fill_value=0).to_string()
    )

    print("\nMODEL PERFORMANCE BY DEMAND PATTERN")

    print(
        summary.sort_values(
            ["origin", "demand_pattern", "WAPE_percent"]
        ).round(4).to_string(index=False)
    )

    print("\nBEST MODEL PER DEMAND PATTERN AND ORIGIN")

    print(
        best_models[
            [
                "origin",
                "demand_pattern",
                "model",
                "WAPE_percent",
                "MAE_daily",
            ]
        ].round(4).to_string(index=False)
    )

    print("\nSAVED REPORTS:")
    print(PATTERN_OUTPUT)
    print(SUMMARY_OUTPUT)


if __name__ == "__main__":
    main()
