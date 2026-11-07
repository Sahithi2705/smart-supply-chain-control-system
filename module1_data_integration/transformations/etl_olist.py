"""Olist canonical entities. Relationships remain source-system-specific."""
import pandas as pd
from config.settings import OLIST_FILES, CURATED
from transformations.common import write_parquet, add_source_metadata, parse_dates, assert_finite_numeric


def run_olist():
    for key, path in OLIST_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing Olist {key}: {path}")
    out = CURATED / "olist"
    out.mkdir(parents=True, exist_ok=True)
    orders = pd.read_csv(OLIST_FILES["orders"])
    items = pd.read_csv(OLIST_FILES["items"])
    products = pd.read_csv(OLIST_FILES["products"])
    sellers = pd.read_csv(OLIST_FILES["sellers"], dtype={"seller_zip_code_prefix": "string"})
    customers = pd.read_csv(OLIST_FILES["customers"], dtype={"customer_zip_code_prefix": "string"})
    payments = pd.read_csv(OLIST_FILES["payments"])

    orders = parse_dates(orders, ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"])
    items = parse_dates(items, ["shipping_limit_date"])
    orders = add_source_metadata(orders, "OLIST", "order_id")
    items["source_system"] = "OLIST"
    items["source_record_id"] = items["order_id"].astype("string") + ":" + items["order_item_id"].astype("string")
    payments["source_system"] = "OLIST"
    payments["source_record_id"] = payments["order_id"].astype("string") + ":" + payments["payment_sequential"].astype("string")
    customers = add_source_metadata(customers, "OLIST", "customer_id")
    sellers = add_source_metadata(sellers, "OLIST", "seller_id")
    customers["customer_zip_code_prefix"] = customers["customer_zip_code_prefix"].astype("string")
    sellers["seller_zip_code_prefix"] = sellers["seller_zip_code_prefix"].astype("string")
    products = add_source_metadata(products, "OLIST", "product_id")

    # Preserve the source's original Portuguese category label and spelling in the canonical attribute.
    products = products.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })
    for c in ["price", "freight_value"]:
        items[c] = pd.to_numeric(items[c], errors="coerce")
    for c in ["payment_value", "payment_installments", "payment_sequential"]:
        payments[c] = pd.to_numeric(payments[c], errors="coerce")
    assert_finite_numeric(items, ["price", "freight_value"], "OLIST.fact_order_items")
    assert_finite_numeric(payments, ["payment_value"], "OLIST.fact_order_payments")

    entities = {
        "fact_orders": orders,
        "fact_order_items": items,
        "dim_customer": customers,
        "dim_seller": sellers,
        "dim_olist_product": products,
        "fact_order_payments": payments,
    }
    for name, df in entities.items():
        write_parquet(df, out / name / "part-00000.parquet")

    # Write a compact relationship-validation snapshot; no orphan records are deleted.
    checks = {
        "order_items_without_order": int((~items["order_id"].isin(orders["order_id"])).sum()),
        "order_items_without_customer_dimension_via_order": int((~items["order_id"].map(orders.set_index("order_id")["customer_id"]).isin(customers["customer_id"])).sum()),
        "order_items_without_product": int((~items["product_id"].isin(products["product_id"])).sum()),
        "order_items_without_seller": int((~items["seller_id"].isin(sellers["seller_id"])).sum()),
        "payments_without_order": int((~payments["order_id"].isin(orders["order_id"])).sum()),
    }
    pd.DataFrame([{"check": k, "violation_count": v} for k, v in checks.items()]).to_csv(out / "relationship_checks.csv", index=False)
    print(f"Olist canonical files written to {out}; relationship checks: {checks}")

if __name__ == "__main__":
    run_olist()
