-- 07: Lost vs Converted Feature Comparison (SQL-side)
-- Uses permanent tables (no temp table references)

USE ecommerce;

-- 7.1 Cart abandoners vs converters: feature comparison using raw data
SELECT '=== Cart: Lost vs Converted ===' AS section;
SELECT 'Lost' AS user_type,
    ROUND(AVG(ub.TimeOnPage_seconds), 1) AS avg_duration,
    ROUND(AVG(ub.ItemsInCart), 1) AS avg_cart_items,
    COUNT(DISTINCT ub.SessionID) AS session_count
FROM user_behavior ub
JOIN funnel_wide f ON ub.SessionID = f.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 0
UNION ALL
SELECT 'Converted',
    ROUND(AVG(ub.TimeOnPage_seconds), 1),
    ROUND(AVG(ub.ItemsInCart), 1),
    COUNT(DISTINCT ub.SessionID)
FROM user_behavior ub
JOIN funnel_wide f ON ub.SessionID = f.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 1;

-- 7.2 Browse->Cart abandoners vs converters: feature comparison
SELECT '=== Browse: Lost vs Converted ===' AS section;
SELECT 'Lost' AS user_type,
    ROUND(AVG(ub.TimeOnPage_seconds), 1) AS avg_duration,
    ROUND(AVG(ub.ItemsInCart), 1) AS avg_cart_items,
    COUNT(DISTINCT ub.SessionID) AS session_count
FROM user_behavior ub
JOIN funnel_wide f ON ub.SessionID = f.SessionID
WHERE f.step2_product = 1 AND f.step3_cart = 0
UNION ALL
SELECT 'Converted',
    ROUND(AVG(ub.TimeOnPage_seconds), 1),
    ROUND(AVG(ub.ItemsInCart), 1),
    COUNT(DISTINCT ub.SessionID)
FROM user_behavior ub
JOIN funnel_wide f ON ub.SessionID = f.SessionID
WHERE f.step2_product = 1 AND f.step3_cart = 1;

-- 7.3 Churn type distribution by channel
SELECT '=== Churn Type by Channel ===' AS section;
SELECT ReferralSource,
    SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END) AS lost_at_browse,
    SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS lost_at_cart,
    SUM(CASE WHEN step4_checkout = 1 AND step5_confirm = 0 THEN 1 ELSE 0 END) AS lost_at_checkout,
    COUNT(DISTINCT SessionID) AS total_sessions
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY total_sessions DESC;

-- 7.4 Device by churn type
SELECT '=== Churn Type by Device ===' AS section;
SELECT DeviceType,
    SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END) AS lost_at_browse,
    SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS lost_at_cart,
    SUM(CASE WHEN step4_checkout = 1 AND step5_confirm = 0 THEN 1 ELSE 0 END) AS lost_at_checkout,
    COUNT(DISTINCT SessionID) AS total_sessions
FROM funnel_wide
GROUP BY DeviceType
ORDER BY total_sessions DESC;
