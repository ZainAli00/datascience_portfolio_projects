-- ============================================================
-- A/B Test Experiment - SQL Queries
-- ============================================================

-- 1. OVERALL RESULTS
SELECT 
    [group],
    COUNT(*) AS participants,
    SUM(converted) AS conversions,
    ROUND(CAST(SUM(converted) AS FLOAT) / COUNT(*) * 100, 2) AS conversion_rate_pct,
    ROUND(AVG(CASE WHEN converted = 1 THEN order_value_gbp END), 2) AS avg_order_value,
    ROUND(AVG(CASE WHEN converted = 1 THEN time_to_action_sec END), 0) AS avg_time_sec
FROM experiment
GROUP BY [group];

-- 2. DEVICE SEGMENT ANALYSIS
SELECT 
    device,
    [group],
    COUNT(*) AS users,
    ROUND(CAST(SUM(converted) AS FLOAT) / COUNT(*) * 100, 2) AS conversion_rate,
    ROUND(AVG(CASE WHEN converted = 1 THEN order_value_gbp END), 2) AS aov
FROM experiment
GROUP BY device, [group]
ORDER BY device, [group];

-- 3. NEW vs RETURNING USER ANALYSIS
SELECT 
    CASE WHEN new_user = 1 THEN 'New User' ELSE 'Returning' END AS user_type,
    [group],
    COUNT(*) AS users,
    ROUND(CAST(SUM(converted) AS FLOAT) / COUNT(*) * 100, 2) AS conversion_rate
FROM experiment
GROUP BY user_type, [group]
ORDER BY user_type;

-- 4. TRAFFIC SOURCE BREAKDOWN
SELECT 
    traffic_source,
    [group],
    COUNT(*) AS users,
    SUM(converted) AS conversions,
    ROUND(CAST(SUM(converted) AS FLOAT) / COUNT(*) * 100, 2) AS conversion_rate,
    ROUND(SUM(order_value_gbp), 0) AS total_revenue
FROM experiment
GROUP BY traffic_source, [group]
ORDER BY traffic_source;

-- 5. SAMPLE RATIO MISMATCH CHECK
SELECT 
    [group],
    COUNT(*) AS n,
    ROUND(CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM experiment) * 100, 2) AS pct
FROM experiment
GROUP BY [group];

-- 6. REVENUE IMPACT PROJECTION
SELECT 
    [group],
    ROUND(CAST(SUM(converted) AS FLOAT) / COUNT(*), 4) AS cr,
    ROUND(AVG(CASE WHEN converted = 1 THEN order_value_gbp END), 2) AS aov,
    ROUND(CAST(SUM(converted) AS FLOAT) / COUNT(*) * AVG(CASE WHEN converted = 1 THEN order_value_gbp END) * 50000, 0) AS projected_monthly_revenue_50k_checkouts
FROM experiment
GROUP BY [group];
