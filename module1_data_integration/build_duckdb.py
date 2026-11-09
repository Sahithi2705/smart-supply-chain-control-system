
"""Create and validate DuckDB views over canonical Parquet files."""

import duckdb

from config.settings import DUCKDB_FILE, CURATED


# ==========================================================
# CANONICAL ENTITY PATHS
# ==========================================================

ENTITIES = {
    # M5: New versioned canonical output
    "m5_dim_product": "m5_canonical_v2/dim_product/part-00000.parquet",
    "m5_dim_store": "m5_canonical_v2/dim_store/part-00000.parquet",
    "m5_dim_date": "m5_canonical_v2/dim_date/part-00000.parquet",
    "m5_fact_sales": "m5_canonical_v2/fact_sales/part-00000.parquet",
    "m5_fact_sell_prices": "m5_canonical_v2/fact_sell_prices/part-00000.parquet",

    # Olist
    "olist_fact_orders": "olist/fact_orders/part-00000.parquet",
    "olist_fact_order_items": "olist/fact_order_items/part-00000.parquet",
    "olist_dim_customer": "olist/dim_customer/part-00000.parquet",
    "olist_dim_seller": "olist/dim_seller/part-00000.parquet",
    "olist_dim_olist_product": "olist/dim_olist_product/part-00000.parquet",
    "olist_fact_order_payments": "olist/fact_order_payments/part-00000.parquet",

    # SCMS
    "scms_fact_procurement": "scms/fact_procurement/part-00000.parquet",
    "scms_fact_delivery": "scms/fact_delivery/part-00000.parquet",
    "scms_dim_supplier": "scms/dim_supplier/part-00000.parquet",
    "scms_dim_shipment": "scms/dim_shipment/part-00000.parquet",
    "scms_dim_product_scms": "scms/dim_product_scms/part-00000.parquet",
}


# ==========================================================
# HELPER
# ==========================================================

def qpath(path):
    return (
        str(path.resolve())
        .replace("\\", "/")
        .replace("'", "''")
    )


# ==========================================================
# MAIN DUCKDB BUILDER
# ==========================================================

def main():

    print("=" * 60)
    print("BUILDING CANONICAL DUCKDB DATABASE")
    print("=" * 60)

    # Check every source file before creating views.
    entity_paths = {}
    missing_files = []

    for view_name, relative_path in ENTITIES.items():

        parquet_path = (
            CURATED / relative_path
        ).resolve()

        if not parquet_path.is_file():
            missing_files.append(str(parquet_path))
        else:
            entity_paths[view_name] = parquet_path

    if missing_files:

        print("\nERROR: The following Parquet files are missing:")

        for path in missing_files:
            print(f"  - {path}")

        raise FileNotFoundError(
            f"{len(missing_files)} canonical Parquet file(s) are missing."
        )

    # Ensure database directory exists.
    DUCKDB_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nConnecting to DuckDB:", DUCKDB_FILE)

    con = duckdb.connect(str(DUCKDB_FILE))

    try:

        # --------------------------------------------------
        # 1. CREATE OR REPLACE ALL 16 VIEWS
        # --------------------------------------------------

        print("\nCREATING CANONICAL VIEWS")

        for view_name, parquet_path in entity_paths.items():

            escaped_path = qpath(parquet_path)

            con.execute(
                f"""
                CREATE OR REPLACE VIEW {view_name} AS
                SELECT *
                FROM read_parquet('{escaped_path}')
                """
            )

            print(f"Created view: {view_name}")

        # --------------------------------------------------
        # 2. VERIFY EXPECTED VIEWS
        # --------------------------------------------------

        result = con.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'main'
            """
        ).fetchall()

        created_views = {
            row[0] for row in result
        }

        expected_views = set(ENTITIES.keys())

        missing_views = expected_views - created_views

        if missing_views:
            raise RuntimeError(
                f"Missing DuckDB views: {sorted(missing_views)}"
            )

        # --------------------------------------------------
        # 3. QUERY VALIDATION
        # --------------------------------------------------

        print("\nVIEW QUERY VALIDATION")

        for view_name in ENTITIES:

            con.execute(
                f"SELECT * FROM {view_name} LIMIT 0"
            )

            columns = con.execute(
                f"DESCRIBE SELECT * FROM {view_name}"
            ).fetchall()

            print(
                f"PASS: {view_name} "
                f"({len(columns)} columns)"
            )

        # --------------------------------------------------
        # 4. SAMPLE QUERIES
        # --------------------------------------------------

        print("\nSAMPLE QUERY VALIDATION")

        sales_count = con.execute(
            "SELECT COUNT(*) FROM m5_fact_sales"
        ).fetchone()[0]

        print(
            f"M5 fact sales count: {sales_count:,}"
        )

        product_count = con.execute(
            "SELECT COUNT(*) FROM m5_dim_product"
        ).fetchone()[0]

        print(
            f"M5 product count: {product_count:,}"
        )

        order_count = con.execute(
            "SELECT COUNT(*) FROM olist_fact_orders"
        ).fetchone()[0]

        print(
            f"Olist order count: {order_count:,}"
        )

        procurement_count = con.execute(
            "SELECT COUNT(*) FROM scms_fact_procurement"
        ).fetchone()[0]

        print(
            f"SCMS procurement count: {procurement_count:,}"
        )

        # --------------------------------------------------
        # 5. FINAL SUMMARY
        # --------------------------------------------------

        print("\n" + "=" * 60)
        print("DUCKDB BUILD COMPLETED SUCCESSFULLY")
        print(f"Database: {DUCKDB_FILE}")
        print(f"Expected views: {len(ENTITIES)}")
        print(f"Created views: {len(created_views & expected_views)}")
        print("All views passed query validation.")
        print("=" * 60)

    finally:
        con.close()


if __name__ == "__main__":
    main()
