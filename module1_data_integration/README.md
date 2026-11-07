# Module 1: Multi-Source Data Integration and Canonical Data Modelling

Local-first implementation for the M5 Forecasting, Olist Brazilian E-commerce and SCMS Delivery History datasets. AWS Glue is optional. The local pipeline uses Python/Pandas/NumPy, PyArrow Parquet and DuckDB; AWS S3 and Athena are documented as the cloud storage/query layer.

## Scope and design decisions

- M5, Olist and SCMS remain three separate source domains. Their product identifiers are never merged.
- M5 uses `sales_train_evaluation.csv` as the single full-history source. The 1,913 common day columns in `sales_train_validation.csv` were compared against evaluation: 30,490 base series IDs matched and 0 quantity mismatches were found. Validation is not appended because that would double-count overlapping history.
- Olist fact grain is order, order line and payment sequence, respectively.
- SCMS has no explicit supplier/product/shipment surrogate IDs. Deterministic SHA-256-derived technical keys are generated from the actual source attributes and documented as generated keys, not source IDs.
- Missing source values are retained. Unparseable SCMS workflow text is represented as null in typed date columns, while source text is retained in `*_source` fields for delivery dates and in the raw source CSV for all date fields.
- Monetary fields use float64 in this public-dataset implementation. For financial-grade accounting, consider decimal types and source-specific currency normalization.

## Repository layout

```text
module1_data_integration/
  profiling/
  transformations/
  validation/
  schemas/
  config/
  sql/
  aws/
  tests/
  data/raw/{m5,olist,scms}/
  data/interim/
  data/curated/{m5,olist,scms}/
  data/database/
```

## 1. Create an environment

Windows PowerShell:

```powershell
cd module1_data_integration
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Python 3.11 or 3.12 is recommended for current DuckDB/PyArrow wheel compatibility. If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.

## 2. Extract the three uploaded archives

Copy the uploaded ZIPs to a convenient local folder, then run from this project folder:

```powershell
python extract_archives.py `
  --m5-zip "C:\path\to\m5-forecasting-accuracy.zip" `
  --olist-zip "C:\path\to\archive.zip" `
  --scms-zip "C:\path\to\SCMS_Delivery_History_Dataset_20150929.csv.zip"
```

Only the requested M5, Olist and SCMS CSVs are extracted. Extra Olist geolocation/review/category-translation files are not silently added to the canonical contract.

## 3. Profile sources first

```powershell
python -m profiling.profile_sources
```

Outputs:
- `profiling/source_profile.json`
- `profiling/source_profile.md`

The profile uses chunked reads. Duplicate counts in the streaming profile are chunk-local; the post-ETL validator checks materialized canonical primary keys globally.

## 4. Run the canonical pipeline

```powershell
python run_pipeline.py
```

The pipeline:
1. Profiles all required raw CSVs.
2. Builds M5 dimensions, weekly sell-price fact and daily sales fact using DuckDB UNPIVOT + joins.
3. Builds Olist order, order-item, customer, seller, product and payment entities.
4. Builds SCMS procurement/delivery facts and supplier/shipment/product dimensions.
5. Validates canonical PK nulls/duplicates and writes validation evidence.
6. Creates `data/database/canonical.duckdb` with SQL views over the Parquet files.

M5 is the largest part: 30,490 product/store series x 1,941 days is approximately 59.3 million fact rows. Run on a machine with sufficient free disk space and memory. DuckDB is configured to a 3 GB memory limit in the M5 step; adjust if needed.

## 5. Query with DuckDB

```powershell
python build_duckdb.py
python -c "import duckdb; c=duckdb.connect('data/database/canonical.duckdb', read_only=True); print(c.sql('SELECT COUNT(*) FROM m5_fact_sales').fetchall()); print(c.sql('SELECT order_status, COUNT(*) FROM olist_fact_orders GROUP BY 1').df()); c.close()"
```

More queries are in `sql/sample_queries.sql`.

## 6. Validation

```powershell
python -m validation.validate_outputs
```

Review:
- `validation/post_etl_validation.json`
- `validation/post_etl_validation.csv`
- `data/curated/olist/relationship_checks.csv`
- `data/curated/scms/date_quality.csv`

The validator reports failures; it does not delete records or alter source facts to make checks pass. Review all failed checks before publishing.

## Canonical entities and grain

| Source | Entity | Grain / primary key |
|---|---|---|
| M5 | dim_product | `item_id` |
| M5 | dim_store | `store_id` |
| M5 | dim_date | `day_id` |
| M5 | fact_sales | `sales_date + sku + store_id` |
| M5 | fact_sell_prices | `store_id + sku + wm_yr_wk` |
| Olist | fact_orders | `order_id` |
| Olist | fact_order_items | `order_id + order_item_id` |
| Olist | dim_customer | `customer_id` |
| Olist | dim_seller | `seller_id` |
| Olist | dim_olist_product | `product_id` |
| Olist | fact_order_payments | `order_id + payment_sequential` |
| SCMS | fact_procurement | `procurement_id` (source `ID`) |
| SCMS | fact_delivery | `procurement_id` (source `ID`) |
| SCMS | dim_supplier | generated `supplier_key` |
| SCMS | dim_shipment | generated `shipment_key` |
| SCMS | dim_product_scms | generated `product_scms_key` |

Field-level schema: `schemas/canonical_schema.json`. Mapping decisions: `schemas/source_to_canonical_mapping.md`. ERD: `schemas/erd.md`.

## AWS S3 and Athena

AWS Glue is not required for the local pipeline. After local Parquet and DuckDB validation succeeds:

1. Configure AWS CLI using a non-root IAM identity with least privilege.
2. Follow `aws/s3_athena_runbook.md` to upload raw and curated files to the existing S3 bucket.
3. Configure Athena query results under `s3://smart-supply-chain-data-2026/athena-results/`.
4. Review and adapt `aws/athena_ddl.sql` to the actual Parquet schema before creating tables.
5. Run `sql/sample_queries.sql` in Athena and save query execution IDs/result exports/screenshots as evidence. The helper can execute statements one-by-one, for example `python aws/run_athena_query.py aws/athena_ddl.sql --database default` and then `python aws/run_athena_query.py aws/athena_validation_queries.sql --database supply_chain_canonical`.

`aws/iam_least_privilege_policy.json` is a starter policy for S3 upload/read, Athena query execution and Glue Data Catalog table creation. Replace `<ACCOUNT_ID>` with your account ID before attaching it. Athena API actions are initially scoped to `*`; narrow to a workgroup ARN where supported by the selected actions. It is not a Glue ETL job-creation policy. Keep public access blocked and never store AWS keys in this repository.

## Git workflow

Run inside the existing repository root after adding this folder:

```powershell
git switch -c feature/canonical-model
git add module1_data_integration
git commit -m "Build Module 1 canonical data integration pipeline"
git push -u origin feature/canonical-model
```

Then open a pull request from `feature/canonical-model` to `main`. Do not commit raw data, generated Parquet, DuckDB files, credentials or large profiling extracts unless your team explicitly wants those artifacts in Git LFS/object storage.

## Current execution status

- Source CSV headers and row counts inspected from the supplied archives.
- Olist full primary-key and tested foreign-key checks: zero duplicates/orphans.
- SCMS source `ID` uniqueness: zero duplicates.
- M5 validation/evaluation overlap: 30,490 base series IDs and 1,913 days checked; zero quantity mismatches.
- Python files compile-checked in the build environment.
- Parquet and DuckDB generation still requires installing `pyarrow` and `duckdb` on the execution machine. The current artifact-building environment had neither package and could not reach package indexes, so it has not fabricated or claimed Parquet/DB outputs.
- AWS S3/Athena execution has not been performed from this environment; AWS access remains account-dependent.

Additional Athena checks are in `aws/athena_validation_queries.sql`. Run them after the DDL and retain the query execution IDs/results as Module 1 evidence.

Before freezing the shared downstream contract, review `schemas/contract_decisions_pending_approval.md`. It lists the proposed SCMS technical keys and the small Olist/M5 naming/type normalizations that should be approved by the module owners.
