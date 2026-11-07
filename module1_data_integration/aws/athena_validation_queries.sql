-- Basic row counts: all 16 canonical entities should be non-empty after a successful ETL.
SELECT 'm5_fact_sales' AS entity, COUNT(*) AS row_count FROM m5_fact_sales
UNION ALL SELECT 'olist_fact_orders', COUNT(*) FROM olist_fact_orders
UNION ALL SELECT 'olist_fact_order_items', COUNT(*) FROM olist_fact_order_items
UNION ALL SELECT 'scms_fact_procurement', COUNT(*) FROM scms_fact_procurement
UNION ALL SELECT 'scms_fact_delivery', COUNT(*) FROM scms_fact_delivery;

-- M5 mandatory key nulls and negative quantity check.
SELECT COUNT(*) AS invalid_rows
FROM m5_fact_sales
WHERE sales_date IS NULL OR sku IS NULL OR store_id IS NULL OR quantity_sold < 0;

-- Olist item foreign-key checks.
SELECT COUNT(*) AS orphan_order_items
FROM olist_fact_order_items i
LEFT JOIN olist_fact_orders o ON i.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT COUNT(*) AS orphan_products
FROM olist_fact_order_items i
LEFT JOIN olist_dim_olist_product p ON i.product_id = p.product_id
WHERE p.product_id IS NULL;

-- SCMS delivery timeliness: only rows with both typed dates participate.
SELECT shipment_mode, COUNT(*) AS dated_shipments,
       AVG(days_late_vs_schedule) AS average_days_late,
       SUM(CASE WHEN days_late_vs_schedule > 0 THEN 1 ELSE 0 END) AS late_shipments
FROM scms_fact_delivery
WHERE scheduled_delivery_date IS NOT NULL AND delivered_to_client_date IS NOT NULL
GROUP BY shipment_mode;
