# Module 1: Multi-Source Data Integration and Canonical Data Modelling

**Project:** Multi-Cloud Smart Supply Chain Control Tower  
**Implementation status:** Local ETL, canonical validation, DuckDB build and independent view verification completed.

Module 1 integrates the M5 Forecasting, Olist Brazilian E-Commerce and SCMS Delivery History datasets into 16 curated entities. Curated outputs are stored as Parquet, with a DuckDB database exposing SQL views over those files.

## Scope and design decisions

- M5, Olist and SCMS remain separate source domains. Their product identifiers are not treated as interchangeable.
- M5 sales are normalized from daily wide columns into a long-format fact table. The curated `m5_fact_sales` view exposes 11 canonical columns; the intermediate `d` field is not part of the canonical fact contract.
- Olist facts preserve order, order-line and payment-sequence grains.
- SCMS generated supplier, shipment and product keys are technical keys, not source identifiers.
- Missing source values are retained and validation observations are reported rather than silently corrected.
- The local DuckDB views read the curated Parquet files. The database therefore depends on the configured Parquet locations being available.

## Technology stack

- Python, Pandas and NumPy
- PyArrow and Apache Parquet
- DuckDB
- PowerShell / VS Code
- Git and GitHub

## Local data locations

Raw source files remain in the repository's `data/raw/` folder.

Curated data and the analytical database are stored outside the Git repository to avoid committing large generated datasets:

- Curated root: `E:\SmartSupplyChainData\curated\`
- M5: `E:\SmartSupplyChainData\curated\m5_canonical_v2\`
- Olist: `E:\SmartSupplyChainData\curated\olist\`
- SCMS: `E:\SmartSupplyChainData\curated\scms\`
- DuckDB: `E:\SmartSupplyChainData\database\canonical.duckdb`

These are the paths on the implementation machine. Update `settings.py` when reproducing the pipeline on another machine.

## Canonical entities and grain

| Source | Entity / DuckDB view | Rows | Grain / key |
|---|---|---:|---|
| M5 | `m5_dim_product` | 3,049 | item |
| M5 | `m5_dim_store` | 10 | store |
| M5 | `m5_dim_date` | 1,969 | date/day |
| M5 | `m5_fact_sales` | 59,181,090 | sales date + SKU + store |
| M5 | `m5_fact_sell_prices` | 6,841,121 | store + SKU + week |
| Olist | `olist_fact_orders` | 99,441 | order |
| Olist | `olist_fact_order_items` | 112,650 | order + order item |
| Olist | `olist_dim_customer` | 99,441 | customer |
| Olist | `olist_dim_seller` | 3,095 | seller |
| Olist | `olist_dim_olist_product` | 32,951 | product |
| Olist | `olist_fact_order_payments` | 103,886 | order + payment sequence |
| SCMS | `scms_fact_procurement` | 10,324 | procurement/source ID |
| SCMS | `scms_fact_delivery` | 10,324 | procurement/source ID |
| SCMS | `scms_dim_supplier` | 805 | generated supplier key |
| SCMS | `scms_dim_shipment` | 7,030 | generated shipment key |
| SCMS | `scms_dim_product_scms` | 184 | generated product key |

Field-level schema and mapping documentation are maintained under `schemas/`.

## Reproduction commands

Run commands from `module1_data_integration/` in the configured Python environment.

```powershell
python -m profiling.profile_sources
python -m validation.validate_outputs
python -m build_duckdb
```

**Important:** The completed ETL outputs already exist on the implementation machine. Do not rerun ETL stages over existing curated outputs. The ETL writers intentionally protect existing outputs from accidental overwrite. To reproduce on a fresh machine, first configure paths and raw inputs, then follow the individual transformation scripts and their safeguards.

## Validation evidence

The completed post-ETL validation run reported:

- **103 total checks**
- **103 passed**
- **0 failed**
- **15/15 foreign-key checks** with zero orphan rows
- **6/6 business-rule checks** with zero violations
- **16/16 entities** validated

Informational data observations (not validation failures):

- SCMS early deliveries: **2,814**
- M5 sales rows without a matching weekly price: **12,299,413**

Validation reports:

- `validation/post_etl_validation_run2.json`
- `validation/post_etl_validation_run2.csv`

The earlier validation reports were preserved.

## DuckDB analytical layer

Database: `E:\SmartSupplyChainData\database\canonical.duckdb`

The build created 16 views and passed query validation for every view. Sample counts returned by the build:

- M5 fact sales: 59,181,090
- M5 products: 3,049
- Olist orders: 99,441
- SCMS procurement: 10,324

A separate read-only connection independently confirmed that the database opens and contains exactly 16 registered views.

Example read-only query:

```python
import duckdb

con = duckdb.connect(
    r"E:\SmartSupplyChainData\database\canonical.duckdb",
    read_only=True,
)
print(con.execute("SELECT COUNT(*) FROM m5_fact_sales").fetchone())
con.close()
```

## Downstream handover

- **Module 2 – Real-Time Event Processing:** use compatible product, supplier and shipment reference data only after explicit key mapping.
- **Module 3 – Demand Forecasting:** use M5 historical sales, date, store, product and price entities.
- **Module 4 – Anomaly and Fraud Detection:** use Olist order/payment entities and SCMS procurement/delivery entities.
- **Module 5 – Risk Correlation and Decision Intelligence:** correlate validated indicators across domains while preserving source identity.
- **Module 6 – Control Tower Visualisation:** consume agreed analytical outputs and KPIs.

A shared DuckDB database does not make unrelated identifiers equivalent. Cross-source joins require explicit business-key mapping.

## Cloud deployment status

This milestone documents the **local Parquet + DuckDB implementation**. AWS S3, Glue Catalog and Athena deployment must be verified separately; this README does not claim that those cloud steps have been executed.

## Git and data handling

Do not commit generated Parquet files, the DuckDB database, credentials, or large raw datasets to ordinary Git history. Keep large data in the configured data storage/object storage and commit code, schemas, SQL, and documentation. Never commit AWS access keys or secrets.
