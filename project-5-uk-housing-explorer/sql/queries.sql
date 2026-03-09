-- ============================================================
-- UK Housing Market Explorer - SQL Queries
-- ============================================================

-- 1. REGIONAL PRICE SUMMARY
SELECT 
    region,
    COUNT(*) AS transactions,
    ROUND(AVG(price_gbp), 0) AS avg_price,
    ROUND(MIN(price_gbp), 0) AS min_price,
    ROUND(MAX(price_gbp), 0) AS max_price
FROM transactions
GROUP BY region
ORDER BY avg_price DESC;

-- 2. AFFORDABILITY TRENDS
SELECT * FROM affordability
ORDER BY region, year;

-- 3. YEAR-ON-YEAR PRICE CHANGE
WITH yearly AS (
    SELECT region, year, ROUND(AVG(price_gbp), 0) AS avg_price
    FROM transactions GROUP BY region, year
)
SELECT 
    y1.region, y1.year,
    y1.avg_price,
    y2.avg_price AS prev_year,
    ROUND((CAST(y1.avg_price AS FLOAT) / y2.avg_price - 1) * 100, 1) AS yoy_change_pct
FROM yearly y1
LEFT JOIN yearly y2 ON y1.region = y2.region AND y1.year = y2.year + 1
ORDER BY y1.region, y1.year;

-- 4. FIRST-TIME BUYER AFFORDABILITY (lower quartile)
SELECT 
    t.region, t.year,
    ROUND(AVG(CASE WHEN t.property_type IN ('Flat', 'Terraced') THEN t.price_gbp END), 0) AS avg_starter_price,
    i.lower_quartile_income,
    ROUND(CAST(AVG(CASE WHEN t.property_type IN ('Flat', 'Terraced') THEN t.price_gbp END) AS FLOAT) / i.lower_quartile_income, 1) AS ftb_ratio
FROM transactions t
JOIN incomes i ON t.region = i.region AND t.year = i.year
GROUP BY t.region, t.year
ORDER BY ftb_ratio DESC;

-- 5. NEW BUILD PREMIUM
SELECT 
    region,
    ROUND(AVG(CASE WHEN new_build = 1 THEN price_gbp END), 0) AS avg_new_build,
    ROUND(AVG(CASE WHEN new_build = 0 THEN price_gbp END), 0) AS avg_existing,
    ROUND((CAST(AVG(CASE WHEN new_build = 1 THEN price_gbp END) AS FLOAT) / 
           AVG(CASE WHEN new_build = 0 THEN price_gbp END) - 1) * 100, 1) AS premium_pct
FROM transactions
GROUP BY region
ORDER BY premium_pct DESC;

-- 6. PROPERTY TYPE MIX BY REGION
SELECT 
    region,
    property_type,
    COUNT(*) AS transactions,
    ROUND(CAST(COUNT(*) AS FLOAT) / SUM(COUNT(*)) OVER (PARTITION BY region) * 100, 1) AS pct_of_region,
    ROUND(AVG(price_gbp), 0) AS avg_price
FROM transactions
GROUP BY region, property_type
ORDER BY region, avg_price DESC;
