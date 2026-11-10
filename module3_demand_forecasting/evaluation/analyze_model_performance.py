
import numpy as np
import pandas as pd

from module3_demand_forecasting.config.settings import OUTPUT_DIR


# =========================================================
# 1. FILE CONFIGURATION
# =========================================================

INPUT_FILE = OUTPUT_DIR / "all_models_comparison.csv"

OUTPUT_FILE = OUTPUT_DIR / "model_performance_by_sku.csv"

MODEL_NAMES = [
    "xgboost",
    "moving_average",
    "seasonal_naive",
    "croston",
    "sba",
    "tsb",
]


# =========================================================
# 2. METRIC CALCULATION
# =========================================================

def calculate_metrics(group, model_name):

    actual = group["actual"].to_numpy(dtype=float)

    predicted = group[model_name].to_numpy(dtype=float)

    absolute_errors = np.abs(actual - predicted)

    actual_total = np.abs(actual).sum()

    wape = (
        absolute_errors.sum() / actual_total * 100
        if actual_total > 0
        else np.nan
    )

    return {
        "forecast_records": len(group),
        "MAE_daily": absolute_errors.mean(),
        "RMSE_daily": np.sqrt(
            np.mean((actual - predicted) ** 2)
        ),
        "WAPE_percent": wape,
        "actual_units": actual.sum(),
        "forecast_units": predicted.sum(),
    }


# =========================================================
# 3. SKU-LEVEL MODEL PERFORMANCE
# =========================================================

def analyze_by_sku(data):

    results = []

    for sku, group in data.groupby("sku"):

        for model_name in MODEL_NAMES:

            metrics = calculate_metrics(
                group,
                model_name,
            )

            results.append({
                "sku": sku,
                "model": model_name,
                **metrics,
            })

    return pd.DataFrame(results)


# =========================================================
# 4. STORE-LEVEL MODEL PERFORMANCE
# =========================================================

def analyze_by_store(data):

    results = []

    for store, group in data.groupby("store_id"):

        for model_name in MODEL_NAMES:

            metrics = calculate_metrics(
                group,
                model_name,
            )

            results.append({
                "store_id": store,
                "model": model_name,
                **metrics,
            })

    return pd.DataFrame(results)


# =========================================================
# 5. BEST MODEL PER SKU
# =========================================================

def identify_best_model(sku_results):

    valid = sku_results.dropna(
        subset=["WAPE_percent"]
    )

    best_indices = valid.groupby("sku")[
        "WAPE_percent"
    ].idxmin()

    best = valid.loc[best_indices].copy()

    best = best.rename(columns={
        "model": "best_model",
        "WAPE_percent": "best_model_WAPE_percent",
    })

    return best[
        [
            "sku",
            "best_model",
            "best_model_WAPE_percent",
            "MAE_daily",
            "RMSE_daily",
        ]
    ].sort_values("best_model_WAPE_percent")


# =========================================================
# 6. MAIN
# =========================================================

def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Comparison file not found: {INPUT_FILE}"
        )

    if OUTPUT_FILE.exists():
        raise FileExistsError(
            f"Output already exists. Inspect before rerunning: "
            f"{OUTPUT_FILE}"
        )

    print("LOADING MODEL COMPARISON RESULTS...")

    data = pd.read_csv(INPUT_FILE)

    required_columns = [
        "sku",
        "store_id",
        "actual",
        *MODEL_NAMES,
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if data[required_columns].isnull().any().any():
        raise ValueError(
            "Missing values detected in required columns."
        )

    print("TOTAL RECORDS:", len(data))
    print("UNIQUE SKUS:", data["sku"].nunique())
    print("UNIQUE STORES:", data["store_id"].nunique())

    # -----------------------------------------------------
    # SKU-level analysis
    # -----------------------------------------------------

    sku_results = analyze_by_sku(data)

    # -----------------------------------------------------
    # Store-level analysis
    # -----------------------------------------------------

    store_results = analyze_by_store(data)

    # -----------------------------------------------------
    # Best model for each SKU
    # -----------------------------------------------------

    best_models = identify_best_model(sku_results)

    # -----------------------------------------------------
    # Save SKU-level output
    # -----------------------------------------------------

    sku_results.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nSKU-LEVEL PERFORMANCE")
    print(
        sku_results.sort_values(
            ["sku", "WAPE_percent"]
        ).round(4).to_string(index=False)
    )

    print("\nSTORE-LEVEL PERFORMANCE")
    print(
        store_results.round(4).to_string(index=False)
    )

    print("\nBEST MODEL PER SKU")
    print(
        best_models.round(4).to_string(index=False)
    )

    print("\nMODEL WIN COUNTS")

    print(
        best_models["best_model"]
        .value_counts()
        .to_string()
    )

    print("\nSAVED SKU REPORT:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
