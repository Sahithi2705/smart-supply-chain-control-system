
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = MODULE_DIR.parent

# Module 1 canonical data (read-only)
CANONICAL_DATA = Path(
    r"E:\SmartSupplyChainData\curated\m5_canonical_v2"
)

FACT_SALES = CANONICAL_DATA / "fact_sales" / "part-00000.parquet"
FACT_SELL_PRICES = CANONICAL_DATA / "fact_sell_prices" / "part-00000.parquet"
DIM_DATE = CANONICAL_DATA / "dim_date" / "part-00000.parquet"
DIM_PRODUCT = CANONICAL_DATA / "dim_product" / "part-00000.parquet"
DIM_STORE = CANONICAL_DATA / "dim_store" / "part-00000.parquet"

OUTPUT_DIR = MODULE_DIR / "outputs"
FEATURE_DIR = MODULE_DIR / "features"
MODEL_DIR = MODULE_DIR / "models"
EVALUATION_DIR = MODULE_DIR / "evaluation"

FORECAST_HORIZON = 28
VALIDATION_DAYS = 28
TEST_DAYS = 28
RANDOM_SEED = 42

SAMPLE_SKUS = 20
SAMPLE_STORES = 2

for directory in [OUTPUT_DIR, FEATURE_DIR, MODEL_DIR, EVALUATION_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def validate_input_files():
    required_files = [
        FACT_SALES,
        FACT_SELL_PRICES,
        DIM_DATE,
        DIM_PRODUCT,
        DIM_STORE,
    ]

    missing = [str(path) for path in required_files if not path.exists()]

    if missing:
        raise FileNotFoundError(
            "Missing canonical input files:\n" + "\n".join(missing)
        )

    return True
