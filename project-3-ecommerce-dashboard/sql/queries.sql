-- ============================================================
-- E-commerce Sales & Marketing Dashboard - SQL Queries
-- ============================================================

-- 1. MONTHLY KPI DASHBOARD
SELECT 
    month,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    ROUND(SUM(revenue_gbp), 0) AS total_revenue,
    ROUND(AVG(order_value_gbp), 2) AS avg_order_value,
    ROUND(CAST(SUM(returned) AS FLOAT) / COUNT(*) * 100, 1) AS return_rate_pct,
    ROUND(CAST(SUM(is_returning_customer) AS FLOAT) / COUNT(*) * 100, 1) AS repeat_customer_pct
FROM orders
GROUP BY month
ORDER BY month;

-- 2. MARKETING CHANNEL ROI
SELECT 
    marketing_channel,
    COUNT(*) AS orders,
    ROUND(SUM(revenue_gbp), 0) AS revenue,
    ROUND(AVG(order_value_gbp), 2) AS avg_order_value,
    ROUND(CAST(SUM(is_returning_customer) AS FLOAT) / COUNT(*) * 100, 1) AS returning_pct
FROM orders
GROUP BY marketing_channel
ORDER BY revenue DESC;

-- 3. TOP CUSTOMERS BY LIFETIME VALUE
SELECT 
    customer_id,
    COUNT(*) AS total_orders,
    ROUND(SUM(revenue_gbp), 2) AS total_spent,
    ROUND(AVG(order_value_gbp), 2) AS avg_order_value,
    MIN(order_date) AS first_order,
    MAX(order_date) AS last_order,
    region
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 3
ORDER BY total_spent DESC
LIMIT 20;

-- 4. CATEGORY x CHANNEL PERFORMANCE MATRIX
SELECT 
    category,
    marketing_channel,
    COUNT(*) AS orders,
    ROUND(SUM(revenue_gbp), 0) AS revenue,
    ROUND(AVG(order_value_gbp), 2) AS avg_aov
FROM orders
GROUP BY category, marketing_channel
ORDER BY category, revenue DESC;

-- 5. REGIONAL PERFORMANCE WITH YOY COMPARISON
SELECT 
    region,
    SUBSTR(month, 1, 4) AS year,
    COUNT(*) AS orders,
    ROUND(SUM(revenue_gbp), 0) AS revenue,
    ROUND(AVG(order_value_gbp), 2) AS aov,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders
GROUP BY region, year
ORDER BY region, year;

-- 6. DEVICE & CONVERSION ANALYSIS
SELECT 
    device,
    COUNT(*) AS sessions,
    SUM(converted) AS conversions,
    ROUND(CAST(SUM(converted) AS FLOAT) / COUNT(*) * 100, 2) AS conversion_rate,
    ROUND(AVG(pages_viewed), 1) AS avg_pages,
    ROUND(AVG(session_duration_sec) / 60.0, 1) AS avg_duration_min,
    ROUND(CAST(SUM(bounced) AS FLOAT) / COUNT(*) * 100, 1) AS bounce_rate
FROM sessions
GROUP BY device;
