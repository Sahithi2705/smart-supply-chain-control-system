
"""Create and validate DuckDB views over canonical Parquet files."""

import duckdb

from config.settings import DUCKDB_FILE, CURATED


ENTITIES = {
    "m5_dim_product": "m5/dim_product/part-00000.parquet",
    "m5_dim_store": "m5/dim_store/part-00000.parquet",
    "m5_dim_date": "m5/dim_date/part-00000.parquet",
    "m5_fact_sales": "m5/fact_sales/part-00000.parquet",
    "m5_fact_sell_prices": "m5/fact_sell_prices/part-00000.parquet",

    "olist_fact_orders": "olist/fact_orders/part-00000.parquet",
    "olist_fact_order_items": "olist/fact_order_items/part-00000.parquet",
    "olist_dim_customer": "olist/dim_customer/part-00000.parquet",
    "olist_dim_seller": "olist/dim_seller/part-00000.parquet",
    "olist_dim_olist_product": "olist/dim_olist_product/part-00000.parquet",
    "olist_fact_order_payments": "olist/fact_order_payments/part-00000.parquet",

    "scms_fact_procurement": "scms/fact_procurement/part-00000.parquet",
    "scms_fact_delivery": "scms/fact_delivery/part-00000.parquet",
    "scms_dim_supplier": "scms/dim_supplier/part-00000.parquet",
    "scms_dim_shipment": "scms/dim_shipment/part-00000.parquet",
    "scms_dim_product_scms": "scms/dim_product_scms/part-00000.parquet",
}


def main():
    print("=" * 60)
    print("BUILDING CANONICAL DUCKDB DATABASE")
    print("=" * 60)

    # Check every source file before creating the database.
    entity_paths = {}
    missing_files = []

    for view_name, relative_path in ENTITIES.items():
        parquet_path = (CURATED / relative_path).resolve()

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

    # Ensure the database directory exists.
    DUCKDB_FILE.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DUCKDB_FILE))

    try:
        # Create one persistent view for each canonical entity.
        for view_name, parquet_path in entity_paths.items():
            escaped_path = str(parquet_path).replace("'", "''")

            con.execute(
                f"""
                CREATE OR REPLACE VIEW {view_name} AS
                SELECT *
                FROM read_parquet('{escaped_path}')
                """
            )

            print(f"Created view: {view_name}")

        # Verify that all expected views exist.
        result = con.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'main'
            """
        ).fetchall()

        created_views = {row[0] for row in result}
        expected_views = set(ENTITIES.keys())

        missing_views = expected_views - created_views

        if missing_views:
            raise RuntimeError(
                f"Missing DuckDB views: {sorted(missing_views)}"
            )

        # Verify that every view can be queried and inspect its schema.
        print("\nVIEW QUERY VALIDATION")

        for view_name in ENTITIES:
            con.execute(f"SELECT * FROM {view_name} LIMIT 0")
            columns = con.execute(
                f"DESCRIBE SELECT * FROM {view_name}"
            ).fetchall()

            print(
                f"PASS: {view_name} "
                f"({len(columns)} columns)"
            )

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
