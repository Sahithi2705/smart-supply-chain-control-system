-- M5: daily unit sales by store and date
SELECT sales_date, store_id, SUM(quantity_sold) AS units_sold
FROM m5_fact_sales
GROUP BY 1, 2
ORDER BY 1, 2
LIMIT 25;

-- M5: product/store weekly price coverage
SELECT store_id, sku, COUNT(*) AS priced_weeks,
       MIN(unit_price) AS min_price, MAX(unit_price) AS max_price
FROM m5_fact_sell_prices
GROUP BY 1, 2
ORDER BY priced_weeks DESC
LIMIT 25;

-- Olist: orders and total payment values
SELECT o.order_status, COUNT(DISTINCT o.order_id) AS orders,
       SUM(p.payment_value) AS payment_total
FROM olist_fact_orders o
LEFT JOIN olist_fact_order_payments p USING (order_id)
GROUP BY o.order_status
ORDER BY orders DESC;

-- Olist: seller item sales value
SELECT i.seller_id, COUNT(*) AS order_lines,
       SUM(i.price) AS merchandise_value, SUM(i.freight_value) AS freight_value
FROM olist_fact_order_items i
GROUP BY i.seller_id
ORDER BY merchandise_value DESC
LIMIT 20;

-- SCMS: delivery timeliness by shipment mode
SELECT shipment_mode,
       COUNT(*) AS shipments_with_actual_date,
       AVG(days_late_vs_schedule) AS avg_days_late,
       SUM(CASE WHEN days_late_vs_schedule > 0 THEN 1 ELSE 0 END) AS late_shipments
FROM scms_fact_delivery
WHERE scheduled_delivery_date IS NOT NULL
  AND delivered_to_client_date IS NOT NULL
GROUP BY shipment_mode
ORDER BY shipments_with_actual_date DESC;

-- SCMS: procurement value by supplier
SELECT s.vendor_name, SUM(p.line_item_value_usd) AS procurement_value_usd,
       SUM(p.line_item_quantity) AS units_ordered
FROM scms_fact_procurement p
LEFT JOIN scms_dim_supplier s USING (supplier_key)
GROUP BY s.vendor_name
ORDER BY procurement_value_usd DESC
LIMIT 20;
