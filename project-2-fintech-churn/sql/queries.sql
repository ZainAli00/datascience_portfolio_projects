-- ============================================================
-- UK Fintech Customer Churn - SQL Queries
-- ============================================================

-- 1. CHURN RATE BY PRODUCT AND REGION
SELECT 
    primary_product,
    region,
    COUNT(*) as total_customers,
    SUM(churned) as churned,
    ROUND(CAST(SUM(churned) AS FLOAT) / COUNT(*) * 100, 1) as churn_rate_pct
FROM customers
GROUP BY primary_product, region
ORDER BY churn_rate_pct DESC;

-- 2. HIGH-VALUE CUSTOMERS AT RISK
SELECT 
    customer_id,
    region,
    primary_product,
    avg_balance_gbp,
    tenure_months,
    satisfaction_score,
    num_support_tickets,
    app_logins_per_month
FROM customers
WHERE churned = 0
    AND avg_balance_gbp > 10000
    AND satisfaction_score <= 2
ORDER BY avg_balance_gbp DESC
LIMIT 20;

-- 3. COHORT ANALYSIS BY TENURE
SELECT 
    CASE 
        WHEN tenure_months <= 6 THEN '0-6 months'
        WHEN tenure_months <= 12 THEN '6-12 months'
        WHEN tenure_months <= 24 THEN '1-2 years'
        WHEN tenure_months <= 48 THEN '2-4 years'
        ELSE '4+ years'
    END as tenure_cohort,
    COUNT(*) as customers,
    ROUND(AVG(avg_balance_gbp), 0) as avg_balance,
    ROUND(AVG(monthly_transactions), 1) as avg_transactions,
    ROUND(CAST(SUM(churned) AS FLOAT) / COUNT(*) * 100, 1) as churn_rate
FROM customers
GROUP BY tenure_cohort
ORDER BY churn_rate DESC;

-- 4. SUPPORT TICKET IMPACT ON CHURN
SELECT 
    num_support_tickets,
    COUNT(*) as customers,
    ROUND(CAST(SUM(churned) AS FLOAT) / COUNT(*) * 100, 1) as churn_rate,
    ROUND(AVG(satisfaction_score), 2) as avg_satisfaction
FROM customers
GROUP BY num_support_tickets
HAVING COUNT(*) > 20
ORDER BY num_support_tickets;

-- 5. REVENUE AT RISK (estimated from balances)
SELECT 
    risk_segment,
    COUNT(*) as customers,
    ROUND(SUM(avg_balance_gbp), 0) as total_balance_at_risk,
    ROUND(AVG(avg_balance_gbp), 0) as avg_balance,
    ROUND(CAST(SUM(churned) AS FLOAT) / COUNT(*) * 100, 1) as actual_churn_rate
FROM customers
WHERE risk_segment IN ('High Risk', 'Critical')
GROUP BY risk_segment;

-- 6. ACQUISITION CHANNEL EFFECTIVENESS  
SELECT 
    referral_source,
    COUNT(*) as total_acquired,
    ROUND(CAST(SUM(churned) AS FLOAT) / COUNT(*) * 100, 1) as churn_rate,
    ROUND(AVG(tenure_months), 1) as avg_tenure,
    ROUND(AVG(num_products), 2) as avg_products
FROM customers
GROUP BY referral_source
ORDER BY churn_rate;
