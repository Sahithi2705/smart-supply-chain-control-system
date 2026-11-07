# Shared contract decisions requiring owner sign-off

The implementation package uses the following proposed canonicalization decisions. They are explicitly surfaced here because they either add generated identifiers or normalize source names/types. Confirm these before treating contract version 1.0.0 as frozen or allowing downstream modules to code against these exact names.

| Area | Proposed decision | Why | Compatibility impact |
|---|---|---|---|
| SCMS supplier | Generate deterministic `supplier_key` from `Vendor + Manufacturing Site` | SCMS has no supplier ID column | Adds a source-local technical key |
| SCMS product | Generate deterministic `product_scms_key` from observed product descriptor fields | SCMS has no product ID column | Adds a source-local technical key |
| SCMS shipment | Generate deterministic `shipment_key` from ASN/PO and shipment attributes | SCMS has no shipment ID column | Adds a source-local technical key |
| Olist product lengths | Rename source typos `product_name_lenght` and `product_description_lenght` to `product_name_length` and `product_description_length` | Canonical spelling consistency | Downstream field-name change from raw source |
| Olist postal prefixes | Store customer/seller ZIP prefixes as strings | Postal codes are identifiers, not quantities; string read preserves leading zeroes | Type changes from inferred integer to string |
| M5 sales | Expose `cat_id` as `category_id` in `fact_sales`; retain `cat_id` in `dim_product` | More descriptive fact column | Additive/renamed fact attribute |
| M5 source snapshot | Use evaluation file as canonical fact source; validation file only verifies overlapping days | Evaluation has the longer 1,941-day horizon; validation has 1,913 days | Prevents duplicate overlapping sales rows |

Generated SCMS keys are deterministic within SCMS and do not imply any relationship to M5 or Olist product/supplier IDs. If a downstream module requires a different field name or key strategy, update this document and the schema together before release.
