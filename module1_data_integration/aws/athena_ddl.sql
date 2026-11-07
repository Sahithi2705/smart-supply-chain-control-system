-- Run in Athena after uploading the Parquet entity folders.
-- Bucket: smart-supply-chain-data-2026. Region must match the S3 bucket.
CREATE DATABASE IF NOT EXISTS supply_chain_canonical;

-- M5 dimensions and facts
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.m5_dim_product (
 item_id string, dept_id string, cat_id string, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/m5/dim_product/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.m5_dim_store (
 store_id string, state_id string, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/m5/dim_store/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.m5_dim_date (
 date date, wm_yr_wk int, weekday string, wday int, month int, year int, day_id string,
 event_name_1 string, event_type_1 string, event_name_2 string, event_type_2 string,
 snap_CA int, snap_TX int, snap_WI int, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/m5/dim_date/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.m5_fact_sales (
 sales_date date, sku string, store_id string, quantity_sold bigint, unit_price double,
 dept_id string, category_id string, state_id string, wm_yr_wk int, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/m5/fact_sales/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.m5_fact_sell_prices (
 store_id string, sku string, wm_yr_wk int, unit_price double, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/m5/fact_sell_prices/';

-- Olist dimensions and facts
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.olist_fact_orders (
 order_id string, customer_id string, order_status string, order_purchase_timestamp timestamp,
 order_approved_at timestamp, order_delivered_carrier_date timestamp,
 order_delivered_customer_date timestamp, order_estimated_delivery_date timestamp,
 source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/olist/fact_orders/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.olist_fact_order_items (
 order_id string, order_item_id int, product_id string, seller_id string, shipping_limit_date timestamp,
 price double, freight_value double, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/olist/fact_order_items/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.olist_dim_customer (
 customer_id string, customer_unique_id string, customer_zip_code_prefix string,
 customer_city string, customer_state string, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/olist/dim_customer/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.olist_dim_seller (
 seller_id string, seller_zip_code_prefix string, seller_city string, seller_state string,
 source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/olist/dim_seller/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.olist_dim_olist_product (
 product_id string, product_category_name string, product_name_length double,
 product_description_length double, product_photos_qty double, product_weight_g double,
 product_length_cm double, product_height_cm double, product_width_cm double,
 source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/olist/dim_olist_product/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.olist_fact_order_payments (
 order_id string, payment_sequential int, payment_type string, payment_installments int,
 payment_value double, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/olist/fact_order_payments/';

-- SCMS dimensions and facts
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.scms_dim_supplier (
 vendor_name string, manufacturing_site string, managed_by string, country string,
 supplier_key string, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/scms/dim_supplier/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.scms_dim_shipment (
 asn_dn_number string, po_so_number string, shipment_mode string, fulfill_via string,
 vendor_inco_term string, country string, shipment_key string, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/scms/dim_shipment/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.scms_dim_product_scms (
 product_group string, sub_classification string, item_description string, molecule_test_type string,
 brand string, dosage string, dosage_form string, unit_of_measure_per_pack double,
 product_scms_key string, source_system string, source_record_id string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/scms/dim_product_scms/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.scms_fact_procurement (
 procurement_id bigint, project_code string, pq_number string, po_so_number string,
 supplier_key string, product_scms_key string, line_item_quantity bigint,
 unit_of_measure_per_pack bigint, line_item_value_usd double, pack_price_usd double,
 unit_price_usd double, country string, pq_first_sent_to_client_date_source string,
 po_sent_to_vendor_date_source string, source_system string, source_record_id string,
 pq_first_sent_to_client_date date, po_sent_to_vendor_date date
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/scms/fact_procurement/';
CREATE EXTERNAL TABLE IF NOT EXISTS supply_chain_canonical.scms_fact_delivery (
 procurement_id bigint, shipment_key string, supplier_key string, product_scms_key string,
 shipment_mode string, fulfill_via string, scheduled_delivery_date_source string,
 delivered_to_client_date_source string, delivery_recorded_date_source string,
 line_item_quantity bigint, weight_kg double, freight_cost_usd double,
 line_item_insurance_usd double, source_system string, source_record_id string,
 scheduled_delivery_date date, delivered_to_client_date date, delivery_recorded_date date,
 days_late_vs_schedule int, weight_kg_source string, freight_cost_usd_source string, line_item_insurance_usd_source string
) STORED AS PARQUET LOCATION 's3://smart-supply-chain-data-2026/curated/scms/fact_delivery/';
