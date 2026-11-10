
import numpy as np
import pandas as pd

from module3_demand_forecasting.config.settings import OUTPUT_DIR


# =========================================================
# 1. CONFIGURATION
# =========================================================

INPUT_FILE = OUTPUT_DIR / "all_models_comparison.csv"

OUTPUT_FILE = OUTPUT_DIR / "model_stability_by_origin.csv"

MODEL_NAMES = [
    "xgboost",
    "moving_average",
    "seasonal_naive",
    "croston",
    "sba",
    "tsb",
]

EXPECTED_ORIGINS = 3


# =========================================================
# 2. METRIC CALCULATION
# =========================================================

def calculate_metrics(group, model_name):

    actual = group["actual"].to_numpy(dtype=float)

    predicted = group[model_name].to_numpy(dtype=float)

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
# 3. PERFORMANCE BY FORECAST ORIGIN
# =========================================================

def analyze_by_origin(data):

    results = []

    for origin, origin_data in data.groupby("origin"):

        for model_name in MODEL_NAMES:

            metrics = calculate_metrics(
                origin_data,
                model_name,
            )

            results.append({
                "origin": origin,
                "model": model_name,
                **metrics,
            })

    return pd.DataFrame(results)


# =========================================================
# 4. MODEL RANKING PER ORIGIN
# =========================================================

def rank_models(stability_results):

    ranked = stability_results.copy()

    ranked["rank_by_WAPE"] = (
        ranked.groupby("origin")["WAPE_percent"]
        .rank(method="min", ascending=True)
    )

    return ranked.sort_values(
        ["origin", "rank_by_WAPE"]
    )


# =========================================================
# 5. CONSISTENCY SUMMARY
# =========================================================

def summarize_stability(ranked):

    summary = (
        ranked.groupby("model")
        .agg(
            average_WAPE=("WAPE_percent", "mean"),
            best_WAPE=("WAPE_percent", "min"),
            worst_WAPE=("WAPE_percent", "max"),
            average_rank=("rank_by_WAPE", "mean"),
            first_place_count=(
                "rank_by_WAPE",
                lambda values: (values == 1).sum(),
            ),
        )
        .reset_index()
    )

    return summary.sort_values(
        ["average_rank", "average_WAPE"]
    )


# =========================================================
# 6. SKU-LEVEL STABILITY
# =========================================================

def analyze_sku_stability(data):

    results = []

    for (sku, origin), group in data.groupby(
        ["sku", "origin"]
    ):

        for model_name in MODEL_NAMES:

            metrics = calculate_metrics(
                group,
                model_name,
            )

            results.append({
                "sku": sku,
                "origin": origin,
                "model": model_name,
                **metrics,
            })

    return pd.DataFrame(results)


# =========================================================
# 7. MAIN
# =========================================================

def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    if OUTPUT_FILE.exists():
        raise FileExistsError(
            f"Output already exists. Inspect before rerunning: "
            f"{OUTPUT_FILE}"
        )

    print("LOADING FORECAST COMPARISON DATA...")

    data = pd.read_csv(INPUT_FILE)

    required_columns = [
        "origin",
        "sales_date",
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

    data["origin"] = pd.to_datetime(data["origin"])

    origin_count = data["origin"].nunique()

    if origin_count != EXPECTED_ORIGINS:
        raise ValueError(
            f"Expected {EXPECTED_ORIGINS} forecast origins, "
            f"found {origin_count}."
        )

    print("TOTAL RECORDS:", len(data))
    print("FORECAST ORIGINS:", origin_count)
    print("UNIQUE SKUS:", data["sku"].nunique())
    print("UNIQUE STORES:", data["store_id"].nunique())

    # -----------------------------------------------------
    # Origin-level analysis
    # -----------------------------------------------------

    stability = analyze_by_origin(data)

    ranked = rank_models(stability)

    consistency = summarize_stability(ranked)

    # -----------------------------------------------------
    # SKU-level stability
    # -----------------------------------------------------

    sku_stability = analyze_sku_stability(data)

    # -----------------------------------------------------
    # Save the primary origin-level report
    # -----------------------------------------------------

    stability.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nMODEL PERFORMANCE BY ORIGIN")

    print(
        ranked[
            [
                "origin",
                "model",
                "MAE_daily",
                "RMSE_daily",
                "WAPE_percent",
                "rank_by_WAPE",
            ]
        ].round(4).to_string(index=False)
    )

    print("\nMODEL CONSISTENCY SUMMARY")

    print(
        consistency.round(4).to_string(index=False)
    )

    print("\nSKU-LEVEL STABILITY SAMPLE")

    print(
        sku_stability.head(18).round(4).to_string(
            index=False
        )
    )

    print("\nMODEL WINS BY ORIGIN")

    print(
        ranked[ranked["rank_by_WAPE"] == 1][
            ["origin", "model", "WAPE_percent"]
        ].to_string(index=False)
    )

    print("\nSAVED REPORT:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
