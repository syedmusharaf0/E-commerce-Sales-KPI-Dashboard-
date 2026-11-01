-- E-Commerce Sales & KPI Dashboard — KPI queries (PostgreSQL)
-- Revenue counts DELIVERED orders only; returned/cancelled orders are
-- analysed as rates. All monetary values in Indian Rupees (INR).

-- 1) HEADLINE KPIs: total revenue, orders, units, average order value
SELECT COUNT(*) FILTER (WHERE order_status = 'Delivered') AS delivered_orders,
       COUNT(*) AS total_orders,
       ROUND(SUM(order_value_inr) FILTER (WHERE order_status = 'Delivered')) AS total_revenue_inr,
       SUM(quantity) FILTER (WHERE order_status = 'Delivered') AS total_units_sold,
       ROUND(AVG(order_value_inr) FILTER (WHERE order_status = 'Delivered')) AS average_order_value_inr
FROM fact_orders;

-- 2) GROSS MARGIN % on delivered orders
SELECT ROUND(100.0 * (SUM(o.order_value_inr) - SUM(o.quantity * p.unit_cost_inr))
             / SUM(o.order_value_inr), 1) AS gross_margin_percent
FROM fact_orders o JOIN dim_products p ON p.product_code = o.product_code
WHERE o.order_status = 'Delivered';

-- 3) REVENUE BY SALES CHANNEL (+ share and AOV)
SELECT sales_channel,
       COUNT(*) AS delivered_orders,
       ROUND(SUM(order_value_inr)) AS revenue_inr,
       ROUND(100.0 * SUM(order_value_inr) / SUM(SUM(order_value_inr)) OVER (), 1) AS revenue_share_percent,
       ROUND(AVG(order_value_inr)) AS average_order_value_inr
FROM fact_orders WHERE order_status = 'Delivered'
GROUP BY sales_channel ORDER BY revenue_inr DESC;

-- 4) REVENUE AND MARGIN BY PRODUCT CATEGORY
SELECT p.product_category,
       COUNT(*) AS delivered_orders,
       SUM(o.quantity) AS units_sold,
       ROUND(SUM(o.order_value_inr)) AS revenue_inr,
       ROUND(100.0 * (SUM(o.order_value_inr) - SUM(o.quantity * p.unit_cost_inr))
             / SUM(o.order_value_inr), 1) AS gross_margin_percent
FROM fact_orders o JOIN dim_products p ON p.product_code = o.product_code
WHERE o.order_status = 'Delivered'
GROUP BY p.product_category ORDER BY revenue_inr DESC;

-- 5) REVENUE BY REGION (region lives in the customer dimension)
SELECT c.customer_region, COUNT(*) AS delivered_orders,
       ROUND(SUM(o.order_value_inr)) AS revenue_inr,
       ROUND(AVG(o.order_value_inr)) AS average_order_value_inr
FROM fact_orders o JOIN dim_customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY c.customer_region ORDER BY revenue_inr DESC;

-- 6) RETURN RATE BY CATEGORY (returns / fulfilled orders)
SELECT p.product_category,
       COUNT(*) FILTER (WHERE o.order_status = 'Returned') AS returned_orders,
       COUNT(*) FILTER (WHERE o.order_status <> 'Cancelled') AS fulfilled_orders,
       ROUND(100.0 * COUNT(*) FILTER (WHERE o.order_status = 'Returned')
             / NULLIF(COUNT(*) FILTER (WHERE o.order_status <> 'Cancelled'), 0), 1) AS return_rate_percent
FROM fact_orders o JOIN dim_products p ON p.product_code = o.product_code
GROUP BY p.product_category ORDER BY return_rate_percent DESC;

-- 7) TOP 10 PRODUCTS BY REVENUE
SELECT o.product_code, p.product_name, p.product_category,
       SUM(o.quantity) AS units_sold, ROUND(SUM(o.order_value_inr)) AS revenue_inr
FROM fact_orders o JOIN dim_products p ON p.product_code = o.product_code
WHERE o.order_status = 'Delivered'
GROUP BY o.product_code, p.product_name, p.product_category
ORDER BY revenue_inr DESC LIMIT 10;

-- 8) REPEAT CUSTOMER RATE (customers with 2+ delivered orders / active customers)
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE delivered_orders >= 2) / COUNT(*), 1)
           AS repeat_customer_percent
FROM (SELECT customer_id, COUNT(*) AS delivered_orders
      FROM fact_orders WHERE order_status = 'Delivered'
      GROUP BY customer_id) c;

-- 9) WEEKLY COMPARISON with LAG — week-over-week (WoW) revenue growth %
WITH w AS (
    SELECT DATE_TRUNC('week', order_date) AS week_start,
           COUNT(*) AS orders, ROUND(SUM(order_value_inr)) AS revenue_inr
    FROM fact_orders WHERE order_status = 'Delivered' GROUP BY 1
)
SELECT week_start, orders, revenue_inr,
       ROUND(100.0 * (revenue_inr - LAG(revenue_inr) OVER (ORDER BY week_start))
             / NULLIF(LAG(revenue_inr) OVER (ORDER BY week_start), 0), 2) AS revenue_wow_growth_percent
FROM w ORDER BY week_start;

-- 10) MONTHLY COMPARISON with LAG — MoM and YoY growth %
WITH m AS (
    SELECT DATE_TRUNC('month', order_date) AS month,
           COUNT(*) AS orders, ROUND(SUM(order_value_inr)) AS revenue_inr
    FROM fact_orders WHERE order_status = 'Delivered' GROUP BY 1
)
SELECT month, orders,
       ROUND(100.0 * (orders - LAG(orders, 1) OVER (ORDER BY month))
             / NULLIF(LAG(orders, 1) OVER (ORDER BY month), 0), 2) AS orders_mom_growth_percent,
       ROUND(100.0 * (orders - LAG(orders, 12) OVER (ORDER BY month))
             / NULLIF(LAG(orders, 12) OVER (ORDER BY month), 0), 2) AS orders_yoy_growth_percent,
       revenue_inr,
       ROUND(100.0 * (revenue_inr - LAG(revenue_inr, 1) OVER (ORDER BY month))
             / NULLIF(LAG(revenue_inr, 1) OVER (ORDER BY month), 0), 2) AS revenue_mom_growth_percent,
       ROUND(100.0 * (revenue_inr - LAG(revenue_inr, 12) OVER (ORDER BY month))
             / NULLIF(LAG(revenue_inr, 12) OVER (ORDER BY month), 0), 2) AS revenue_yoy_growth_percent
FROM m ORDER BY month;

-- 11) YEARLY COMPARISON with LAG — year-over-year growth % (2025 = Jan-Jun, partial)
WITH y AS (
    SELECT DATE_TRUNC('year', order_date) AS year,
           COUNT(*) AS orders, ROUND(SUM(order_value_inr)) AS revenue_inr
    FROM fact_orders WHERE order_status = 'Delivered' GROUP BY 1
)
SELECT year, orders, revenue_inr,
       ROUND(100.0 * (revenue_inr - LAG(revenue_inr) OVER (ORDER BY year))
             / NULLIF(LAG(revenue_inr) OVER (ORDER BY year), 0), 2) AS revenue_yoy_growth_percent
FROM y ORDER BY year;
