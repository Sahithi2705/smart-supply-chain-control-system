# AWS S3 + Athena runbook (Glue optional)

## S3 layout

```text
s3://smart-supply-chain-data-2026/
  raw/m5/
  raw/olist/
  raw/scms/
  curated/m5/<entity>/
  curated/olist/<entity>/
  curated/scms/<entity>/
  athena-results/
```

Upload raw CSVs and curated Parquet files separately. Keep S3 Block Public Access enabled, use bucket-owner-enforced object ownership, and enable default encryption (SSE-S3 or SSE-KMS). Do not make the bucket public.

## IAM

Attach `iam_least_privilege_policy.json` to a dedicated IAM role/user used for uploads and Athena access. Replace the bucket name if yours differs. The policy is a starter policy and may need KMS permissions if SSE-KMS is selected. Do not create access keys for the root user; prefer an IAM role or IAM Identity Center credentials. Never commit credentials to GitHub.

## Upload

From the project root, after configuring AWS CLI with a non-root identity:

```powershell
aws s3 sync .\data\raw\m5 s3://smart-supply-chain-data-2026/raw/m5/ --exclude ".gitkeep"
aws s3 sync .\data\raw\olist s3://smart-supply-chain-data-2026/raw/olist/ --exclude ".gitkeep"
aws s3 sync .\data\raw\scms s3://smart-supply-chain-data-2026/raw/scms/ --exclude ".gitkeep"
aws s3 sync .\data\curated\m5 s3://smart-supply-chain-data-2026/curated/m5/ --exclude ".gitkeep"
aws s3 sync .\data\curated\olist s3://smart-supply-chain-data-2026/curated/olist/ --exclude ".gitkeep"
aws s3 sync .\data\curated\scms s3://smart-supply-chain-data-2026/curated/scms/ --exclude ".gitkeep"
```

The `sync` command preserves entity-level subdirectories. Recommended object key shape: `curated/<source>/<entity>/part-*.parquet`.

## Athena

1. Open Athena in the same region as the S3 bucket.
2. Configure query result location as `s3://smart-supply-chain-data-2026/athena-results/`.
3. Run `athena_ddl.sql` after adapting table DDL to the exact Parquet schemas produced by the pipeline.
4. Run `../sql/sample_queries.sql` in Athena after creating the corresponding tables/views.
5. Save query execution IDs, CSV result exports, and console screenshots in the project evidence folder.

Note: the DDL file is a starter for the primary fact tables. Generate/verify all table DDLs from the actual Parquet schemas before production use. Athena access depends on account/service permissions; local ETL is not blocked by AWS access.
