from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
CURATED = DATA / "curated"
DATABASE = DATA / "database"
PROFILE = ROOT / "profiling" / "source_profile.json"
DUCKDB_FILE = DATABASE / "canonical.duckdb"

M5_FILES = {
    "validation": RAW / "m5" / "sales_train_validation.csv",
    "evaluation": RAW / "m5" / "sales_train_evaluation.csv",
    "calendar": RAW / "m5" / "calendar.csv",
    "prices": RAW / "m5" / "sell_prices.csv",
}
OLIST_FILES = {
    "orders": RAW / "olist" / "olist_orders_dataset.csv",
    "items": RAW / "olist" / "olist_order_items_dataset.csv",
    "products": RAW / "olist" / "olist_products_dataset.csv",
    "sellers": RAW / "olist" / "olist_sellers_dataset.csv",
    "customers": RAW / "olist" / "olist_customers_dataset.csv",
    "payments": RAW / "olist" / "olist_order_payments_dataset.csv",
}
# Correct the sellers path separately to keep the mapping explicit.
OLIST_FILES["sellers"] = RAW / "olist" / "olist_sellers_dataset.csv"
SCMS_FILE = RAW / "scms" / "SCMS_Delivery_History_Dataset_20150929.csv"

for path in [INTERIM, CURATED / "m5", CURATED / "olist", CURATED / "scms", DATABASE]:
    path.mkdir(parents=True, exist_ok=True)
