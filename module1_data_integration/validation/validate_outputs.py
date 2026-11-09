
"""
Comprehensive validation for the 16 canonical entities.

Uses DuckDB to query Parquet files without loading
the 59-million-row M5 sales fact into Pandas.
"""

import json

import duckdb
import pandas as pd

from config.settings import CURATED, ROOT, DUCKDB_FILE


CHECKS = []

# M5 now has a separate versioned canonical output directory.
M5_CURATED = CURATED / "m5_canonical_v2"


def record(source, check, passed, detail):
    CHECKS.append({
        "source": source,
        "check": check,
        "passed": bool(passed),
        "detail": str(detail)
    })


def qpath(path):
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def get_entity_path(system, entity):
    """Return the correct Parquet path for each canonical entity."""

    if system == "m5":
        base = M5_CURATED
    else:
        base = CURATED / system

    return base / entity / "part-00000.parquet"


def main():

    CHECKS.clear()

    print("\n========== CANONICAL DATA VALIDATION ==========\n")

    con = duckdb.connect(str(DUCKDB_FILE))

    try:

        # --------------------------------------------------
        # 1. DEFINE ALL 16 CANONICAL ENTITIES
        # --------------------------------------------------

        entities = {
            "m5": {
                "dim_product": ["sku"],
                "dim_store": ["store_id"],
                "dim_date": ["day_id"],
                "fact_sell_prices": [
                    "store_id", "sku", "wm_yr_wk"
                ],
                "fact_sales": [
                    "source_record_id", "d"
                ],
            },

            "olist": {
                "fact_orders": ["order_id"],
                "fact_order_items": [
                    "order_id", "order_item_id"
                ],
                "dim_customer": ["customer_id"],
                "dim_seller": ["seller_id"],
                "dim_olist_product": ["product_id"],
                "fact_order_payments": [
                    "order_id", "payment_sequential"
                ],
            },

            "scms": {
                "fact_procurement": ["procurement_id"],
                "fact_delivery": ["procurement_id"],
                "dim_supplier": ["supplier_key"],
                "dim_shipment": ["shipment_key"],
                "dim_product_scms": ["product_scms_key"],
            },
        }

        # --------------------------------------------------
        # 2. EXPECTED ROW COUNTS
        # --------------------------------------------------

        expected_rows = {
            ("m5", "dim_product"): 3049,
            ("m5", "dim_store"): 10,
            ("m5", "dim_date"): 1969,
            ("m5", "fact_sell_prices"): 6841121,
            ("m5", "fact_sales"): 59181090,

            ("olist", "fact_orders"): 99441,
            ("olist", "fact_order_items"): 112650,
            ("olist", "dim_customer"): 99441,
            ("olist", "dim_seller"): 3095,
            ("olist", "dim_olist_product"): 32951,
            ("olist", "fact_order_payments"): 103886,

            ("scms", "fact_procurement"): 10324,
            ("scms", "fact_delivery"): 10324,
            ("scms", "dim_supplier"): 805,
            ("scms", "dim_shipment"): 7030,
            ("scms", "dim_product_scms"): 184,
        }

        views = {}

        # --------------------------------------------------
        # 3. ENTITY EXISTENCE, ROW COUNTS AND PRIMARY KEYS
        # --------------------------------------------------

        print("ENTITY VALIDATION")

        for system, table_defs in entities.items():

            for entity, pk_columns in table_defs.items():

                path = get_entity_path(system, entity)

                if not path.exists():

                    record(
                        system,
                        f"{entity}_exists",
                        False,
                        f"Missing file: {path}"
                    )

                    print(f"{system}.{entity}: MISSING")
                    continue

                view = f"v_{system}_{entity}"

                con.execute(
                    f"""
                    CREATE OR REPLACE VIEW {view}
                    AS SELECT *
                    FROM read_parquet('{qpath(path)}')
                    """
                )

                views[(system, entity)] = view

                count = con.execute(
                    f"SELECT COUNT(*) FROM {view}"
                ).fetchone()[0]

                print(f"{system}.{entity}: {count:,} rows")

                record(
                    system,
                    f"{entity}_exists",
                    True,
                    str(path)
                )

                expected = expected_rows[(system, entity)]

                record(
                    system,
                    f"{entity}_expected_row_count",
                    count == expected,
                    f"actual={count}; expected={expected}"
                )

                # Primary-key NULL validation
                null_expr = " OR ".join(
                    [f'"{column}" IS NULL' for column in pk_columns]
                )

                nulls = con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {view}
                    WHERE {null_expr}
                    """
                ).fetchone()[0]

                record(
                    system,
                    f"{entity}_pk_nulls",
                    nulls == 0,
                    nulls
                )

                # Primary-key duplicate validation
                group_columns = ", ".join(
                    [f'"{column}"' for column in pk_columns]
                )

                duplicates = con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM (
                        SELECT {group_columns}
                        FROM {view}
                        GROUP BY {group_columns}
                        HAVING COUNT(*) > 1
                    )
                    """
                ).fetchone()[0]

                record(
                    system,
                    f"{entity}_pk_duplicates",
                    duplicates == 0,
                    duplicates
                )

                # Source metadata validation
                metadata_nulls = con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {view}
                    WHERE source_system IS NULL
                       OR source_record_id IS NULL
                    """
                ).fetchone()[0]

                record(
                    system,
                    f"{entity}_source_metadata_nulls",
                    metadata_nulls == 0,
                    metadata_nulls
                )

        # --------------------------------------------------
        # 4. FOREIGN-KEY VALIDATION
        # --------------------------------------------------

        print("\nFOREIGN KEY VALIDATION")

        relationships = [
            (
                "m5", "fact_sales_sku_fk",
                "fact_sales", "sku",
                "dim_product", "sku"
            ),
            (
                "m5", "fact_sales_store_fk",
                "fact_sales", "store_id",
                "dim_store", "store_id"
            ),
            (
                "m5", "fact_sales_date_fk",
                "fact_sales", "sales_date",
                "dim_date", "date"
            ),
            (
                "m5", "fact_sell_prices_product_fk",
                "fact_sell_prices", "sku",
                "dim_product", "sku"
            ),
            (
                "m5", "fact_sell_prices_store_fk",
                "fact_sell_prices", "store_id",
                "dim_store", "store_id"
            ),
            (
                "olist", "fact_orders_customer_fk",
                "fact_orders", "customer_id",
                "dim_customer", "customer_id"
            ),
            (
                "olist", "fact_items_order_fk",
                "fact_order_items", "order_id",
                "fact_orders", "order_id"
            ),
            (
                "olist", "fact_items_product_fk",
                "fact_order_items", "product_id",
                "dim_olist_product", "product_id"
            ),
            (
                "olist", "fact_items_seller_fk",
                "fact_order_items", "seller_id",
                "dim_seller", "seller_id"
            ),
            (
                "olist", "fact_payments_order_fk",
                "fact_order_payments", "order_id",
                "fact_orders", "order_id"
            ),
            (
                "scms", "fact_procurement_supplier_fk",
                "fact_procurement", "supplier_key",
                "dim_supplier", "supplier_key"
            ),
            (
                "scms", "fact_procurement_product_fk",
                "fact_procurement", "product_scms_key",
                "dim_product_scms", "product_scms_key"
            ),
            (
                "scms", "fact_delivery_shipment_fk",
                "fact_delivery", "shipment_key",
                "dim_shipment", "shipment_key"
            ),
            (
                "scms", "fact_delivery_supplier_fk",
                "fact_delivery", "supplier_key",
                "dim_supplier", "supplier_key"
            ),
            (
                "scms", "fact_delivery_product_fk",
                "fact_delivery", "product_scms_key",
                "dim_product_scms", "product_scms_key"
            ),
        ]

        for system, name, child, child_key, parent, parent_key in relationships:

            child_view = views.get((system, child))
            parent_view = views.get((system, parent))

            if child_view is None or parent_view is None:

                record(
                    system,
                    name,
                    False,
                    "Required child or parent entity is missing"
                )

                continue

            sql = f"""
                SELECT COUNT(*)
                FROM {child_view} c
                LEFT JOIN {parent_view} p
                    ON c."{child_key}" = p."{parent_key}"
                WHERE c."{child_key}" IS NOT NULL
                  AND p."{parent_key}" IS NULL
            """

            try:

                violations = con.execute(sql).fetchone()[0]

                record(
                    system,
                    name,
                    violations == 0,
                    violations
                )

                print(f"{name}: {violations:,} orphans")

            except Exception as exc:

                record(
                    system,
                    name,
                    False,
                    f"Could not execute: {exc}"
                )

        # --------------------------------------------------
        # 5. BUSINESS-RULE VALIDATION
        # --------------------------------------------------

        print("\nBUSINESS RULE VALIDATION")

        business_checks = [
            (
                "m5", "negative_sales_quantity",
                "fact_sales",
                """
                SELECT COUNT(*)
                FROM v_m5_fact_sales
                WHERE quantity_sold < 0
                """
            ),
            (
                "m5", "negative_sell_price",
                "fact_sell_prices",
                """
                SELECT COUNT(*)
                FROM v_m5_fact_sell_prices
                WHERE unit_price < 0
                """
            ),
            (
                "olist", "negative_item_price_or_freight",
                "fact_order_items",
                """
                SELECT COUNT(*)
                FROM v_olist_fact_order_items
                WHERE price < 0 OR freight_value < 0
                """
            ),
            (
                "olist", "negative_payment_value",
                "fact_order_payments",
                """
                SELECT COUNT(*)
                FROM v_olist_fact_order_payments
                WHERE payment_value < 0
                """
            ),
            (
                "scms", "negative_procurement_values",
                "fact_procurement",
                """
                SELECT COUNT(*)
                FROM v_scms_fact_procurement
                WHERE line_item_quantity < 0
                   OR line_item_value_usd < 0
                   OR pack_price_usd < 0
                   OR unit_price_usd < 0
                """
            ),
            (
                "olist", "order_delivery_before_purchase",
                "fact_orders",
                """
                SELECT COUNT(*)
                FROM v_olist_fact_orders
                WHERE order_delivered_customer_date
                      < order_purchase_timestamp
                """
            ),
        ]

        for system, name, required_entity, sql in business_checks:

            if (system, required_entity) not in views:

                record(
                    system,
                    name,
                    False,
                    "Required entity is missing"
                )

                continue

            try:

                violations = con.execute(sql).fetchone()[0]

                record(
                    system,
                    name,
                    violations == 0,
                    violations
                )

                print(f"{name}: {violations:,} violations")

            except Exception as exc:

                record(
                    system,
                    name,
                    False,
                    f"Could not execute: {exc}"
                )

        # --------------------------------------------------
        # 6. SCMS EARLY DELIVERY INFORMATIONAL METRIC
        # --------------------------------------------------

        print("\nSCMS DELIVERY OBSERVATIONS")

        if ("scms", "fact_delivery") in views:

            early_deliveries = con.execute(
                """
                SELECT COUNT(*)
                FROM v_scms_fact_delivery
                WHERE delivered_to_client_date
                      < scheduled_delivery_date
                """
            ).fetchone()[0]

            record(
                "scms",
                "early_deliveries_informational",
                True,
                (
                    f"{early_deliveries:,} deliveries occurred "
                    "before scheduled dates. Original dates preserved."
                )
            )

            print(
                f"Early deliveries (informational): "
                f"{early_deliveries:,}"
            )

        # --------------------------------------------------
        # 7. M5 MISSING PRICE COVERAGE
        # --------------------------------------------------

        print("\nM5 PRICE COVERAGE")

        if ("m5", "fact_sales") in views:

            missing_prices = con.execute(
                """
                SELECT COUNT(*)
                FROM v_m5_fact_sales
                WHERE unit_price IS NULL
                """
            ).fetchone()[0]

            record(
                "m5",
                "sales_rows_without_weekly_price",
                True,
                (
                    f"{missing_prices:,} rows without weekly price. "
                    "Reported, not dropped or imputed."
                )
            )

            print(
                f"Sales rows without weekly price: "
                f"{missing_prices:,}"
            )

    finally:
        con.close()

    # --------------------------------------------------
    # 8. SAVE VALIDATION REPORTS
    # --------------------------------------------------

    validation_dir = ROOT / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)

    json_path = (
        validation_dir / "post_etl_validation.json"
    )

    csv_path = (
        validation_dir / "post_etl_validation.csv"
    )

    json_path.write_text(
        json.dumps(CHECKS, indent=2),
        encoding="utf-8"
    )

    pd.DataFrame(CHECKS).to_csv(
        csv_path,
        index=False
    )

    failed = [
        check for check in CHECKS
        if not check["passed"]
    ]

    passed = len(CHECKS) - len(failed)

    print("\n========== VALIDATION SUMMARY ==========")

    print(f"Total checks: {len(CHECKS)}")
    print(f"Passed: {passed}")
    print(f"Failed: {len(failed)}")

    print(f"\nJSON report: {json_path}")
    print(f"CSV report: {csv_path}")

    if failed:

        print("\nFAILED CHECKS:")

        print(
            pd.DataFrame(failed).to_string(index=False)
        )

        raise SystemExit(1)

    print("\nALL CANONICAL VALIDATION CHECKS PASSED.")


if __name__ == "__main__":
    main()
