# Canonical data dictionary

All IDs are stored as strings unless the source contract defines a numeric row identifier. Monetary values are `float64` in this initial public-dataset contract; downstream financial use should consider decimal precision. Dates are typed `date`; Olist event times are timestamps.

| System | Entity | Grain / primary key | Description |
|---|---|---|---|
| M5 | dim_product | `item_id` | Product item, department and category |
| M5 | dim_store | `store_id` | Store and state |
| M5 | dim_date | `day_id` | M5 day/date/calendar attributes |
| M5 | fact_sales | `sales_date, sku, store_id` | Daily unit sales by item and store, with calendar and weekly price context |
| M5 | fact_sell_prices | `store_id, sku, wm_yr_wk` | Weekly selling price |
| Olist | fact_orders | `order_id` | Order lifecycle and customer reference |
| Olist | fact_order_items | `order_id, order_item_id` | Products/sellers and item-level price/freight |
| Olist | dim_customer | `customer_id` | Customer address attributes and unique-customer identifier |
| Olist | dim_seller | `seller_id` | Seller address attributes |
| Olist | dim_olist_product | `product_id` | Product category and physical dimensions |
| Olist | fact_order_payments | `order_id, payment_sequential` | Payment method, installments and value |
| SCMS | fact_procurement | `procurement_id` | Procurement line quantity and item costs |
| SCMS | fact_delivery | `procurement_id` | Shipment mode, planned/actual delivery, freight and insurance |
| SCMS | dim_supplier | `supplier_key` | Vendor/manufacturing site attributes; generated key because source has no supplier ID |
| SCMS | dim_shipment | `shipment_key` | ASN/PO and shipment attributes; generated key |
| SCMS | dim_product_scms | `product_scms_key` | Medical supply/product descriptors; generated key |

See `canonical_schema.json` for field-level names, types, keys and relationships.
