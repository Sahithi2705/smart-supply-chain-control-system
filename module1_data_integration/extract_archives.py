"""Extract the supplied source archives into the project's data/raw layout."""
import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ARCHIVES = {
    "m5": {
        "archive": "m5-forecasting-accuracy.zip",
        "members": ["calendar.csv", "sales_train_validation.csv", "sales_train_evaluation.csv", "sell_prices.csv"],
    },
    "olist": {
        "archive": "archive.zip",
        "members": ["olist_orders_dataset.csv", "olist_order_items_dataset.csv", "olist_products_dataset.csv",
                    "olist_sellers_dataset.csv", "olist_customers_dataset.csv", "olist_order_payments_dataset.csv"],
    },
    "scms": {"archive": "SCMS_Delivery_History_Dataset_20150929.csv.zip", "members": ["SCMS_Delivery_History_Dataset_20150929.csv"]},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--m5-zip", required=True)
    parser.add_argument("--olist-zip", required=True)
    parser.add_argument("--scms-zip", required=True)
    args = parser.parse_args()
    supplied = {"m5": args.m5_zip, "olist": args.olist_zip, "scms": args.scms_zip}
    for source, archive in supplied.items():
        target = ROOT / "data" / "raw" / source
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zf:
            available = set(zf.namelist())
            for member in ARCHIVES[source]["members"]:
                if member not in available:
                    raise FileNotFoundError(f"{member} not found inside {archive}")
                # Extract only named files, not unrequested auxiliary datasets.
                dest = target / member
                with zf.open(member) as src, dest.open("wb") as dst:
                    while True:
                        block = src.read(1024 * 1024)
                        if not block:
                            break
                        dst.write(block)
                print(f"Extracted {source}/{member}")

if __name__ == "__main__":
    main()
