-- ============================================================
-- NHS A&E Wait Times Analysis - SQL Queries
-- ============================================================
-- Database: nhs_ae_analysis.db (SQLite)
-- Author: [Your Name]
-- ============================================================

-- 1. NATIONAL OVERVIEW: Monthly 4-hour target performance
SELECT 
    period,
    SUM(total_attendances) AS total_attendances,
    SUM(within_4hrs) AS within_4hrs,
    SUM(breaches_over_4hrs) AS breaches,
    ROUND(CAST(SUM(within_4hrs) AS FLOAT) / SUM(total_attendances) * 100, 1) AS pct_within_4hrs
FROM ae_attendances
WHERE ae_type = 'Type 1 - Major A&E'
GROUP BY period
ORDER BY period;


-- 2. REGIONAL PERFORMANCE RANKING (latest year)
SELECT 
    region,
    SUM(total_attendances) AS total_attendances,
    ROUND(CAST(SUM(within_4hrs) AS FLOAT) / SUM(total_attendances) * 100, 1) AS pct_within_4hrs,
    ROUND(AVG(avg_wait_minutes), 0) AS avg_wait_mins,
    SUM(over_12hr_waits) AS total_12hr_waits
FROM ae_attendances
WHERE ae_type = 'Type 1 - Major A&E'
    AND period LIKE '2024%'
GROUP BY region
ORDER BY pct_within_4hrs DESC;


-- 3. WORST PERFORMING TRUSTS (bottom 10)
SELECT 
    trust_name,
    region,
    ROUND(AVG(pct_within_4hrs), 1) AS avg_pct_within_4hrs,
    SUM(total_attendances) AS total_attendances,
    ROUND(AVG(avg_wait_minutes), 0) AS avg_wait_mins,
    SUM(over_12hr_waits) AS total_12hr_waits
FROM ae_attendances
WHERE ae_type = 'Type 1 - Major A&E'
GROUP BY trust_name, region
ORDER BY avg_pct_within_4hrs ASC
LIMIT 10;


-- 4. SEASONAL ANALYSIS: Winter vs Summer performance
SELECT 
    CASE 
        WHEN CAST(SUBSTR(period, 6, 2) AS INT) IN (12, 1, 2) THEN 'Winter'
        WHEN CAST(SUBSTR(period, 6, 2) AS INT) IN (6, 7, 8) THEN 'Summer'
        ELSE 'Other'
    END AS season,
    COUNT(DISTINCT period) AS months,
    ROUND(AVG(pct_within_4hrs), 1) AS avg_pct_within_4hrs,
    ROUND(AVG(avg_wait_minutes), 0) AS avg_wait_mins,
    SUM(over_12hr_waits) AS total_12hr_waits
FROM ae_attendances
WHERE ae_type = 'Type 1 - Major A&E'
GROUP BY season
ORDER BY avg_pct_within_4hrs ASC;


-- 5. YEAR-OVER-YEAR CHANGE BY REGION
SELECT 
    region,
    SUBSTR(period, 1, 4) AS year,
    SUM(total_attendances) AS total_attendances,
    ROUND(CAST(SUM(within_4hrs) AS FLOAT) / SUM(total_attendances) * 100, 1) AS pct_within_4hrs,
    SUM(over_12hr_waits) AS total_12hr_waits
FROM ae_attendances
WHERE ae_type = 'Type 1 - Major A&E'
GROUP BY region, year
ORDER BY region, year;


-- 6. TRUSTS WITH MOST 12-HOUR WAITS
SELECT 
    trust_name,
    region,
    SUM(over_12hr_waits) AS total_12hr_waits,
    ROUND(CAST(SUM(over_12hr_waits) AS FLOAT) / SUM(breaches_over_4hrs) * 100, 1) AS pct_of_breaches_12hr,
    ROUND(AVG(pct_within_4hrs), 1) AS avg_4hr_performance
FROM ae_attendances
WHERE ae_type = 'Type 1 - Major A&E'
    AND breaches_over_4hrs > 0
GROUP BY trust_name, region
HAVING SUM(over_12hr_waits) > 0
ORDER BY total_12hr_waits DESC
LIMIT 10;


-- 7. MONTH-ON-MONTH CHANGE (Window function style for analysis)
WITH monthly AS (
    SELECT 
        period,
        SUM(total_attendances) AS attendances,
        ROUND(CAST(SUM(within_4hrs) AS FLOAT) / SUM(total_attendances) * 100, 1) AS pct
    FROM ae_attendances
    WHERE ae_type = 'Type 1 - Major A&E'
    GROUP BY period
)
SELECT 
    m1.period,
    m1.attendances,
    m1.pct AS current_pct,
    m2.pct AS prev_month_pct,
    ROUND(m1.pct - COALESCE(m2.pct, m1.pct), 1) AS month_change
FROM monthly m1
LEFT JOIN monthly m2 ON m2.period = (
    SELECT MAX(period) FROM monthly WHERE period < m1.period
)
ORDER BY m1.period;
