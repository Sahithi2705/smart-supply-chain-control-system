# Source-to-canonical mapping

## Global contract

- Each source system is modelled independently. No cross-system product/customer/supplier key is inferred.
- Each fact includes `source_system` and `source_record_id`.
- Missing source values remain null unless a documented deterministic derivation is necessary for a technical key.
- Date parsing failures remain null in typed date fields; the original CSV remains the audit source.

## M5

| Source field | Canonical entity.field | Rule |
|---|---|---|
| `item_id` | `dim_product.item_id`, `fact_sales.sku`, `fact_sell_prices.sku` | Preserve source ID as string |
| `dept_id`, `cat_id` | `dim_product.dept_id`, `dim_product.cat_id` | `cat_id` is named `category_id` in fact_sales |
| `store_id`, `state_id` | `dim_store` and `fact_sales` | Preserve source IDs |
| `d_1...d_1941` | `fact_sales.quantity_sold` | Unpivot evaluation snapshot to one row per item/store/day |
| `calendar.d` | `dim_date.day_id`, fact join key | Join daily facts to calendar |
| `calendar.date` | `fact_sales.sales_date`, `dim_date.date` | Parsed as date |
| `calendar.wm_yr_wk` | `fact_sales.wm_yr_wk` | Used to join price rows |
| `sell_prices.store_id,item_id,wm_yr_wk` | `fact_sell_prices` and `fact_sales.unit_price` | Exact composite join; no guessed price fill |
| `sales_train_validation` | validation input only | Compare its 1,913 common days with evaluation; do not append and double-count |

## Olist

| Source file.field | Canonical entity.field | Rule |
|---|---|---|
| orders: `order_id`, `customer_id`, `order_status`, timestamps | `fact_orders` | Parse timestamps; keep null lifecycle dates |
| order_items: `order_id`, `order_item_id` | `fact_order_items` composite key | Preserve item grain |
| order_items: `product_id`, `seller_id` | `fact_order_items` foreign keys | Join to Olist dimensions only |
| order_items: `price`, `freight_value`, `shipping_limit_date` | `fact_order_items` | Numeric and timestamp types |
| customers fields | `dim_customer` | `customer_id` is order-level key; `customer_unique_id` is retained as separate source identity |
| sellers fields | `dim_seller` | Preserve seller postal/city/state attributes |
| products fields | `dim_olist_product` | Correct source misspellings `product_name_lenght` and `product_description_lenght` to `*_length` |
| payments fields | `fact_order_payments` | Composite key `(order_id, payment_sequential)`; multiple payments per order retained |

## SCMS

| Actual source field | Canonical entity.field | Rule |
|---|---|---|
| `ID` | `fact_procurement.procurement_id`, `fact_delivery.procurement_id` | Source row identifier and grain |
| `PO / SO #`, `PQ #`, `Project Code` | `fact_procurement` | Retain procurement references |
| `Vendor`, `Manufacturing Site`, `Managed By`, `Country` | `dim_supplier` | Deterministic `supplier_key` from vendor + manufacturing site; source has no supplier ID |
| `ASN/DN #`, `Shipment Mode`, `Fulfill Via`, `Vendor INCO Term`, `Country` | `dim_shipment` | Deterministic shipment key from observed shipment attributes |
| `Product Group`, `Sub Classification`, `Item Description`, `Molecule/Test Type`, `Brand`, `Dosage`, `Dosage Form`, `Unit of Measure (Per Pack)` | `dim_product_scms` | Deterministic product key from source attributes; not merged with M5/Olist products |
| `Line Item Quantity`, `Line Item Value`, `Pack Price`, `Unit Price` | `fact_procurement` | Quantities and USD cost/price attributes |
| `PQ First Sent to Client Date`, `PO Sent to Vendor Date` | `fact_procurement` | Original source strings retained; day-first typed dates are nullable because workflow labels occur |
| `Scheduled Delivery Date`, `Delivered to Client Date`, `Delivery Recorded Date` | `fact_delivery` | Day-first parsing; special text sentinels become null typed dates |
| `Weight (Kilograms)`, `Freight Cost (USD)`, `Line Item Insurance (USD)` | `fact_delivery` | Numeric cost/logistics attributes |

## Grain notes

- M5 `fact_sales`: one row per `sales_date + sku + store_id`.
- M5 `fact_sell_prices`: one row per `store_id + sku + wm_yr_wk`.
- Olist `fact_orders`: one row per order; `fact_order_items`: one row per order line; payments: one row per order payment sequence.
- SCMS procurement and delivery facts are each at the source line-item `ID` grain. Their relationship is 1:1 on `procurement_id` in this dataset.
